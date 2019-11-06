#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 21 15:37:16 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import io
import csv
import urllib
import logging
import pycountry

from collections import defaultdict, namedtuple

from django.utils.dateparse import parse_date

from common.constants import LOADED, ERROR, MISSING, SAMPLE_STORAGE
from common.helpers import image_timedelta
from uid.helpers import (
    FileDataSourceMixin, get_or_create_obj, update_or_create_obj)
from uid.models import (
    DictSpecie, DictSex, DictCountry, DictBreed, Animal, Sample,
    DictUberon, Publication)
from submissions.helpers import send_message
from validation.helpers import construct_validation_message
from validation.models import ValidationSummary

# Get an instance of a logger
logger = logging.getLogger(__name__)


# A class to deal with cryoweb import errors
class CRBAnimImportError(Exception):
    pass


class CRBAnimReader(FileDataSourceMixin):
    mandatory_columns = [
            'sex',
            'species_latin_name',
            'country_of_origin',
            'breed_name',
            'animal_ID',
            'sample_bibliographic_references',
            'sample_identifier',
            'animal_birth_date',
            'sample_storage_temperature',
            'sample_type_name',
            'body_part_name',
            'sampling_date',
            'sampling_protocol_url',
            'sample_availability',
            'EBI_Biosample_identifier',
        ]

    def __init__(self):
        self.data = None
        self.header = None
        self.dialect = None
        self.items = None
        self.filename = None

    @classmethod
    def get_dialect(cls, chunk):
        """Determine dialect of a CSV from a chunk"""

        return csv.Sniffer().sniff(chunk)

    @classmethod
    def is_valid(cls, chunk):
        """Try to determine if CRBanim has at least the required columns
        or not"""

        dialect = cls.get_dialect(chunk)

        # get a handle from a string
        handle = io.StringIO(chunk)

        # read chunk
        reader = csv.reader(handle, dialect)
        header = next(reader)

        not_found = []

        for column in cls.mandatory_columns:
            if column not in header:
                not_found.append(column)

        if len(not_found) == 0:
            logger.debug("This seems to be a valid CRBanim file")
            return True, []

        else:
            logger.error("Couldn't not find mandatory CRBanim columns %s" % (
                not_found))
            return False, not_found

    def read_file(self, filename):
        """Read crb anim files and set tit to class attribute"""

        with open(filename, newline='') as handle:
            # initialize data
            self.filename = filename
            self.data = []

            # get dialect
            chunk = handle.read(2048)
            self.dialect = self.get_dialect(chunk)

            # restart filename from the beginning
            handle.seek(0)

            # read csv file
            reader = csv.reader(handle, self.dialect)
            self.header = next(reader)

            # find sex index column
            sex_idx = self.header.index('sex')

            # create a namedtuple object
            Data = namedtuple("Data", self.header)

            # add records to data
            for record in reader:
                # replace all "\\N" occurences in a list
                record = [None if col in ["\\N", ""]
                          else col for col in record]

                # 'unknown' sex should be replaced with 'record of unknown sex'
                if record[sex_idx].lower() == 'unknown':
                    logger.debug(
                        "Changing '%s' with '%s'" % (
                            record[sex_idx], 'record of unknown sex'))
                    record[sex_idx] = 'record of unknown sex'

                record = Data._make(record)
                self.data.append(record)

        self.items = self.eval_columns()

    def eval_columns(self):
        """define a set from column data"""

        # target_columns = ['sex', 'species_latin_name', 'breed_name']
        target_columns = self.header

        items = defaultdict(list)

        for line in self.data:
            for column in target_columns:
                idx = self.header.index(column)
                items[column].append(line[idx])

        # now get a set of object
        for column in target_columns:
            items[column] = set(items[column])

        return items

    def print_line(self, num):
        """print a record with its column names"""

        for i, column in enumerate(self.header):
            logger.debug("%s: %s" % (column, self.data[num][i]))

    def filter_by_column_values(self, column, values, ignorecase=False):
        if ignorecase is True:
            # lower values
            values = [value.lower() for value in values]

        for line in self.data:
            # search for case insensitive value (lower attrib in lower values)
            if ignorecase is True:
                if getattr(line, column).lower() in values:
                    yield line

                else:
                    logger.debug("Filtering: %s" % (str(line)))

            else:
                if getattr(line, column) in values:
                    yield line

                else:
                    logger.debug("Filtering: %s" % (str(line)))

            # ignore case or not

        # cicle for line

    # a function to detect if crbanim species are in UID database or not
    def check_species(self, country):
        """Check if all species are defined in UID DictSpecies"""

        # CRBAnim usually have species in the form required for UID
        # However sometimes there could be a common name, not a DictSpecie one
        column = 'species_latin_name'
        item_set = self.items[column]

        # call FileDataSourceMixin.check_species
        return super().check_species(column, item_set, country)

    # check that dict sex table contains data
    def check_sex(self):
        """check that dict sex table contains data"""

        # item.sex are in uppercase
        column = 'sex'
        item_set = [item.lower() for item in self.items[column]]

        # call FileDataSourceMixin.check_items
        return self.check_items(item_set, DictSex, column)

    def check_countries(self):
        """Check that all efabis countries are present in database"""

        def get_label(country_of_origin):
            return pycountry.countries.get(
                alpha_2=country_of_origin).name

        column = "country_of_origin"
        item_set = [get_label(item) for item in self.items[column]]

        # call FileDataSourceMixin.check_items
        return self.check_items(item_set, DictCountry, column)


