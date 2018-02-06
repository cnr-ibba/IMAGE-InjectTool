#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 15:04:07 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.management import call_command

from image_app.forms import DataSourceForm


# TODO: render as a FormView
class DataSourceView(View):
    """Handling DataSource forms with class based views"""

    form_class = DataSourceForm
    template_name = "image_app/data_upload.html"

    def get(self, request, *args, **kwargs):
        """Return this when accessing form through GET method"""

        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        """Return this when accessing form through POST method"""

        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            # save data
            form.save()

            # return to succes page (home in this case)
            return HttpResponseRedirect('admin:index')

        return render(request, self.template_name, {'form': form})


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
    call_command('truncate_image_tables')

    return redirect('admin:index')


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

    call_command('truncate_image_tables')

    return redirect('admin:index')
