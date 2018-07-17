
import os
import json
import logging

from decouple import AutoConfig

from django.conf import settings
from django.urls import reverse_lazy
from django.utils.crypto import get_random_string
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, CreateView, ModelFormMixin
from django.contrib import messages

from pyEBIrest import Auth
from pyEBIrest.client import User

from .forms import CreateAuthViewForm, RegisterUserForm, CreateUserForm
from .models import Account, ManagedTeam

# Get an instance of a logger
logger = logging.getLogger(__name__)


# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)


class CreateAuthView(LoginRequiredMixin, FormView):
    template_name = 'biosample/generate_token.html'
    form_class = CreateAuthViewForm

    # add the request to the kwargs
    # https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
    # this is needed to display messages (django.contronb) on pages
    def get_form_kwargs(self):
        kwargs = super(CreateAuthView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """

        initial = super(CreateAuthView, self).get_initial()
        initial['user'] = self.request.user.biosample_account.name

        return initial

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        user = form.cleaned_data['user']
        password = form.cleaned_data['password']

        try:
            auth = Auth(user=user, password=password)
            self.request.session['token'] = auth.token
            return super(CreateAuthView, self).form_valid(form)

        except ConnectionError as e:
            # logger exception. With repr() the exception name is rendered
            logger.error(repr(e))

            # parse error message
            messages.error(
                self.request,
                "Unable to generate token: %s" % str(e),
                extra_tags="alert alert-dismissible alert-danger")

            # return invalid form
            return self.form_invalid(form)

    def get_success_url(self):
        """Override default function"""

        messages.success(
            request=self.request,
            message='Token generated!',
            extra_tags="alert alert-dismissible alert-success")

        return reverse_lazy("image_app:dashboard")


class AuthView(LoginRequiredMixin, TemplateView):
    template_name = 'biosample/token.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(AuthView, self).get_context_data(**kwargs)

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
            logger.error(repr(e))

            messages.error(
                self.request,
                "You haven't generated any token yet",
                extra_tags="alert alert-dismissible alert-danger")

        return context

    def dispatch(self, request, *args, **kwargs):
        # this will ask to login to an un-logged user
        if not request.user.is_authenticated:
            return self.handle_no_permission()

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
                AuthView, self).dispatch(request, *args, **kwargs)


class RegisterUserView(LoginRequiredMixin, CreateView):
    template_name = 'biosample/register_user.html'
    form_class = RegisterUserForm

    # add the request to the kwargs
    # https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
    # this is needed to display messages (django.contrib) on pages
    def get_form_kwargs(self):
        kwargs = super(RegisterUserView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        # this will ask to login to an un-logged user
        if not request.user.is_authenticated:
            return self.handle_no_permission()

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
                RegisterUserView, self).dispatch(request, *args, **kwargs)

        else:
            messages.warning(
                request=self.request,
                message='Your biosample account is already registered',
                extra_tags="alert alert-dismissible alert-warning")

            return redirect('image_app:dashboard')

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

    def form_invalid(self, form):
        messages.error(
            self.request,
            message="Please correct the errors below",
            extra_tags="alert alert-dismissible alert-danger")

        return super(RegisterUserView, self).form_invalid(form)

    def get_success_url(self):
        """Override default function"""

        messages.success(
            request=self.request,
            message='Account registered',
            extra_tags="alert alert-dismissible alert-success")

        return reverse_lazy("image_app:dashboard")


class CreateUserView(LoginRequiredMixin, FormView):
    template_name = 'biosample/create_user.html'
    form_class = CreateUserForm

    # add the request to the kwargs
    # https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
    # this is needed to display messages (django.contrib) on pages
    def get_form_kwargs(self):
        kwargs = super(CreateUserView, self).get_form_kwargs()

        # create a new biosample user
        username = "image-%s" % (get_random_string(length=8))

        # add username to instance
        kwargs['username'] = username

        # add the request to the kwargs
        # https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
        kwargs['request'] = self.request
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        # this will ask to login to an un-logged user
        if not request.user.is_authenticated:
            return self.handle_no_permission()

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
                CreateUserView, self).dispatch(request, *args, **kwargs)

        else:
            messages.warning(
                request=self.request,
                message='Your biosample account is already registered',
                extra_tags="alert alert-dismissible alert-warning")

            return redirect('image_app:dashboard')

    def form_valid(self, form):
        """Create a new team in with biosample manager user, then crete a new
        user and register it"""

        password = form.cleaned_data['password1']
        confirmPwd = form.cleaned_data['password2']

        # get user model associated with this session
        user = self.request.user

        first_name = user.first_name
        last_name = user.last_name
        email = user.email
        organization = user.person.organization.name

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
                organization=organization
            )

        except ConnectionError as e:
            logger.error("Problem in creating user %s" % (form.username))
            logger.error("Message was: %s" % (json.loads(str(e))['message']))
            messages.error(
                self.request,
                message="Problem in creating user %s",
                extra_tags="alert alert-dismissible alert-danger")

            messages.error(
                self.request,
                message="Message was: %s" % (json.loads(str(e))['message']),
                extra_tags="alert alert-dismissible alert-danger")

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

    def get_success_url(self):
        """Override default function"""

        messages.success(
            request=self.request,
            message='Account created',
            extra_tags="alert alert-dismissible alert-success")

        return reverse_lazy("image_app:dashboard")
