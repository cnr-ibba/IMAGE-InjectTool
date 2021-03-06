#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  5 16:37:48 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from common.constants import (
    ERROR, LOADED, ACCURACIES, SAMPLE_STORAGE, SAMPLE_STORAGE_PROCESSING)
from common.helpers import image_timedelta, parse_image_timedelta
from uid.helpers import get_or_create_obj, update_or_create_obj
from uid.models import (
    DictBreed, DictCountry, DictSpecie, DictSex, DictUberon, Animal,
    Sample, DictDevelStage, DictPhysioStage)
from submissions.helpers import send_message
from validation.helpers import construct_validation_message
from validation.models import ValidationSummary

from .exceptions import ExcelImportError
from .exceltemplate import ExcelTemplateReader

# Get an instance of a logger
logger = logging.getLogger(__name__)


def fill_uid_breeds(submission_obj, template):
    """Fill DictBreed from a excel record"""

    logger.info("fill_uid_breeds() started")

    # ok get languages from submission (useful for translation)
    language = submission_obj.gene_bank_country.label

    # iterate among excel template
    for record in template.get_breed_records():
        # get a DictSpecie object. Species are in latin names, but I can
        # find also a common name in translation tables
        specie = DictSpecie.get_specie_check_synonyms(
            species_label=record.species,
            language=language)

        # get country for breeds. Ideally will be the same of submission,
        # however, it could be possible to store data from other contries
        country = DictCountry.objects.get(label=record.efabis_breed_country)

        get_or_create_obj(
            DictBreed,
            supplied_breed=record.supplied_breed,
            specie=specie,
            country=country)

    logger.info("fill_uid_breeds() completed")


def get_relationship(animal_id_in_data_source, name, breed, owner):
    try:
        parent = Animal.objects.get(
            name=name,
            breed=breed,
            owner=owner)

    except Animal.DoesNotExist as exc:
        logger.error(exc)
        message = (
            "Unknown parent '%s': check animal '%s' "
            "in your dataset" % (name, animal_id_in_data_source))
        logger.error(message)
        raise ExcelImportError(message)

    return parent


def fill_uid_animals(submission_obj, template):
    # debug
    logger.info("called fill_uid_animals()")

    # get language
    language = submission_obj.gene_bank_country.label

    # iterate among excel template
    for record in template.get_animal_records():
        # determine sex. Check for values
        sex = DictSex.objects.get(label__iexact=record.sex)

        # get specie (mind synonyms)
        specie = DictSpecie.get_specie_check_synonyms(
            species_label=record.species, language=language)

        logger.debug("Found '%s' as specie" % (specie))

        # how I can get breed from my data?
        breed_record = template.get_breed_from_animal(record)

        # get a country for this breed
        country = DictCountry.objects.get(
            label=breed_record.efabis_breed_country)

        # ok get a real dictbreed object
        breed = DictBreed.objects.get(
            supplied_breed=breed_record.supplied_breed,
            specie=specie,
            country=country)

        logger.debug("Selected breed is %s" % (breed))

        # define mother and father
        mother, father = None, None

        # get name for this animal and for mother and father
        if record.father_id_in_data_source:
            logger.debug("Getting %s as father" % (
                record.father_id_in_data_source))

            father = get_relationship(
                record.animal_id_in_data_source,
                record.father_id_in_data_source,
                breed,
                submission_obj.owner)

        if record.mother_id_in_data_source:
            logger.debug("Getting %s as mother" % (
                record.mother_id_in_data_source))

            mother = get_relationship(
                record.animal_id_in_data_source,
                record.mother_id_in_data_source,
                breed,
                submission_obj.owner)

        # now get accuracy
        accuracy = ACCURACIES.get_value_by_desc(
            record.birth_location_accuracy)

        # create a new object. Using defaults to avoid collisions when
        # updating data
        defaults = {
            'alternative_id': record.alternative_animal_id,
            'description': record.animal_description,
            'sex': sex,
            'father': father,
            'mother': mother,
            'birth_date': record.birth_date,
            'birth_location': record.birth_location,
            'birth_location_latitude': record.birth_location_latitude,
            'birth_location_longitude': record.birth_location_longitude,
            'birth_location_accuracy': accuracy,
        }

        # creating or updating an object
        update_or_create_obj(
            Animal,
            name=record.animal_id_in_data_source,
            breed=breed,
            owner=submission_obj.owner,
            submission=submission_obj,
            defaults=defaults)

    # create a validation summary object and set all_count
    validation_summary = get_or_create_obj(
        ValidationSummary,
        submission=submission_obj,
        type="animal")

    # reset counts
    validation_summary.reset_all_count()

    # debug
    logger.info("fill_uid_animals() completed")


