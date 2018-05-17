#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 15:04:32 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

In this module, all function useful to export data are defined

"""

import logging

from image_app.models import Sample, Animal
from image_app.views import custom


# Get an instance of a logger
logger = logging.getLogger(__name__)


class SampleJSON(custom.BioSampleDetailView):
    """Get a specific sample in JSON"""

    model = Sample

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SampleJSON, self).get_context_data(**kwargs)

        # add a new object to context wich is rendered using
        # BioSampleDetailView and its method
        context["biosample"] = self.object.to_biosample()

        return context


class SampleListJSON(custom.BioSampleListView):
    """Get all samples from database in JSON"""

    model = Sample

    # limit results to 5
    queryset = Sample.objects.all()[:5]

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SampleListJSON, self).get_context_data(**kwargs)

        # add a new object to context wich is rendered using
        # BioSampleDetailView and its method. self.object_list has all
        # queryset objects
        context["biosample"] = [
                sample.to_biosample() for sample in self.object_list]

        # return a new context object
        return context


class AnimalJSON(custom.BioSampleDetailView):
    """Get a specific animal in JSON"""

    model = Animal

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(AnimalJSON, self).get_context_data(**kwargs)

        # add a new object to context wich is rendered using
        # BioSampleDetailView and its method
        context["biosample"] = self.object.to_biosample()

        # return a new context object
        return context


class AnimalListJSON(custom.BioSampleListView):
    """Get all animals from database in JSON"""

    model = Animal

    # limit results to 5
    queryset = Animal.objects.all()[:5]

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(AnimalListJSON, self).get_context_data(**kwargs)

        # add a new object to context wich is rendered using
        # BioSampleDetailView and its method. self.object_list has all
        # queryset objects
        context["biosample"] = [
                animal.to_biosample() for animal in self.object_list]

        # return a new context object
        return context


class BioSampleJSON(custom.BioSampleDetailView):
    """Get animal and its samples in JSON"""

    model = Animal

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(BioSampleJSON, self).get_context_data(**kwargs)

        # collect all json data for this animal
        animal_json = self.object.to_biosample()

        # then get all sample for such animal
        samples_json = []

        # collect each json for a sample
        for sample in self.object.sample_set.all():
            samples_json += [sample.to_biosample()]

        # now define biosample context with a sample key having a list
        # of all biosample data
        context["biosample"] = {'sample': [animal_json] + samples_json}

        # return a new context object
        return context


class BioSampleListJSON(custom.BioSampleListView):
    """Get all animals and their sample in a single json"""

    model = Animal

    # get only animals with samples and limiting results to 5
    queryset = Animal.objects.filter(sample__name__isnull=False).distinct()[:5]

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(BioSampleListJSON, self).get_context_data(**kwargs)

        # get all biosample data for animals
        animals_json = []
        samples_json = []

        # get animal data and add to a list
        for animal in self.object_list:
            animals_json += [animal.to_biosample()]

            # get samples data and add to a list
            for sample in animal.sample_set.all():
                samples_json += [sample.to_biosample()]

        # now define biosample context with a sample key having a list
        # of all biosample data
        context["biosample"] = {'sample': animals_json + samples_json}

        # return a new context object
        return context
