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

from common.constants import LOADED, ERROR, MISSING
from image_app.models import (
    DictSpecie, DictSex, DictCountry, DictBreed, Name, Animal, Sample,
    DictUberon)

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

    def read_file(self, filename):
        """Read crb anim files and set tit to class attribute"""

        with open(filename, newline='') as csvfile:
            # initialize data
            self.data = []
            self.dialect = csv.Sniffer().sniff(csvfile.read(2048))
            csvfile.seek(0)

            # read csv file
            reader = csv.reader(csvfile, self.dialect)
            self.header = next(reader)

            # create a namedtuple object
            Data = namedtuple("Data", self.header)

            # add records to data
            for record in reader:
                # replace all "\\N" occurences in a list
                record = [None if col in ["\\N", ""]
                          else col for col in record]
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
            logger.error(
                "Those %s are not present in UID database:" % (column))
            logger.error(not_found)

        return result, not_found

    # a function to detect if crbanim species are in UID database or not
    # HINT: crbanim species are already in the form required from DictSpecies
    # tables, no need to search for language
    def check_species(self):
        """Check if all species are defined in UID DictSpecies"""

        column = 'species_latin_name'

        return self.__check_items(self.items[column], DictSpecie, column)

    # check that dict sex table contains data
    def check_sex(self):
        """check that dict sex table contains data"""

        # item.sex are in uppercase
        column = 'sex'
        item_set = [item.lower() for item in self.items[column]]

        return self.__check_items(item_set, DictSex, column)


def fill_uid_breed(record):
    """Fill DioctBreed from a crbanim record"""

    # get a DictSpecie object. Species are in latin names, so I don't need
    # a translation
    specie = DictSpecie.objects.get(label=record.species_latin_name)

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

    # name record for sample
    sample_name, created = Name.objects.get_or_create(
        name=record.sample_identifier,
        submission=submission,
        owner=submission.owner)

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
            'alternative_id': record.EBI_Biosample_identifier,
            'breed': breed,
            'sex': sex,
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


def fill_uid_sample(record, sample_name, animal, submission):
    """Helper function to fill animal data in UID sample table"""

    # name and animal name come from parameters

    # get a organism part. Organism parts need to be in lowercases
    # waht sample_type_name stands for?
    organism_part, created = DictUberon.objects.get_or_create(
        label=record.body_part_name.lower()
    )

    if created:
        logger.info("Created uberon %s" % organism_part)

    else:
        logger.debug("Found uberon %s" % organism_part)

    # create a new object. Using defaults to avoid collisions when
    # updating data
    defaults = {
        # can't be EBI_Biosample_identifier
        # 'alternative_id': v_vessel.db_vessel,
        'collection_date': record.sampling_date,
        'protocol': record.sampling_protocol_url,
        'organism_part': organism_part,
        'animal': animal,
        # 'description': v_vessel.comment,
        'owner': submission.owner,
        'storage': " ".join([
            record.sample_container_type, record.sample_storage_temperature])
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
    breed = fill_uid_breed(record)

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

        check, not_found = reader.check_species()

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
