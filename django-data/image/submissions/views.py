#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 15:49:23 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import io
import re
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, StreamingHttpResponse
from django.views.generic import (
    CreateView, DetailView, ListView, UpdateView, DeleteView)
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import BaseUpdateView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse

from common.constants import (
    WAITING, ERROR, SUBMITTED, NEED_REVISION, CRYOWEB_TYPE, CRB_ANIM_TYPE,
    TIME_UNITS, VALIDATION_MESSAGES_ATTRIBUTES, SAMPLE_STORAGE,
    SAMPLE_STORAGE_PROCESSING, ACCURACIES, UNITS_VALIDATION_MESSAGES,
    VALUES_VALIDATION_MESSAGES)
from common.helpers import uid2biosample
from common.views import OwnerMixin, FormInvalidMixin
from crbanim.tasks import ImportCRBAnimTask
from cryoweb.tasks import ImportCryowebTask

from uid.models import Submission, Animal, Sample
from excel.tasks import ImportTemplateTask

from validation.helpers import construct_validation_message
from validation.models import ValidationSummary
from animals.tasks import BatchDeleteAnimals, BatchUpdateAnimals
from samples.tasks import BatchDeleteSamples, BatchUpdateSamples

from .forms import SubmissionForm, ReloadForm, UpdateSubmissionForm
from .helpers import is_target_in_message, AnimalResource, SampleResource

# Get an instance of a logger
logger = logging.getLogger(__name__)


class CreateSubmissionView(LoginRequiredMixin, FormInvalidMixin, CreateView):
    form_class = SubmissionForm
    model = Submission

    # template name is derived from model position and views type.
    # in this case, ir will be 'uid/submission_form.html' so
    # i need to clearly specify it
    template_name = "submissions/submission_form.html"

    # add user to this object
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.owner = self.request.user

        # I will have a different loading function accordingly with data type
        if self.object.datasource_type == CRYOWEB_TYPE:
            # update object and force status
            self.object.message = "waiting for data loading"
            self.object.status = WAITING
            self.object.save()

            # create a task
            my_task = ImportCryowebTask()

            # a valid submission start a task
            res = my_task.delay(self.object.pk)
            logger.info(
                "Start cryoweb importing process with task %s" % res.task_id)

        # I will have a different loading function accordingly with data type
        elif self.object.datasource_type == CRB_ANIM_TYPE:
            # update object and force status
            self.object.message = "waiting for data loading"
            self.object.status = WAITING
            self.object.save()

            # create a task
            my_task = ImportCRBAnimTask()

            # a valid submission start a task
            res = my_task.delay(self.object.pk)
            logger.info(
                "Start crbanim importing process with task %s" % res.task_id)

        else:
            # update object and force status
            self.object.message = "waiting for data loading"
            self.object.status = WAITING
            self.object.save()

            # create a task
            my_task = ImportTemplateTask()

            # a valid submission start a task
            res = my_task.delay(self.object.pk)
            logger.info(
                "Start template importing process with task %s" % res.task_id)

        # a redirect to self.object.get_absolute_url()
        return HttpResponseRedirect(self.get_success_url())


