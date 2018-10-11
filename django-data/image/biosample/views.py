
import os
import redis
import logging

from decouple import AutoConfig

from django.conf import settings
from django.urls import reverse_lazy, reverse
from django.utils.crypto import get_random_string
from django.utils.http import is_safe_url
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, CreateView, ModelFormMixin
from django.contrib import messages

from pyEBIrest import Auth
from pyEBIrest.client import User

from image_app.models import Submission
from submissions.templatetags.submissions_tags import can_submit

from .forms import (
    GenerateTokenForm, RegisterUserForm, CreateUserForm, SubmitForm)
from .models import Account, ManagedTeam
from .tasks import submit

# get available statuses
WAITING = Submission.STATUSES.get_value('waiting')

# Get an instance of a logger
logger = logging.getLogger(__name__)


# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)


# In programming, a mixin is a class that provides functionality to be
# inherited, but isn’t meant for instantiation on its own. In programming
# languages with multiple inheritance, mixins can be used to add enhanced
# functionality and behavior to classes.
class TokenMixin(object):
    """Register account if a biosample account is not registered"""

    def dispatch(self, request, *args, **kwargs):
        # get user from request and user model. This could be also Anonymous
        # user:however with metod decorator a login is required before dispatch
        # method is called
        User = get_user_model()
        user = self.request.user

        try:
            user.biosample_account

        except User.biosample_account.RelatedObjectDoesNotExist:
            messages.warning(
                request=self.request,
                message='You need to register a valid biosample account',
                extra_tags="alert alert-dismissible alert-warning")

            return redirect('accounts:registration_activation_complete')

        else:
            # call the default get method
            return super(
                TokenMixin, self).dispatch(request, *args, **kwargs)


class RegisterMixin(object):
    """If a biosample account is already registered, returns to dashboard"""

    def dispatch(self, request, *args, **kwargs):
        # get user from request and user model. This could be also Anonymous
        # user:however with metod decorator a login is required before dispatch
        # method is called
        User = get_user_model()
        user = self.request.user

        try:
            user.biosample_account

        except User.biosample_account.RelatedObjectDoesNotExist:
            # call the default get method
            return super(
                RegisterMixin, self).dispatch(request, *args, **kwargs)

        else:
            messages.warning(
                request=self.request,
                message='Your biosample account is already registered',
                extra_tags="alert alert-dismissible alert-warning")

            return redirect('image_app:dashboard')