def fill_uid_breed(record, language):
    """Fill DictBreed from a crbanim record"""

    # get a DictSpecie object. Species are in latin names, but I can
    # find also a common name in translation tables
    specie = DictSpecie.get_specie_check_synonyms(
            species_label=record.species_latin_name,
            language=language)

    # get country name using pycountries
    country_name = pycountry.countries.get(
        alpha_2=record.country_of_origin).name

    # get country for breeds. Ideally will be the same of submission,
    # however, it could be possible to store data from other contries
    country = DictCountry.objects.get(label=country_name)

    breed = get_or_create_obj(
        DictBreed,
        supplied_breed=record.breed_name,
        specie=specie,
        country=country)

    # return a DictBreed object
    return breed


def fill_uid_animal(record, breed, submission, animals):
    """Helper function to fill animal data in UID animal table"""

    # HINT: does CRBAnim models mother and father?

    # check if such animal is already beed updated
    if record.animal_ID in animals:
        logger.debug(
            "Ignoring %s: already created or updated" % (record.animal_ID))

        # return an animal object
        animal = animals[record.animal_ID]

    else:
        # determine sex. Check for values
        sex = DictSex.objects.get(label__iexact=record.sex)

        # there's no birth_location for animal in CRBAnim
        accuracy = MISSING

        # create a new object. Using defaults to avoid collisions when
        # updating data
        # HINT: CRBanim has less attribute than cryoweb
        defaults = {
            # HINT: is a duplication of name. Can this be non-mandatory?
            'alternative_id': record.animal_ID,
            'sex': sex,
            'birth_date': record.animal_birth_date,
            'birth_location_accuracy': accuracy,
        }

        # I could have the same animal again and again. by tracking it in a
        # dictionary, I will change animal once
        animal = update_or_create_obj(
            Animal,
            name=record.animal_ID,
            breed=breed,
            owner=submission.owner,
            submission=submission,
            defaults=defaults)

        # track this animal in dictionary
        animals[record.animal_ID] = animal

    # I need to track animal to relate the sample
    return animal


def find_storage_type(record):
    """Determine a sample storage relying on a dictionary"""

    mapping = {
        '-196°C': 'frozen, liquid nitrogen',
        '-20°C': 'frozen, -20 degrees Celsius freezer',
        '-30°C': 'frozen, -20 degrees Celsius freezer',
        '-80°C': 'frozen, -80 degrees Celsius freezer'}

    if record.sample_storage_temperature in mapping:
        # get ENUM conversion
        storage = SAMPLE_STORAGE.get_value_by_desc(
            mapping[record.sample_storage_temperature])

        return storage

    else:
        logging.warning("Couldn't find %s in storage types mapping" % (
            record.sample_storage_temperature))

        return None


def sanitize_url(url):
    """Quote URLs for accession"""

    return urllib.parse.quote(url, ':/#?=')