def parse_times(record, animal):
    """Try to deal with times in excel templates"""

    animal_age_at_collection, time_units = None, None

    # animal age could be present or not
    if record.animal_age_at_collection:
        try:
            animal_age_at_collection, time_units = parse_image_timedelta(
                record.animal_age_at_collection)

        except ValueError as exc:
            message = (
                "Error for Sample '%s' at animal_age_at_collection "
                "column: %s" % (
                    record.sample_id_in_data_source, exc))
            logger.error(message)
            raise ExcelImportError(message)

    elif record.collection_date and animal.birth_date:
        # derive animal age at collection if I have recommended values
        animal_age_at_collection, time_units = image_timedelta(
            record.collection_date, animal.birth_date)

    # another time column
    preparation_interval, preparation_interval_units = None, None

    try:
        if record.sampling_to_preparation_interval:
            preparation_interval, preparation_interval_units = \
                parse_image_timedelta(record.sampling_to_preparation_interval)

    except ValueError as exc:
        message = (
            "Error for Sample '%s' at sampling_to_preparation_interval "
            "column: %s" % (
                record.sample_id_in_data_source, exc))
        logger.error(message)
        raise ExcelImportError(message)

    return (animal_age_at_collection, time_units, preparation_interval,
            preparation_interval_units)


def fill_uid_samples(submission_obj, template):
    # debug
    logger.info("called fill_uid_samples()")

    # get language
    language = submission_obj.gene_bank_country.label

    # iterate among excel template
    for record in template.get_sample_records():
        # get animal by reading record
        animal_record = template.get_animal_from_sample(record)

        # get specie (mind synonyms)
        specie = DictSpecie.get_specie_check_synonyms(
            species_label=animal_record.species,
            language=language)

        logger.debug("Found '%s' as specie" % (specie))

        # get breed from animal record
        breed_record = template.get_breed_from_animal(animal_record)

        # get a country for this breed
        country = DictCountry.objects.get(
            label=breed_record.efabis_breed_country)

        # ok get a real dictbreed object
        breed = DictBreed.objects.get(
            supplied_breed=breed_record.supplied_breed,
            specie=specie,
            country=country)

        logger.debug("Selected breed is %s" % (breed))

        animal = Animal.objects.get(
            name=animal_record.animal_id_in_data_source,
            breed=breed,
            owner=submission_obj.owner)

        logger.debug("Selected animal is %s" % (animal))

        # get a organism part. Organism parts need to be in lowercases
        organism_part = get_or_create_obj(
            DictUberon,
            label=record.organism_part
        )

        # get developmental_stage and physiological_stage terms
        # they are not mandatory
        devel_stage, physio_stage = None, None

        if record.developmental_stage:
            devel_stage = get_or_create_obj(
                DictDevelStage,
                label=record.developmental_stage
            )

        if record.physiological_stage:
            physio_stage = get_or_create_obj(
                DictPhysioStage,
                label=record.physiological_stage
            )

        # deal with time columns
        (animal_age_at_collection, time_units, preparation_interval,
         preparation_interval_units) = parse_times(record, animal)

        # now get accuracy
        accuracy = ACCURACIES.get_value_by_desc(
            record.collection_place_accuracy)

        # now get storage and storage processing
        # TODO; check those values in excel columns
        storage = SAMPLE_STORAGE.get_value_by_desc(
            record.sample_storage)

        storage_processing = SAMPLE_STORAGE_PROCESSING.get_value_by_desc(
            record.sample_storage_processing)

        # create a new object. Using defaults to avoid collisions when
        # updating data
        defaults = {
            'alternative_id': record.alternative_sample_id,
            'description': record.sample_description,
            'protocol': record.specimen_collection_protocol,
            'collection_date': record.collection_date,
            'collection_place_latitude': record.collection_place_latitude,
            'collection_place_longitude': record.collection_place_longitude,
            'collection_place': record.collection_place,
            'collection_place_accuracy': accuracy,
            'organism_part': organism_part,
            'developmental_stage': devel_stage,
            'physiological_stage': physio_stage,
            'animal_age_at_collection': animal_age_at_collection,
            'animal_age_at_collection_units': time_units,
            'availability': record.availability,
            'storage': storage,
            'storage_processing': storage_processing,
            'preparation_interval': preparation_interval,
            'preparation_interval_units': preparation_interval_units,
        }

        update_or_create_obj(
            Sample,
            name=record.sample_id_in_data_source,
            animal=animal,
            owner=submission_obj.owner,
            submission=submission_obj,
            defaults=defaults)

    # create a validation summary object and set all_count
    validation_summary = get_or_create_obj(
        ValidationSummary,
        submission=submission_obj,
        type="sample")

    # reset counts
    validation_summary.reset_all_count()

    # debug
    logger.info("fill_uid_samples() completed")