class MessagesSubmissionMixin(object):
    """Display messages in SubmissionViews"""

    # https://stackoverflow.com/a/45696442
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        # get the submission message
        message = self.submission.message

        # check if data are loaded or not
        if self.submission.status in [WAITING, SUBMITTED]:
            messages.warning(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-warning")

        elif self.submission.status in [ERROR, NEED_REVISION]:
            messages.error(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-danger")

        elif message is not None and message != '':
            messages.info(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-info")

        return data


class DetailSubmissionView(MessagesSubmissionMixin, OwnerMixin, DetailView):
    model = Submission
    template_name = "submissions/submission_detail.html"

    def get_context_data(self, **kwargs):
        # pass self.object to a new submission attribute in order to call
        # MessagesSubmissionMixin.get_context_data()
        self.submission = self.object

        # Call the base implementation first to get a context
        context = super(DetailSubmissionView, self).get_context_data(**kwargs)

        # add submission report to context
        validation_summary = construct_validation_message(self.submission)

        # HINT: is this computational intensive?
        context["validation_summary"] = validation_summary

        return context


class SubmissionValidationSummaryView(OwnerMixin, DetailView):
    model = Submission
    template_name = "submissions/submission_validation_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        summary_type = self.kwargs['type']
        try:
            validation_summary = self.object.validationsummary_set\
                .get(type=summary_type)
            context['validation_summary'] = validation_summary

            editable = list()

            for message in validation_summary.messages:
                if 'offending_column' not in message:
                    txt = ("Old validation results, please re-run validation"
                           " step!")
                    logger.warning(txt)
                    messages.warning(
                        request=self.request,
                        message=txt,
                        extra_tags="alert alert-dismissible alert-warning")
                    editable.append(False)

                elif (uid2biosample(message['offending_column']) in
                        [val for sublist in VALIDATION_MESSAGES_ATTRIBUTES for
                         val in sublist]):
                    logger.debug(
                        "%s is editable" % message['offending_column'])
                    editable.append(True)
                else:
                    logger.debug(
                        "%s is not editable" % message['offending_column'])
                    editable.append(False)

            context['editable'] = editable

        except ObjectDoesNotExist:
            context['validation_summary'] = None

        context['submission'] = Submission.objects.get(pk=self.kwargs['pk'])

        return context


class EditSubmissionMixin():
    """A mixin to deal with Updates, expecially when searching ListViews"""

    def dispatch(self, request, *args, **kwargs):
        handler = super(EditSubmissionMixin, self).dispatch(
                request, *args, **kwargs)

        # here I've done get_queryset. Check for submission status
        if hasattr(self, "submission") and not self.submission.can_edit():
            message = "Cannot edit submission: current status is: %s" % (
                    self.submission.get_status_display())

            logger.warning(message)
            messages.warning(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-warning")

            return redirect(self.submission.get_absolute_url())

        return handler


class SubmissionValidationSummaryFixErrorsView(
        EditSubmissionMixin, OwnerMixin, ListView):
    template_name = "submissions/submission_validation_summary_fix_errors.html"

    def get_queryset(self):
        """Define columns that need to change"""

        self.submission = get_object_or_404(
            Submission,
            pk=self.kwargs['pk'],
            owner=self.request.user)

        self.summary_type = self.kwargs['type']
        self.validation_summary = ValidationSummary.objects.get(
            submission=self.submission, type=self.summary_type)
        self.message = self.validation_summary.messages[
            int(self.kwargs['message_counter'])]

        self.offending_column = uid2biosample(
            self.message['offending_column'])
        self.show_units = True
        if is_target_in_message(self.message['message'],
                                UNITS_VALIDATION_MESSAGES):
            self.units = [unit.name for unit in TIME_UNITS]
            if self.offending_column == 'animal_age_at_collection':
                self.offending_column += "_units"

        elif is_target_in_message(self.message['message'],
                                  VALUES_VALIDATION_MESSAGES):
            if self.offending_column == 'storage':
                self.units = [unit.name for unit in SAMPLE_STORAGE]
            elif self.offending_column == 'storage_processing':
                self.units = [unit.name for unit in SAMPLE_STORAGE_PROCESSING]
            elif self.offending_column == 'collection_place_accuracy' or \
                    self.offending_column == 'birth_location_accuracy':
                self.units = [unit.name for unit in ACCURACIES]
        else:
            self.show_units = False
            self.units = None
        if self.summary_type == 'animal':
            return Animal.objects.filter(id__in=self.message['ids'])
        elif self.summary_type == 'sample':
            return Sample.objects.filter(id__in=self.message['ids'])

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(
            SubmissionValidationSummaryFixErrorsView, self
        ).get_context_data(**kwargs)

        # add submission to context
        context["message"] = self.message
        context["type"] = self.summary_type
        context['attribute_to_edit'] = self.offending_column
        for attributes in VALIDATION_MESSAGES_ATTRIBUTES:
            if self.offending_column in attributes:
                context['attributes_to_show'] = [
                    attr for attr in attributes if
                    attr != self.offending_column
                ]
        context['submission'] = self.submission
        context['show_units'] = self.show_units
        if self.units:
            context['units'] = self.units
        return context


# a detail view since I need to operate on a submission object
# HINT: rename to a more informative name?
class EditSubmissionView(
        EditSubmissionMixin, MessagesSubmissionMixin, OwnerMixin, ListView):
    template_name = "submissions/submission_edit.html"
    paginate_by = 10

    # set the columns for this union query
    headers = [
        'id',
        'name',
        'material',
        'biosample_id',
        'status',
        'last_changed',
        'last_submitted'
    ]

    def get_queryset(self):
        """Subsetting names relying submission id"""

        self.submission = get_object_or_404(
            Submission,
            pk=self.kwargs['pk'],
            owner=self.request.user)

        # need to perform 2 distinct queryset
        animal_qs = Animal.objects.filter(
            submission=self.submission).values_list(*self.headers)

        sample_qs = Sample.objects.filter(
            submission=self.submission).values_list(*self.headers)

        return animal_qs.union(sample_qs).order_by('material', 'id')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(EditSubmissionView, self).get_context_data(**kwargs)

        # add submission to context
        context["submission"] = self.submission

        # modify queryset to a more useful object
        object_list = context["object_list"]

        # the new result object
        new_object_list = []

        for element in object_list:
            # modify element in a dictionary
            element = dict(zip(self.headers, element))

            if element['material'] == 'Organism':
                # change material to be more readable
                element['material'] = 'animal'
                element['model'] = Animal.objects.get(pk=element['id'])

            else:
                # this is a specimen
                element['material'] = 'sample'
                element['model'] = Sample.objects.get(pk=element['id'])

            new_object_list.append(element)

        # ovverride the default object list
        context["object_list"] = new_object_list

        return context


# streaming CSV large files, as described in
# https://docs.djangoproject.com/en/2.2/howto/outputting-csv/#streaming-large-csv-files
class ExportSubmissionView(OwnerMixin, BaseDetailView):
    model = Submission

    def get(self, request, *args, **kwargs):
        """A view that streams a large CSV file."""

        # required to call queryset and to initilize the proper BaseDetailView
        # attributes
        self.object = self.get_object()

        # ok define two distinct queryset to filter animals and samples
        # relying on a submission object (self.object)
        animal_qs = Animal.objects.filter(submission=self.object)
        sample_qs = Sample.objects.filter(submission=self.object)

        # get the two import_export.resources.ModelResource objects
        animal_resource = AnimalResource()
        sample_resource = SampleResource()

        # get the two data objects relying on custom queryset
        animal_dataset = animal_resource.export(animal_qs)
        sample_dataset = sample_resource.export(sample_qs)

        # merge the two tablib.Datasets into one
        merged_dataset = animal_dataset.stack(sample_dataset)

        # streaming a response
        response = StreamingHttpResponse(
            io.StringIO(merged_dataset.csv),
            content_type="text/csv")
        response['Content-Disposition'] = (
            'attachment; filename="submission_%s_names.csv"' % self.object.id)

        return response


class ListSubmissionsView(OwnerMixin, ListView):
    model = Submission
    template_name = "submissions/submission_list.html"
    ordering = ['-created_at']
    paginate_by = 10


class ReloadSubmissionView(OwnerMixin, FormInvalidMixin, UpdateView):
    form_class = ReloadForm
    model = Submission
    template_name = 'submissions/submission_reload.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)

        # update object and force status
        self.object.message = "waiting for data loading"
        self.object.status = WAITING
        self.object.save()

        # call the proper method
        if self.object.datasource_type == CRYOWEB_TYPE:
            # a valid submission start a task
            my_task = ImportCryowebTask()

            res = my_task.delay(self.object.pk)
            logger.info(
                "Start cryoweb reload process with task %s" % res.task_id)

        elif self.object.datasource_type == CRB_ANIM_TYPE:
            # a valid submission start a task
            my_task = ImportCRBAnimTask()

            # a valid submission start a task
            res = my_task.delay(self.object.pk)
            logger.info(
                "Start crbanim reload process with task %s" % res.task_id)

        else:
            # a valid submission start a task
            my_task = ImportTemplateTask()

            # a valid submission start a task
            res = my_task.delay(self.object.pk)
            logger.info(
                "Start template reload process with task %s" % res.task_id)

        # a redirect to self.object.get_absolute_url()
        return HttpResponseRedirect(self.get_success_url())


class DeleteSubmissionMixin():
    """Prevent a delete relying on statuses"""

    def dispatch(self, request, *args, **kwargs):
        handler = super(DeleteSubmissionMixin, self).dispatch(
                request, *args, **kwargs)

        # here I've done get_queryset. Check for submission status
        if hasattr(self, "object") and not self.object.can_delete():
            message = "Cannot delete %s: submission status is: %s" % (
                    self.object, self.object.get_status_display())

            logger.warning(message)
            messages.warning(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-warning")

            return redirect(self.object.get_absolute_url())

        return handler


class BatchDeleteMixin(
        DeleteSubmissionMixin, OwnerMixin):

    model = Submission
    delete_type = None

    def get_context_data(self, **kwargs):
        """Add custom values to template context"""

        context = super().get_context_data(**kwargs)

        context['delete_type'] = self.delete_type
        context['pk'] = self.object.id

        return context

    def post(self, request, *args, **kwargs):
        # get object (Submission) like BaseUpdateView does
        submission = self.get_object()

        # get arguments from post object
        pk = self.kwargs['pk']
        keys_to_delete = set()

        # process all keys in form
        for key in request.POST['to_delete'].split('\n'):
            keys_to_delete.add(key.rstrip())

        submission.message = 'waiting for batch delete to complete'
        submission.status = WAITING
        submission.save()

        if self.delete_type == 'Animals':
            # Batch delete task for animals
            my_task = BatchDeleteAnimals()
            summary_obj, created = ValidationSummary.objects.get_or_create(
                submission=submission, type='animal')

        elif self.delete_type == 'Samples':
            # Batch delete task for samples
            my_task = BatchDeleteSamples()
            summary_obj, created = ValidationSummary.objects.get_or_create(
                submission=submission, type='sample')

        # reset validation counters
        summary_obj.reset()
        res = my_task.delay(pk, [item for item in keys_to_delete])

        logger.info(
            "Start %s batch delete with task %s" % (
                self.delete_type, res.task_id))

        return HttpResponseRedirect(reverse('submissions:detail', args=(pk,)))


class DeleteAnimalsView(BatchDeleteMixin, DetailView):
    model = Submission
    template_name = 'submissions/submission_batch_delete.html'
    delete_type = 'Animals'


class DeleteSamplesView(BatchDeleteMixin, DetailView):
    model = Submission
    template_name = 'submissions/submission_batch_delete.html'
    delete_type = 'Samples'


class DeleteSubmissionView(DeleteSubmissionMixin, OwnerMixin, DeleteView):
    model = Submission
    template_name = "submissions/submission_confirm_delete.html"
    success_url = reverse_lazy('uid:dashboard')

    # https://stackoverflow.com/a/39533619/4385116
    def get_context_data(self, **kwargs):
        # determining related objects
        context = super().get_context_data(**kwargs)

        # counting object relying submission
        animal_count = Animal.objects.filter(
            submission=self.object).count()
        sample_count = Sample.objects.filter(
            submission=self.object).count()

        # get only sample and animals from model_count
        info_deleted = {
            'animals': animal_count,
            'samples': sample_count
        }

        # add info to context
        context['info_deleted'] = dict(info_deleted).items()

        return context

    # https://ccbv.co.uk/projects/Django/1.11/django.views.generic.edit/DeleteView/#delete
    def delete(self, request, *args, **kwargs):
        """
        Add a message after calling base delete method
        """

        httpresponseredirect = super().delete(request, *args, **kwargs)

        message = "Submission %s was successfully deleted" % self.object.title
        logger.info(message)

        messages.info(
            request=self.request,
            message=message,
            extra_tags="alert alert-dismissible alert-info")

        return httpresponseredirect


class UpdateSubmissionView(OwnerMixin, FormInvalidMixin, UpdateView):
    form_class = UpdateSubmissionForm
    model = Submission
    template_name = 'submissions/submission_update.html'


class FixValidation(OwnerMixin, BaseUpdateView):
    model = Submission

    def post(self, request, **kwargs):
        # get object (Submission) like BaseUpdateView does
        submission = self.get_object()

        # Fetch all required ids from input names and use it as keys
        keys_to_fix = dict()
        for key_to_fix in request.POST:
            if 'to_edit' in key_to_fix:
                keys_to_fix[
                    int(re.search('to_edit(.*)', key_to_fix).groups()[0])] \
                    = request.POST[key_to_fix]

        pk = self.kwargs['pk']
        record_type = self.kwargs['record_type']
        attribute_to_edit = self.kwargs['attribute_to_edit']

        submission.message = "waiting for data updating"
        submission.status = WAITING
        submission.save()

        # Update validation summary
        summary_obj, created = ValidationSummary.objects.get_or_create(
            submission=submission, type=record_type)
        summary_obj.submission = submission
        summary_obj.reset()

        # create a task
        if record_type == 'animal':
            my_task = BatchUpdateAnimals()
        elif record_type == 'sample':
            my_task = BatchUpdateSamples()
        else:
            return HttpResponseRedirect(
                reverse('submissions:detail', args=(pk,)))

        # a valid submission start a task
        res = my_task.delay(pk, keys_to_fix, attribute_to_edit)
        logger.info(
            "Start fix validation process with task %s" % res.task_id)
        return HttpResponseRedirect(reverse('submissions:detail', args=(pk,)))
