#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 21 15:37:16 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import csv
import logging
import pycountry

from collections import defaultdict, namedtuple

from django.utils.dateparse import parse_date

from common.constants import LOADED, ERROR, MISSING
from common.helpers import image_timedelta
from image_app.models import (
    DictSpecie, DictSex, DictCountry, DictBreed, Name, Animal, Sample,
    DictUberon, Publication)
from language.helpers import check_species_synonyms

# Get an instance of a logger
logger = logging.getLogger(__name__)


# A class to deal with cryoweb import errors
class CRBAnimImportError(Exception):
    pass


class CRBAnimReader():
    def __init__(self):
        self.data = None
        self.header = None
        self.dialect = None
        self.items = None
        self.filename = None

    def read_file(self, filename):
        """Read crb anim files and set tit to class attribute"""

        with open(filename, newline='') as csvfile:
            # initialize data
            self.filename = filename
            self.data = []
            self.dialect = csv.Sniffer().sniff(csvfile.read(2048))
            csvfile.seek(0)

            # read csv file
            reader = csv.reader(csvfile, self.dialect)
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

    def __check_items(self, item_set, model, column):
        """General check of CRBanim items into database"""

        # a list of not found terms and a status to see if something is missing
        # or not
        not_found = []
        result = True

        for item in item_set:
            # check for species in database
            if not model.objects.filter(label=item).exists():
                not_found.append(item)

        if len(not_found) != 0:
            result = False
            logger.warning(
                "Those %s are not present in UID database:" % (column))
            logger.warning(not_found)

        return result, not_found

    # a function to detect if crbanim species are in UID database or not
    def check_species(self, country):
        """Check if all species are defined in UID DictSpecies"""

        # CRBAnim usually have species in the form required for UID
        # However sometimes there could be a common name, not a DictSpecie one
        column = 'species_latin_name'

        check, not_found = self.__check_items(
            self.items[column], DictSpecie, column)

        if check is False:
            # try to check in dictionary table
            logger.info("Searching for %s in dictionary tables" % (not_found))

            # if this function return True, I found all synonyms
            if check_species_synonyms(not_found, country) is True:
                logger.info("Found %s in dictionary tables" % not_found)

                # return True and an empty list for check and not found items
                return True, []

        # if I arrive here, there are species that I couldn't find
        logger.error("Couldnt' find those species in dictionary tables:")
        logger.error(not_found)

        return check, not_found

    # check that dict sex table contains data
    def check_sex(self):
        """check that dict sex table contains data"""

        # item.sex are in uppercase
        column = 'sex'
        item_set = [item.lower() for item in self.items[column]]

        return self.__check_items(item_set, DictSex, column)


def fill_uid_breed(record, language):
    """Fill DioctBreed from a crbanim record"""

    # get a DictSpecie object. Species are in latin names, but I can
    # find also a common name in translation tables
    try:
        specie = DictSpecie.objects.get(label=record.species_latin_name)

    except DictSpecie.DoesNotExist:
        logger.info("Search %s in synonyms" % (record.species_latin_name))
        # search for language synonym (if I arrived here a synonym should
        # exists)
        specie = DictSpecie.get_by_synonym(
            synonym=record.species_latin_name,
            language=language)

    # get country name using pycountries
    country_name = pycountry.countries.get(
        alpha_2=record.country_of_origin).name

    # get country for breeds. Ideally will be the same of submission,
    # however, it could be possible to store data from other contries
    country, created = DictCountry.objects.get_or_create(
        label=country_name)

    # I could create a country from a v_breed_specie instance. That's
    # ok, maybe I could have a lot of breed from different countries and
    # a few organizations submitting them
    if created:
        logger.info("Created %s" % country)

    else:
        logger.debug("Found %s" % country)

    breed, created = DictBreed.objects.get_or_create(
        supplied_breed=record.breed_name,
        specie=specie,
        country=country)

    if created:
        logger.info("Created %s" % breed)

    else:
        logger.debug("Found %s" % breed)

    # return a DictBreed object
    return breed