def check_UID(submission_obj, reader):
    # check for species and sex in a similar way as cryoweb does
    # TODO: identical to CRBanim. Move to a mixin
    check, not_found = reader.check_sex()

    # check sex
    if not check:
        message = (
            "Not all Sex terms are loaded into database: "
            "check for '%s' in your dataset" % (not_found))

        raise ExcelImportError(message)

    check, not_found = reader.check_species(
        submission_obj.gene_bank_country)

    # check species and related
    if not check:
        raise ExcelImportError(
            "Some species are not loaded into database: "
            "check for '%s' in your dataset" % (not_found))

    check, not_found = reader.check_species_in_animal_sheet()

    if not check:
        raise ExcelImportError(
            "Some species are not defined in breed sheet: "
            "check for '%s' in your dataset" % (not_found))

    # check countries
    check, not_found = reader.check_countries()

    if not check:
        raise ExcelImportError(
            "Those countries are not loaded in database: "
            "check for '%s' in your dataset" % (not_found))

    # check accuracies
    check, not_found = reader.check_accuracies()

    if not check:
        message = (
            "Not all accuracy levels are defined in database: "
            "check for '%s' in your dataset" % (not_found))

        raise ExcelImportError(message)


def upload_template(submission_obj):
    # debug
    logger.info("Importing from Excel template file")

    # this is the full path in docker container
    fullpath = submission_obj.get_uploaded_file_path()

    # read submission data
    reader = ExcelTemplateReader()
    reader.read_file(fullpath)

    # start data loading
    try:
        # check UID data like cryoweb does
        check_UID(submission_obj, reader)

        # BREEDS
        fill_uid_breeds(submission_obj, reader)

        # ANIMALS
        fill_uid_animals(submission_obj, reader)

        # SAMPLES
        fill_uid_samples(submission_obj, reader)

    except Exception as exc:
        # set message:
        message = "Error in importing data: %s" % (str(exc))

        # save a message in database
        submission_obj.status = ERROR
        submission_obj.message = message
        submission_obj.save()

        # send async message
        send_message(submission_obj)

        # debug
        logger.error("Error in importing from Template: %s" % (exc))
        logger.exception(exc)

        return False

    else:
        message = "Template import completed for submission: %s" % (
            submission_obj.id)

        submission_obj.message = message
        submission_obj.status = LOADED
        submission_obj.save()

        # send async message
        send_message(
            submission_obj,
            validation_message=construct_validation_message(submission_obj))

    logger.info("Import from Template is complete")

    return True