class MyFormMixin(object):
    success_url_message = "Please set this variable"
    success_url = reverse_lazy("image_app:dashboard")

    # add the request to the kwargs
    # https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
    # this is needed to display messages (django.contronb) on pages
    def get_form_kwargs(self):
        kwargs = super(MyFormMixin, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        """Override default function"""

        messages.success(
            request=self.request,
            message=self.success_url_message,
            extra_tags="alert alert-dismissible alert-success")

        return super(MyFormMixin, self).get_success_url()

    def form_invalid(self, form):
        messages.error(
            self.request,
            message="Please correct the errors below",
            extra_tags="alert alert-dismissible alert-danger")

        return super(MyFormMixin, self).form_invalid(form)


class GenerateTokenView(LoginRequiredMixin, MyFormMixin, TokenMixin, FormView):
    template_name = 'biosample/generate_token.html'
    form_class = GenerateTokenForm
    success_url_message = 'Token generated!'

    def dispatch(self, request, *args, **kwargs):
        # try to read next link
        next_url = request.GET.get('next', None)

        # redirect to next url. is_safe_url: is a safe redirection
        # (i.e. it doesn't point to a different host and uses a safe scheme).
        if next_url and is_safe_url(next_url):
            logger.debug("Got %s as next_url" % next_url)
            self.success_url = next_url

        return super(
            GenerateTokenView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """

        initial = super(GenerateTokenView, self).get_initial()
        initial['user'] = self.request.user.biosample_account.name

        return initial

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        user = form.cleaned_data['user']
        password = form.cleaned_data['password']

        try:
            auth = Auth(user=user, password=password)

        except ConnectionError as e:
            # logger exception. With repr() the exception name is rendered
            logger.error(repr(e))

            # maybe I typed a wrong password or there is an issue in biosample
            # logg error in message and return form_invalid
            # HINT: deal with two conditions?

            # parse error message
            messages.error(
                self.request,
                "Unable to generate token: %s" % str(e),
                extra_tags="alert alert-dismissible alert-danger")

            # return invalid form
            return self.form_invalid(form)

        else:
            self.request.session['token'] = auth.token
            return super(GenerateTokenView, self).form_valid(form)


class TokenView(LoginRequiredMixin, TokenMixin, TemplateView):
    """Visualize token details"""

    template_name = 'biosample/token.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(TokenView, self).get_context_data(**kwargs)

        # get user and team object
        context['name'] = self.request.user.biosample_account.name
        context['team'] = self.request.user.biosample_account.team

        try:
            # add content to context
            auth = Auth(token=self.request.session['token'])

            if auth.is_expired():
                messages.error(
                    self.request,
                    "Your token is expired",
                    extra_tags="alert alert-dismissible alert-danger")

            context["auth"] = auth

        except KeyError as e:
            logger.error("No valid token found for %s" % self.request.user)

            messages.error(
                self.request,
                "You haven't generated any token yet",
                extra_tags="alert alert-dismissible alert-danger")

        return context


class RegisterUserView(LoginRequiredMixin, RegisterMixin, MyFormMixin,
                       CreateView):
    template_name = 'biosample/register_user.html'
    form_class = RegisterUserForm
    success_url_message = 'Account registered'

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        name = form.cleaned_data['name']
        password = form.cleaned_data['password']
        team = form.cleaned_data['team']

        try:
            auth = Auth(user=name, password=password)

        except ConnectionError as e:
            # logger exception. With repr() the exception name is rendered
            logger.error(repr(e))

            messages.error(
                self.request,
                "Unable to generate token: %s" % str(e),
                extra_tags="alert alert-dismissible alert-danger")

            # return invalid form
            return self.form_invalid(form)

        if team.name not in auth.claims['domains']:
            messages.error(
                self.request,
                "You don't belong to team: %s" % team,
                extra_tags="alert alert-dismissible alert-danger")

            # return invalid form
            return self.form_invalid(form)

        # record token in session
        self.request.session['token'] = auth.token

        # add a user to object (comes from section not from form)
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()

        # call to a specific function (which does an HttpResponseRedirect
        # to success_url)
        return super(ModelFormMixin, self).form_valid(form)


class CreateUserView(LoginRequiredMixin, RegisterMixin, MyFormMixin, FormView):
    template_name = 'biosample/create_user.html'
    form_class = CreateUserForm
    success_url_message = "Account created"

    def get_form_kwargs(self):
        """Override get_form_kwargs"""

        kwargs = super(CreateUserView, self).get_form_kwargs()

        # create a new biosample user
        username = "image-%s" % (get_random_string(length=8))

        # add username to instance
        kwargs['username'] = username

        return kwargs

    # HINT: move to a celery task?
    def form_valid(self, form):
        """Create a new team in with biosample manager user, then create a new
        user and register it"""

        password = form.cleaned_data['password1']
        confirmPwd = form.cleaned_data['password2']

        # get user model associated with this session
        user = self.request.user

        first_name = user.first_name
        last_name = user.last_name
        email = user.email

        # Affiliation is the institution the user belong
        affiliation = user.person.affiliation.name

        # set full name as
        full_name = " ".join([first_name, last_name])

        # creating a user
        logger.debug("Creating user %s" % (form.username))

        try:
            user_id = User.create_user(
                user=form.username,
                password=password,
                confirmPwd=confirmPwd,
                email=email,
                full_name=full_name,
                organization=affiliation
            )

        except ConnectionError as e:
            logger.error("Problem in creating user %s" % (form.username))
            logger.error("Message was: %s" % (e))
            messages.error(
                self.request,
                message="Problem in creating user %s",
                extra_tags="alert alert-dismissible alert-danger")

            messages.error(
                self.request,
                message="Message was: %s" % (e),
                extra_tags="alert alert-dismissible alert-danger")

            # return invalid form
            return self.form_invalid(form)

        # creating a new team. First create an user object
        # create a new auth object
        logger.debug("Generate a token for 'USI_MANAGER'")

        auth = Auth(
            user=config('USI_MANAGER'),
            password=config('USI_MANAGER_PASSWORD'))

        admin = User(auth)

        description = "Team for %s" % (full_name)

        # now create a team
        logger.debug("Creating team for %s" % (full_name))
        team = admin.create_team(description=description)

        logger.info("Team %s generated" % (team.name))

        # register team in ManagedTeam table
        managed, created = ManagedTeam.objects.get_or_create(
            name=team.name)

        if created is True:
            logger.info("Created: %s" % (managed))

        # I need to generate a new token to see the new team
        logger.debug("Generate a new token for 'USI_MANAGER'")

        auth = Auth(
            user=config('USI_MANAGER'),
            password=config('USI_MANAGER_PASSWORD'))

        # pass the new auth object to admin
        admin = User(auth)

        # list all domain for manager
        logger.debug("Listing all domains for %s" % (config('USI_MANAGER')))
        logger.debug(", ".join(auth.claims['domains']))

        # get the domain for the new team, and then the domain_id
        logger.debug("Getting domain info for team %s" % (team.name))
        domain = admin.get_domain_by_name(team.name)
        domain_id = domain.domainReference

        logger.debug(
            "Adding user %s to team %s" % (form.username, team.name))

        # user to team
        admin.add_user_to_team(user_id=user_id, domain_id=domain_id)

        # save objects in accounts table
        account = Account.objects.create(
            user=self.request.user,
            name=form.username,
            team=managed
        )

        logger.info("%s created" % (account))

        # add message
        messages.debug(
            request=self.request,
            message="User %s added to team %s" % (form.username, team.name),
            extra_tags="alert alert-dismissible alert-light")

        # call to a inherited function (which does an HttpResponseRedirect
        # to success_url)
        return super(CreateUserView, self).form_valid(form)


class SubmitView(LoginRequiredMixin, FormView):
    form_class = SubmitForm
    template_name = 'biosample/submit.html'
    submission_id = None

    def get_success_url(self):
        return reverse('submissions:detail', kwargs={
            'pk': self.submission_id})

    def redirect_to_token(self, submission_id):
        """Save the current submission_id in session, then return a redirect
        to GenerateTokenView with my current url as next parameter"""

        # determine next url after token generarion
        next_url = (
            reverse("biosample:token-generation") +
            "?next=%s" % self.request.path)

        # POST data can't be shared accross redirect, since redirect can be
        # accessible only wia GET. So post data need to be stored elsewere,
        # eg in session
        self.request.session["submitview:submission_id"] = submission_id
        logger.debug("Tracking submission_id %s for submission" % (
            submission_id))

        # redirect to my new url
        return redirect(next_url)

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form or
        resume submission after token generation"""

        if "submitview:submission_id" in self.request.session:
            # track submission id in order to render page
            self.submission_id = self.request.session.pop(
                "submitview:submission_id")
            logger.debug(
                "Resume submission view for %s" % (self.submission_id))

            if 'token' in self.request.session:
                auth = Auth(token=self.request.session['token'])
                submission = Submission.objects.get(pk=self.submission_id)

                # start the submission project
                self.start_submission(auth, submission)

                # get success url
                return redirect(self.get_success_url())

        # outside a valid token and submission key, I will return the form
        return self.render_to_response(self.get_context_data())

    def form_valid(self, form):
        submission_id = form.cleaned_data['submission_id']
        submission = Submission.objects.get(pk=submission_id)

        # track submission id in order to render page
        self.submission_id = submission_id

        # check if I can submit object (statuses)
        if not can_submit(submission):
            # return super method (which calls get_success_url)
            logger.error(
                "Can't submit submission %s: current status is %s" % (
                    submission, submission.get_status_display()))
            return super(SubmitView, self).form_valid(form)

        # check token: if expired or near to expiring, call
        # generate token with a redirect to generate-token
        if 'token' in self.request.session:
            auth = Auth(token=self.request.session['token'])

        else:
            logger.warning(
                "No valid token found. Redirect to tocken generation")

            messages.error(
                self.request,
                "You haven't generated any token yet. Generate a new one",
                extra_tags="alert alert-dismissible alert-danger")

            # redirect to token-generation
            return self.redirect_to_token(submission_id)

        # check tocken expiration
        if auth.is_expired() or auth.get_duration().seconds < 1800:
            logger.warning(
                "Token is expired or near to expire. Generate a new one")

            messages.error(
                self.request,
                "Your token is expired or near to expire",
                extra_tags="alert alert-dismissible alert-danger")

            # redirect to token-generation
            return self.redirect_to_token(submission_id)

        # start the submission project
        self.start_submission(auth, submission)

        return redirect(self.get_success_url())

    def start_submission(self, auth, submission):
        """Change submission status and submit data with a valid token"""

        logger.debug("Connecting to redis database")

        # here token is valid, so store it in redis database
        client = redis.StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB)

        key = "token:submission:{submission_id}:{user}".format(
            submission_id=self.submission_id,
            user=self.request.user)

        logger.debug("Writing token in redis")

        client.set(key, auth.token, ex=auth.get_duration().seconds)

        # Update submission status
        submission.status = WAITING
        submission.message = "Waiting for biosample submission"
        submission.save()

        # a valid submission start a task
        res = submit.delay(submission.id)
        logger.info(
            "Start validation process for %s with task %s" % (
                submission,
                res.task_id))