def fill_uid_names(record, submission):
    """fill Names table from crbanim record"""

    # in the same record I have the sample identifier and animal identifier
    # a name record for animal
    animal_name, created = Name.objects.get_or_create(
        name=record.animal_ID,
        submission=submission,
        owner=submission.owner)

    if created:
        logger.info("Created animal name %s" % animal_name)

    else:
        logger.debug("Found animal name %s" % animal_name)

    # get a publication (if present)
    publication = None

    # HINT: mind this mispelling
    if record.sample_bibliographic_references:
        publication, created = Publication.objects.get_or_create(
            doi=record.sample_bibliographic_references)

        if created:
            logger.info("Created publication %s" % publication)

    # name record for sample
    sample_name, created = Name.objects.get_or_create(
        name=record.sample_identifier,
        submission=submission,
        owner=submission.owner,
        publication=publication)

    if created:
        logger.info("Created sample name %s" % sample_name)

    else:
        logger.debug("Found sample name %s" % sample_name)

    # returning 2 Name instances
    return animal_name, sample_name


def fill_uid_animal(record, animal_name, breed, submission, animals):
    """Helper function to fill animal data in UID animal table"""

    # HINT: does CRBAnim models mother and father?

    # check if such animal is already beed updated
    if animal_name.name in animals:
        logger.debug(
            "Ignoring %s: already created or updated" % (animal_name))

        # return an animal object
        animal = animals[animal_name.name]

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
            'alternative_id': animal_name.name,
            'breed': breed,
            'sex': sex,
            'birth_date': record.animal_birth_date,
            'birth_location_accuracy': accuracy,
            'owner': submission.owner
        }

        # HINT: I could have the same animal again and again. Should I update
        # every times?
        animal, created = Animal.objects.update_or_create(
            name=animal_name,
            defaults=defaults)

        if created:
            logger.info("Created animal %s" % animal)

        else:
            logger.debug("Updating animal %s" % animal)

        # track this animal in dictionary
        animals[animal_name.name] = animal

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
        return mapping[record.sample_storage_temperature]

    else:
        logging.warning("Couldn' find %s in storage types mapping" % (
            record.sample_storage_temperature))

        return None


def fill_uid_sample(record, sample_name, animal, submission):
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
    organism_part, created = DictUberon.objects.get_or_create(
        label=organism_part_label
    )

    if created:
        logger.info("Created uberon %s" % organism_part)

    else:
        logger.debug("Found uberon %s" % organism_part)

    # calculate animal age at collection
    animal_birth_date = parse_date(record.animal_birth_date)
    sampling_date = parse_date(record.sampling_date)
    animal_age_at_collection, time_units = image_timedelta(
        sampling_date, animal_birth_date)

    # create a new object. Using defaults to avoid collisions when
    # updating data
    defaults = {
        # HINT: is a duplication of name. Can this be non-mandatory?
        'alternative_id': sample_name.name,
        'collection_date': record.sampling_date,
        'protocol': record.sampling_protocol_url,
        'organism_part': organism_part,
        'animal': animal,
        # 'description': v_vessel.comment,
        'owner': submission.owner,
        'storage': find_storage_type(record),
        'availability': record.sample_availability,
        'animal_age_at_collection': animal_age_at_collection,
        'animal_age_at_collection_units': time_units
    }

    sample, created = Sample.objects.update_or_create(
        name=sample_name,
        defaults=defaults)

    if created:
        logger.info("Created sample %s" % sample)

    else:
        logger.debug("Updating sample %s" % sample)

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

    # filling name tables
    animal_name, sample_name = fill_uid_names(record, submission)

    # fill animal
    animal = fill_uid_animal(record, animal_name, breed, submission, animals)

    # fill sample
    fill_uid_sample(record, sample_name, animal, submission)


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
        # check for species and sex in a similar way as cryoweb does
        check, not_found = reader.check_sex()

        if not check:
            message = (
                "Not all Sex terms are loaded into database: "
                "check for %s in your dataset" % (not_found))

            raise CRBAnimImportError(message)

        check, not_found = reader.check_species(submission.gene_bank_country)

        if not check:
            raise CRBAnimImportError(
                "Some species are not loaded in UID database: "
                "%s" % (not_found))

        # ok get languages from submission (useful for translation)
        # HINT: no traslations implemented, at the moment
        language = submission.gene_bank_country.label

        # a dictionary in which store animal data
        animals = {}

        for record in reader.data:
            process_record(record, submission, animals, language)

    except Exception as exc:
        # set message:
        message = "Error in importing data: %s" % (str(exc))

        # save a message in database
        submission.status = ERROR
        submission.message = message
        submission.save()

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

    logger.info("Import from CRBAnim is complete")

    return True
