
import json
import logging

from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, CreateView
from django.contrib import messages

from pyEBIrest import Auth

from .forms import CreateAuthViewForm, RegisterUserForm

# Get an instance of a logger
logger = logging.getLogger(__name__)


# dispatch is an internal method Django use (defined inside the View class)
@method_decorator(login_required, name='dispatch')
class CreateAuthView(FormView):

    template_name = 'biosample/generate_token.html'
    form_class = CreateAuthViewForm

    # add the request to the kwargs
    # https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
    # this is needed to display messages (django.contronb) on pages
    def get_form_kwargs(self):
        kwargs = super(CreateAuthView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

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


@method_decorator(login_required, name='dispatch')
class AuthView(TemplateView):
    template_name = 'biosample/token.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(AuthView, self).get_context_data(**kwargs)

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


@method_decorator(login_required, name='dispatch')
class RegisterUserView(CreateView):
    template_name = 'biosample/register_user.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('image_app:dashboard')

    # add the request to the kwargs
    # https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
    # this is needed to display messages (django.contrib) on pages
    def get_form_kwargs(self):
        kwargs = super(RegisterUserView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super(RegisterUserView, self).get_initial()
        initial['user_id'] = self.request.user.id
        initial['user'] = self.request.user
        return initial

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        name = form.cleaned_data['name']
        password = form.cleaned_data['password']
        team = form.cleaned_data['team']

        try:
            auth = Auth(user=name, password=password)

            if team not in auth.claims['domains']:
                messages.error(
                    self.request,
                    "You don't belong to team: %s" % team,
                    extra_tags="alert alert-dismissible alert-danger")

                # return invalid form
                return self.form_invalid(form)

            # record token in session
            self.request.session['token'] = auth.token
            return super(RegisterUserView, self).form_valid(form)

        except ConnectionError as e:
            # logger exception. With repr() the exception name is rendered
            logger.error(repr(e))

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
            message='Account registered',
            extra_tags="alert alert-dismissible alert-success")

        return reverse_lazy("image_app:dashboard")