def fill_uid_sample(record, animal, submission):
    """Helper function to fill animal data in UID sample table"""

    # name and animal name come from parameters
    organism_part_label = None
    sample_type_name = record.sample_type_name.lower()
    body_part_name = record.body_part_name.lower()

    # sylvain has proposed to apply the following decision rule:
    if body_part_name != "unknown" and body_part_name != "not relevant":
        organism_part_label = body_part_name

    else:
        organism_part_label = sample_type_name

    # get a organism part. Organism parts need to be in lowercases
    organism_part = get_or_create_obj(
        DictUberon,
        label=organism_part_label
    )

    # calculate animal age at collection
    animal_birth_date = parse_date(record.animal_birth_date)
    sampling_date = parse_date(record.sampling_date)
    animal_age_at_collection, time_units = image_timedelta(
        sampling_date, animal_birth_date)

    # get a publication (if present)
    publication = None

    if record.sample_bibliographic_references:
        publication = get_or_create_obj(
            Publication,
            doi=record.sample_bibliographic_references)

    # create a new object. Using defaults to avoid collisions when
    # updating data
    defaults = {
        # HINT: is a duplication of name. Can this be non-mandatory?
        'alternative_id': record.sample_identifier,
        'collection_date': record.sampling_date,
        'protocol': record.sampling_protocol_url,
        'organism_part': organism_part,
        # 'description': v_vessel.comment,
        'storage': find_storage_type(record),
        'availability': sanitize_url(record.sample_availability),
        'animal_age_at_collection': animal_age_at_collection,
        'animal_age_at_collection_units': time_units,
        'publication': publication,
    }

    sample = update_or_create_obj(
        Sample,
        name=record.sample_identifier,
        animal=animal,
        owner=submission.owner,
        submission=submission,
        defaults=defaults)

    return sample


def process_record(record, submission, animals, language):
    # Peter mail 26/02/19 18:30: I agree that it sounds like we will
    # need to create sameAs BioSamples for the IMAGE project, and it makes
    # sense that the inject tool is able to do this.  It may be that we
    # tackle these cases after getting the main part of the inject tool
    # functioning and hold or ignore these existing BioSamples for now.
    # HINT: record with a biosample id should be ignored, for the moment
    if record.EBI_Biosample_identifier is not None:
        logger.warning("Ignoring %s: already in biosample!" % str(record))
        return

    # filling breeds
    breed = fill_uid_breed(record, language)

    # fill animal
    animal = fill_uid_animal(record, breed, submission, animals)

    # fill sample
    fill_uid_sample(record, animal, submission)


def check_UID(submission, reader):
    # check for species and sex in a similar way as cryoweb does
    check, not_found = reader.check_sex()

    if not check:
        message = (
            "Not all Sex terms are loaded into database: "
            "check for '%s' in your dataset" % (not_found))

        raise CRBAnimImportError(message)

    # check for countries
    check, not_found = reader.check_countries()

    if not check:
        message = (
            "Not all countries are loaded into database: "
            "check for '%s' in your dataset" % (not_found))

        raise CRBAnimImportError(message)

    check, not_found = reader.check_species(submission.gene_bank_country)

    if not check:
        raise CRBAnimImportError(
            "Some species are not loaded in UID database: "
            "check for '%s' in your dataset" % (not_found))


def upload_crbanim(submission):
    # debug
    logger.info("Importing from CRB-Anim file")

    # this is the full path in docker container
    fullpath = submission.get_uploaded_file_path()

    # read submission data
    reader = CRBAnimReader()
    reader.read_file(fullpath)

    # start data loading
    try:
        # check UID data like cryoweb does
        check_UID(submission, reader)

        # ok get languages from submission (useful for translation)
        # HINT: no traslations implemented, at the moment
        language = submission.gene_bank_country.label

        # a dictionary in which store animal data
        animals = {}

        for record in reader.data:
            process_record(record, submission, animals, language)

        # after processing records, initilize validationsummary objects
        # create a validation summary object and set all_count
        vs_animal = get_or_create_obj(
            ValidationSummary,
            submission=submission,
            type="animal")

        # reset counts
        vs_animal.reset_all_count()

        vs_sample = get_or_create_obj(
            ValidationSummary,
            submission=submission,
            type="sample")

        # reset counts
        vs_sample.reset_all_count()

    except Exception as exc:
        # set message:
        message = "Error in importing data: %s" % (str(exc))

        # save a message in database
        submission.status = ERROR
        submission.message = message
        submission.save()

        # send async message
        send_message(submission)

        # debug
        logger.error("error in importing from crbanim: %s" % (exc))
        logger.exception(exc)

        return False

    else:
        message = "CRBAnim import completed for submission: %s" % (
            submission.id)

        submission.message = message
        submission.status = LOADED
        submission.save()

        # send async message
        send_message(
            submission,
            validation_message=construct_validation_message(submission))

    logger.info("Import from CRBAnim is complete")

    return True
