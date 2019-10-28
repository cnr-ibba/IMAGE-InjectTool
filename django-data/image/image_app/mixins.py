#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 14:46:39 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Define mixins classes for image_app.models

"""

import logging

from django.db import connections
from django.utils import timezone

from common.constants import STATUSES
from common.helpers import format_attribute

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Adding a classmethod to Category if you want to enable truncate
# https://books.agiliq.com/projects/django-orm-cookbook/en/latest/truncate.html
class BaseMixin(object):
    """Base class for UID tables. It implement common stuff for all UID
    tables::

        from image_app.models import BaseMixin

        class Submission(BaseMixin):
            pass

    """

    @classmethod
    def truncate(cls):
        """
        Truncate table data and restart indexes from 0::

            from image_app.models import Submission

            Submission.truncate()
        """

        # Django.db.connections is a dictionary-like object that allows you
        # to retrieve a specific connection using its alias
        with connections["default"].cursor() as cursor:
            statement = "TRUNCATE TABLE {0} RESTART IDENTITY CASCADE".format(
                cls._meta.db_table)
            logger.debug(statement)
            cursor.execute(statement)


class BioSampleMixin(BaseMixin):
    """
    Common methods for animal and samples useful in biosample generation
    Need to called with data into biosample or animals::

        from image_app.models import Animal

        animal = Animal.objects.get(pk=1)
        biosample_data = animal.to_biosample()

    """

    def __str__(self):
        return str(self.name)

    @property
    def person(self):
        """Retrieve :py:class:`Person` information from owner relationship"""

        return self.owner.person

    @property
    def organization(self):
        """Return :py:class:`Organization` relationship from related
        :py:class:`Submission` object"""

        return self.name.submission.organization

    @property
    def gene_bank_country(self):
        """Return :py:class:`DictCountry` relationship from related
        :py:class:`Submission` object"""

        return self.name.submission.gene_bank_country

    @property
    def gene_bank_name(self):
        """Return gene bank name from related :py:class:`Submission` object"""

        return self.name.submission.gene_bank_name

    @property
    def data_source_id(self):
        """Get Data source id (original animal/sample name) from related
        :py:class:`Name` object"""

        return self.name.name

    @property
    def submission(self):
        """Get related :py:class:`Submission` object throgh :py:class:`Name`
        """
        return self.name.submission

    @property
    def specie(self):
        raise NotImplementedError(
            "You need to define this method in your class")

    @property
    def biosample_id(self):
        """Get the biosample_id of an object (need to be submitted and
        retrieved sing USI)"""

        return self.name.biosample_id

    def get_same_as_relationship(self):
        """Format the same as attribute (if exists)"""

        if self.name.same_as and self.name.same_as != '':
            return {
                "relationshipNature": "same as",
                "accession": self.name.same_as
            }

        return None

    def get_attributes(self):
        """Common attribute definition required from Animal and samples. Need
        to be called inside Animal/sample get_atribute method. Keys
        is the name in metadata rules

        Returns:
            dict: a dictionary object
        """

        attributes = {}

        attributes['Data source ID'] = format_attribute(
            value=self.data_source_id)

        attributes['Alternative id'] = format_attribute(
            value=self.alternative_id)

        # HINT: this is a mandatory biosample field: could be removed from
        # attributes?
        attributes['Description'] = format_attribute(
            value=self.description)

        attributes["Project"] = format_attribute(
            value="IMAGE")

        attributes['Submission title'] = format_attribute(
            value=self.submission.title)

        attributes['Submission description'] = format_attribute(
            value=self.submission.description)

        attributes['Person last name'] = format_attribute(
            value=self.owner.last_name)

        attributes['Person initial'] = format_attribute(
            value=self.person.initials)

        attributes['Person first name'] = format_attribute(
            value=self.owner.first_name)

        attributes['Person email'] = format_attribute(
            value="mailto:%s" % (self.owner.email))

        attributes['Person affiliation'] = format_attribute(
            value=self.person.affiliation.name)

        attributes['Person role'] = self.person.role.format_attribute()

        attributes['Organization name'] = format_attribute(
            value=self.organization.name)

        attributes['Organization address'] = format_attribute(
            value=self.organization.address)

        attributes['Organization uri'] = format_attribute(
            value=self.organization.URI)

        attributes['Organization country'] = \
            self.organization.country.format_attribute()

        attributes[
            'Organization role'] = self.organization.role.format_attribute()

        # this could be present or not
        if self.name.publication:
            attributes['Publication DOI'] = format_attribute(
                value=self.name.publication.doi)

        attributes['Gene bank name'] = format_attribute(
            value=self.gene_bank_name)

        attributes[
            'Gene bank country'] = self.gene_bank_country.format_attribute()

        attributes['Data source type'] = format_attribute(
            value=self.submission.get_datasource_type_display())

        attributes['Data source version'] = format_attribute(
            value=self.submission.datasource_version)

        attributes['Species'] = self.specie.format_attribute()

        return attributes

    def to_biosample(self, release_date=None):
        """
        Common stuff to generate a biosample object. Need to be called
        inside Animal/Sample to_biosample method

        Args:
            release_date (str): data will no be published before this day
                (YYYY-MM-DD)

        Returns:
            dict: a dictionary object
        """

        result = {}

        # define mandatory fields
        result['alias'] = self.biosample_alias
        result['title'] = self.name.name

        # in case of update, I need to provide the old accession in payload
        if self.biosample_id and self.biosample_id != '':
            result['accession'] = self.biosample_id

        if release_date:
            result['releaseDate'] = release_date

        else:
            now = timezone.now()
            result['releaseDate'] = str(now.date())

        result['taxonId'] = self.specie.taxon_id

        result['taxon'] = self.specie.label

        # define optinal fields
        if self.description:
            result['description'] = self.description

        # define attributes that will be customized in Animal and sample
        result['attributes'] = self.get_attributes()

        # define an empty relationship array
        result['sampleRelationships'] = []

        # test for a same as relationship
        same_as_relationship = self.get_same_as_relationship()

        if same_as_relationship:
            result['sampleRelationships'].append(same_as_relationship)

        return result

    def __can_I(self, names):
        """
        Return True id self.status in statuses

        Args:
            names (list): a list of :py:class:`common.constants.STATUSES`

        Returns:
            bool
        """

        statuses = [x.value[0] for x in STATUSES if x.name in names]

        if self.submission.status not in statuses:
            return True

        else:
            return False

    def can_edit(self):
        """Returns True if I can edit a sample/animal according to submission
        status

        Returns:
            bool
        """

        names = ['waiting', 'submitted']

        return self.__can_I(names)

    def can_delete(self):
        """Returns True if I can delete a sample/animal according to submission
        status

        Returns:
            bool
        """

        names = ['waiting', 'submitted']

        return self.__can_I(names)
