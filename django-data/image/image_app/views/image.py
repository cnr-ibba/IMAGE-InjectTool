#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 15:04:07 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.db import transaction
from django.shortcuts import redirect, render, reverse
from django.views.generic.edit import FormView

from image_app.forms import DataSourceForm, PersonForm, UserForm


class DataSourceView(FormView):
    """Handling DataSource forms with class based views"""

    form_class = DataSourceForm
    template_name = "image_app/data_upload.html"

    def get_success_url(self):
        """Override default function"""

        return reverse("admin:index")

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        # save data
        form.save()

        return super(DataSourceView, self).form_valid(form)


@login_required
@transaction.atomic
def update_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        person_form = PersonForm(request.POST, instance=request.user.person)

        if user_form.is_valid() and person_form.is_valid():
            user_form.save()
            person_form.save()

            messages.success(
                    request, 'Your profile was successfully updated!')

            return redirect('admin:index')

        else:
            messages.error(
                    request, 'Please correct the error below.')
    else:
        user_form = UserForm(instance=request.user)
        person_form = PersonForm(instance=request.user.person)

    return render(request, 'image_app/update_user.html', {
        'user_form': user_form,
        'person_form': person_form
    })


@login_required
def truncate_databases(request):
    """ truncate cryoweb and image tables

    this fx calls the custom functions truncate_cryoweb_tables and
    truncate_image_tables, defined in
    image_app/management/commands/truncate_cryoweb_tables.py and
    image_app/management/commands/truncate_image_tables.py
    in order to have the same fx "command line" is necessary to call both
    $ docker-compose run --rm uwsgi python manage.py truncate_cryoweb_tables
    $ docker-compose run --rm uwsgi python manage.py truncate_image_tables

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    call_command('truncate_cryoweb_tables')

    messages.success(request, 'cryoweb database was truncated '
                              'with success')

    call_command('truncate_image_tables')

    messages.success(request, 'image database was truncated with success')

    return redirect('admin:index')


# TODO: this will be removed in production
@login_required
def truncate_image_tables(request):
    """ truncate image tables

    this fx calls the custom function truncate_image_tables, defined in
    image_app/management/commands/truncate_image_tables.py
    this fx can also be called command line as
    $ docker-compose run --rm uwsgi python manage.py truncate_image_tables

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    # TODO: move commands to a function
    call_command('truncate_image_tables')

    messages.success(request, 'image database was truncated with success')

    return redirect('admin:index')
