#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 14 10:28:39 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

# --- import

import os
import shlex
import logging
import subprocess
import pandas as pd

from decouple import AutoConfig

from django.conf import settings

from image_app.helpers import CryowebDB
from image_app.models import (
    Submission, DictSex, Name, DictCountry, DictSpecie, DictBreed, Animal,
    Sample)
from language.models import SpecieSynonim

from .models import (
    VBreedsSpecies, db_has_data as cryoweb_has_data, VTransfer, VAnimal,
    VVessels)

# Get an instance of a logger
logger = logging.getLogger(__name__)


# --- check functions
# a function to detect if cryoweb species have synonims or not
def check_species(language):
    """Check specie for a language, ie: check_species(language='Germany').
    Language is image_app.models.DictCountry.label"""

    # get all species using view
    species = VBreedsSpecies.get_all_species()

    # for logging purposes
    database_name = settings.DATABASES['cryoweb']['NAME']

    # debug
    logger.debug("Got %s species from %s" % (species, database_name))

    # get a queryset for each
    synonims = SpecieSynonim.objects.filter(
        word__in=species, language__label=language)

    # HINT: is this state useful?
    # check that numbers are equal
    if len(species) == synonims.count():
        logger.debug("Each species has a synonim in %s language" % (language))
        return True

    elif len(species) > synonims.count():
        logger.warning(
            "Some species haven't a synonim for language: %s!" % (language))
        logger.debug("Following terms lack of synonim:")
        for specie in species:
            if not SpecieSynonim.objects.filter(
                    word=specie, language__label=language).exists():
                logger.debug(specie)
        return False

    # may I see this case? For instance when filling synonims?
    else:
        raise NotImplementedError("Not implemented")


# a function specific for cryoweb import path to ensure that all required
# fields in UID are present. There could be a function like this in others
# import paths
def check_UID(submission):
    """A function to ensure that UID is valid before data upload. Specific
    to the module where is called from"""

    logger.debug("Checking UID")

    # check that dict sex table contains data
    if len(DictSex.objects.all()) == 0:
        raise CryoWebImportError("You have to upload DictSex data")

    # HINT: if I don't have a synonim, what I need to do?
    if not check_species(submission.gene_bank_country.label):
        raise CryoWebImportError("Some species haven't a synonim!")

    # TODO: deal with exceptions
    # TODO: return a status


# A class to deal with cryoweb import errors
class CryoWebImportError(Exception):
    pass


# --- Upload data into cryoweb database
def upload_cryoweb(submission_id):
    """Imports backup into the cryoweb db

    This function uses the container's installation of psql to import a backup
    file into the "cryoweb" database. The imported backup file is
    the last inserted into the image's table image_app_submission.

    :submission_id: the submission primary key
    """

    # define some useful variables
    database_name = settings.DATABASES['cryoweb']['NAME']

    # define a decouple config object
    config_dir = os.path.join(settings.BASE_DIR, 'image')
    config = AutoConfig(search_path=config_dir)

    # get a submission object
    submission = Submission.objects.get(pk=submission_id)

    # debug
    logger.info("Importing data into cryoweb staging area")
    logger.debug("Got Submission %s" % (submission))

    # If cryoweb has data, update submission message and return exception:
    # maybe another process is running or there is another type of problem
    if cryoweb_has_data():
        logger.error("Cryoweb has data!")

        # update submission status
        submission.status = Submission.STATUSES.get_value('error')
        submission.message = "Cryoweb has data"
        submission.save()

        raise CryoWebImportError("Cryoweb has data!")

    # this is the full path in docker container
    fullpath = submission.uploaded_file.file

    # get a string and quote fullpath
    fullpath = shlex.quote(str(fullpath))

    # define command line
    cmd_line = "/usr/bin/psql -U {user} -h db {database}".format(
        database=database_name, user='cryoweb_insert_only')

    cmds = shlex.split(cmd_line)

    logger.debug("Executing: %s" % " ".join(cmds))

    try:
        result = subprocess.run(
            cmds,
            stdin=open(fullpath),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            env={'PGPASSWORD': config('CRYOWEB_INSERT_ONLY_PW')},
            encoding='utf8'
            )

    except Exception as exc:
        # save a message in database
        submission.status = Submission.STATUSES.get_value('error')
        submission.message = str(exc)
        submission.save()

        # debug
        logger.error("error in calling upload_cryoweb: %s" % (exc))

        return False

    n_of_statements = len(result.stdout.split("\n"))
    logger.debug("%s statement executed" % n_of_statements)

    for line in result.stderr.split("\n"):
        logger.error(line)

    logger.info("{filename} uploaded into {database}".format(
        filename=submission.uploaded_file.name, database=database_name))

    return True


# --- Upload data into UID database
def add_warnings(context, section, msg):
    """Helper function for import_from_cryoweb and its functions"""

    if context["has_warnings"] is False:
        context["has_warnings"] = True

    if section in context['warnings']:
        context['warnings'][section] += [msg]

    else:
        context['warnings'][section] = [msg]


def fill_species(df_breeds_species, context, submission):
    """Return a list of DictSpecie.id. Fill DictSpecies if necessary"""

    # debug
    logger.info("called fill_species()")

    # get all species
    species_set = set(df_breeds_species["ext_species"])

    # get submission language
    language = submission.gene_bank_country.label

    # now a dictionary for label to ids
    species_dict = dict()

    # cicle over specie
    for synonim in species_set:
        specie_obj = DictSpecie.get_by_synonim(
            synonim,
            language)

        # get pk (or id)
        species_dict[synonim] = specie_obj.id

    # debug
    logger.info("Found %s species" % (len(species_set)))
    context['loaded']['specie'] = len(species_set)

    logger.info("fill_species() completed")
    logger.debug("returning: %s" % (species_dict))

    # now I have a dictionary of species to id, map columns to values
    return list(df_breeds_species.ext_species.map(species_dict))


def fill_countries(df_breeds_species, context):
    """Return a list of DictCountry.id. Fill DictCountry if necessary"""

    # get all countries
    countries_set = set(df_breeds_species["efabis_country"])

    # now a dictionary for label to ids
    countries_dict = dict()
    counter = 0

    # cicle over specie
    for country in countries_set:
        country_obj, created = DictCountry.objects.get_or_create(
                label=country)

        # get pk (or id)
        countries_dict[country] = country_obj.id

        if created:
            counter += 1

    # debug
    if counter > 0:
        logger.info("Added %s countries" % (counter))
        context['loaded']['countries'] = counter

    # now I have a dictionary of species to id, map columns to values
    return list(df_breeds_species.efabis_country.map(countries_dict))


def fill_uid_breeds(submission):
    """Fill UID DictBreed model. Require a submission instance"""

    logger.debug("fill_uid_breeds() started")

    # get submission language
    language = submission.gene_bank_country.label

    for v_breed_specie in VBreedsSpecies.objects.all():
        # get specie. Since I need a dictionary tables, DictSpecie is
        # already filled
        specie = DictSpecie.get_by_synonim(
            synonim=v_breed_specie.ext_species,
            language=language)

        # get country. Maybe DictCountry will be related to dictionary table
        # for now, I can create an object or not
        # TODO: define if is a dictionary related term or not
        # use language for consistency with submission
        country, created = DictCountry.objects.get_or_create(
            label=language)

        if created:
            logger.info("Created %s" % country)

        else:
            logger.debug("Found %s" % country)

        breed, created = DictBreed.objects.get_or_create(
            supplied_breed=v_breed_specie.efabis_mcname,
            specie=specie,
            country=country)

        if created:
            logger.info("Created %s" % breed)

        else:
            logger.debug("Found %s" % breed)

    logger.debug("fill_uid_breeds() completed")


def fill_breeds(engine_from_cryoweb, context, submission):
    """Helper function to upload breeds data in image database"""

    # debug
    logger.info("called fill_breeds()")

    # read the the v_breeds_species view in the "cryoweb
    # database"
    df_breeds_species = pd.read_sql_table(
            'v_breeds_species',
            con=engine_from_cryoweb,
            schema="apiis_admin")

    logger.debug("Read %s records from v_breeds_species" % (
            df_breeds_species.shape[0]))

    species_ids = fill_species(df_breeds_species, context, submission)
    countries_ids = fill_countries(df_breeds_species, context)

    # keep only interesting columns and rename them
    df_breeds_fin = df_breeds_species[
        ['db_breed',
         'efabis_mcname',
         'ext_species',
         'efabis_country']]

    # set index to dataframe. Index will be internal cryoweb id
    df_breeds_fin.index = df_breeds_fin["db_breed"]

    # remove db_breed column
    del(df_breeds_fin["db_breed"])

    df_breeds_fin = df_breeds_fin.rename(
        columns={
            'efabis_mcname': 'supplied_breed',
            'ext_species': 'species',
            'efabis_country': 'country',
        }
    )

    # add species and countries
    df_breeds_fin["specie_id"] = species_ids
    df_breeds_fin["country_id"] = countries_ids

    # if we don't truncate any data, I can't put all breeds as they
    # are in database, but I need to check and add only new breeds

    # A dictionary of object to create
    to_create = {}

    # get list of breeds present in database
    queryset = DictBreed.objects.filter()

    # BUG: need to be supplied_breed, species as a key
    in_table_breeds = [breed.supplied_breed for breed in queryset]

    # debug
    logger.debug("read %s breeds" % (queryset.count()))

    # insert dataframe as table into the UID database
    for row in df_breeds_fin.itertuples():
        # skip duplicates (in the same bulk insert)
        # BUG: need to be supplied_breed, species as a key
        if row.supplied_breed in to_create:
            logger.warning("%s: already marked for insertion (%s)" % (
                    str(row), str(to_create[row.supplied_breed])))

            msg = "Duplicated record %s" % (str(row))

            # add warning to context
            add_warnings(context, 'breed', msg)

        # get or create objects: check for existance if not create an
        # object for a bulk_insert
        # BUG: need to be supplied_breed, species as a key
        elif row.supplied_breed in in_table_breeds:
            msg = "%s: already present in database" % (str(row))
            logger.warning(msg)

            # add warning to context
            # HINT: is this a warning?
            add_warnings(context, 'breed', msg)

        else:
            # create a new object
            obj = DictBreed(
                    supplied_breed=row.supplied_breed,
                    specie_id=row.specie_id,
                    country_id=row.country_id)

            # append object to to_create list
            # BUG: need to be supplied_breed, species as a key
            to_create[row.supplied_breed] = obj

    # Now eval to_create list; if necessary, bulk_insert
    if len(to_create) > 0:
        DictBreed.objects.bulk_create(to_create.values(), batch_size=100)

    logger.debug("%s breeds added to database" % (len(to_create)))
    context['loaded']['breed'] = len(to_create)
    logger.info("fill_breeds() completed")

    # return processed dataframe
    return df_breeds_fin


def fill_uid_names(submission):
    """Read VTransfer Views and fill name table"""

    # debug
    logger.info("called fill_uid_names()")

    # get all Vtransfer object
    for v_tranfer in VTransfer.objects.all():
        # no name manipulation. If two objects are indentical, there's no
        # duplicates.
        # HINT: The ramon example will be a issue in validation step
        name, created = Name.objects.get_or_create(
            name=v_tranfer.get_fullname(),
            submission=submission,
            owner=submission.owner)

        if created:
            logger.info("Created %s" % name)

        else:
            logger.debug("Found %s" % name)

    logger.info("fill_uid_names() completed")


def fill_names(dataframe, submission, context):
    """A generic function to fill Name table starting from a dataframe and
    submission"""

    # debug
    logger.info("called fill_names()")

    # A dictionary of object to create
    to_create = {}

    # get list of names of already inserted animals
    queryset = Name.objects.filter(submission=submission)
    in_table_names = [name.name for name in queryset]

    # debug
    logger.debug("read %s names" % (queryset.count()))

    # insert dataframe as table into the UID database
    for row in dataframe.itertuples():
        # skip duplicates (in the same bulk insert)
        if row.name in to_create:
            logger.warning("%s: already marked for insertion (%s)" % (
                    str(row), str(to_create[row.name])))

            msg = "Duplicated record %s" % (str(row))

            # add warning to context
            add_warnings(context, 'name', msg)

        # get or create objects: check for existance if not create an
        # object for a bulk_insert
        elif row.name in in_table_names:
            msg = "%s: already present in database" % (str(row))
            logger.warning(msg)

            # add warning to context
            add_warnings(context, 'name', msg)

        else:
            # create a new object
            obj = Name(name=row.name,
                       submission=submission,
                       owner=submission.owner)

            # append object to to_create list
            to_create[row.name] = obj

    # Now eval to_create list; if necessary, bulk_insert
    if len(to_create) > 0:
        Name.objects.bulk_create(to_create.values(), batch_size=100)

    logger.debug("%s names added to database" % (len(to_create)))

    # update context
    if 'name' in context['loaded']:
        context['loaded']['name'] += len(to_create)

    else:
        context['loaded']['name'] = len(to_create)

    logger.info("fill_names() finished")


def fill_transfer(engine_from_cryoweb, submission, context):
    """Helper function to fill transfer data into image name table"""

    # debug
    logger.info("called fill_transfer()")

    # in order to use relational constraints in animal relations (
    # mother, father) we need to 'register' an animal name into the
    # database
    df_transfer = pd.read_sql_table(
            'v_transfer',
            con=engine_from_cryoweb,
            schema="apiis_admin")

    logger.debug("Read %s records from v_transfer" % (
            df_transfer.shape[0]))

    # now derive animal names from columns
    df_transfer['name'] = (
            df_transfer['ext_unit'] + ':::' +
            df_transfer['ext_animal'])

    # subset of columns: copy the dataframe as suggested at
    # https://stackoverflow.com/a/43358763 in order to resolve
    # https://www.dataquest.io/blog/settingwithcopywarning/
    df_transfer_fin = df_transfer.copy()[['db_animal', 'name']]

    logger.debug("Removing spaces from names")

    # remove empty spaces
    df_transfer_fin['name'] = df_transfer_fin['name'].str.replace(
            ' +', '_')

    # set index to dataframe
    df_transfer_fin.index = df_transfer_fin["db_animal"]

    # remove column from dataframe
    del(df_transfer_fin["db_animal"])

    # call a function to fill name table
    fill_names(df_transfer_fin, submission, context)

    # debug
    logger.info("fill_transfer() finished")

    # return processed objects
    return df_transfer_fin


# define a function to get the row from a dictionary of
# {(species, description: dictbreed.id} starting from dataframe
def getDictBreedId(row, df_breeds_fin, breed_to_id, submission):
    """Returns DictBreed.id from a row from df_animals and df_breed"""

    # get db_breed index from row
    db_breed = row.db_breed

    # get data from df_breeds_fin using dataframr indexes
    data = df_breeds_fin.loc[db_breed].to_dict()

    # get submission language
    language = submission.gene_bank_country.label

    # convert cryoweb specie into UID specie
    specie = DictSpecie.get_by_synonim(
            synonim=data['species'],
            language=language)

    # ok get dictbreed.id from dictionary
    key = (data['supplied_breed'], specie.label)
    return breed_to_id[key]


def getNameId(row, df_transfer_fin, tag, name_to_id):
    """Returns Name.id from df_animal, df_transfer and a tag like
    father_id, mother_id and animal_id"""

    if tag not in ["db_animal", "db_sire", "db_dam"]:
        raise Exception("Unknown tag: %s" % (tag))

    # get index from tag name (now is a row index)
    index = getattr(row, tag)

    # get data for index (using supplied submission)
    data = df_transfer_fin.loc[index].to_dict()

    # get name.id from dictionary
    return name_to_id[data["name"]]


def fill_uid_animals(submission):
    """Helper function to fill animal data in UID animal table"""

    # debug
    logger.info("called fill_uid_animals()")

    # get submission language
    language = submission.gene_bank_country.label

    # get male and female DictSex objects from database
    male = DictSex.objects.get(label="male")
    female = DictSex.objects.get(label="female")

    # cycle over animals
    for v_animal in VAnimal.objects.all():
        # get specie translated by dictionary
        specie = DictSpecie.get_by_synonim(
            synonim=v_animal.ext_species,
            language=language)

        # get breed name through VBreedsSpecies model
        efabis_mcname = v_animal.efabis_mcname()
        breed = DictBreed.objects.get(
            supplied_breed=efabis_mcname,
            specie=specie)

        # get name for this animal and for mother and father
        name = Name.objects.get(
            name=v_animal.ext_animal, submission=submission)

        father = Name.objects.get(
            name=v_animal.ext_sire, submission=submission)

        mother = Name.objects.get(
            name=v_animal.ext_dam, submission=submission)

        # determine sex. Check for values
        if v_animal.ext_sex == 'm':
            sex = male

        elif v_animal.ext_sex == 'f':
            sex = female

        else:
            raise CryoWebImportError(
                "Unknown sex '%s' for '%s'" % (v_animal.ext_sex, v_animal))

        # create a new object
        animal, created = Animal.objects.get_or_create(
            name=name,
            alternative_id=v_animal.db_animal,
            breed=breed,
            sex=sex,
            father=father,
            mother=mother,
            birth_location_latitude=v_animal.latitude,
            birth_location_longitude=v_animal.longitude,
            description=v_animal.comment,
            owner=submission.owner)

        if created:
            logger.info("Created %s" % animal)

        else:
            logger.debug("Found %s" % animal)

    # debug
    logger.info("fill_uid_animals() completed")


def fill_animals(engine_from_cryoweb, df_breeds_fin, df_transfer_fin,
                 submission, context):
    """Helper function to fill animal data in image animal table"""

    # debug
    logger.info("called fill_animals()")

    # read the v_animal view in the "cryoweb" db
    df_animals = pd.read_sql_table(
            'v_animal',
            con=engine_from_cryoweb,
            schema="apiis_admin")

    logger.debug("Read %s records from v_animal" % (
            df_animals.shape[0]))

    # now get breeds and their ids from database
    breed_to_id = {}

    # map breed name and species to its id
    for dictbreed in DictBreed.objects.all():
        breed_to_id[
            (dictbreed.supplied_breed, dictbreed.specie.label)] = dictbreed.id

    logger.debug("read %s breeds" % (DictBreed.objects.count()))

    # assign the breed_id column as DictBreed.id (will fill the)
    # breed id foreign key in animals table
    df_animals['breed_id'] = df_animals.apply(
            lambda row: getDictBreedId(
                    row,
                    df_breeds_fin,
                    breed_to_id,
                    submission),
            axis=1)

    # get name to id relation
    name_to_id = {}

    # get all names for this submission
    for name in Name.objects.filter(submission=submission):
        name_to_id[name.name] = name.id

    logger.debug("read %s names" % (
            Name.objects.filter(submission=submission).count()))

    # get internal keys from name
    df_animals['name_id'] = df_animals.apply(
            lambda row: getNameId(
                    row,
                    df_transfer_fin,
                    "db_animal",
                    name_to_id),
            axis=1)

    # get internal keys from mother and father
    df_animals["db_sire"] = df_animals.apply(
            lambda row: getNameId(
                    row,
                    df_transfer_fin,
                    "db_sire",
                    name_to_id),
            axis=1)

    df_animals["db_dam"] = df_animals.apply(
            lambda row: getNameId(
                    row,
                    df_transfer_fin,
                    "db_dam",
                    name_to_id),
            axis=1)

    # keep only interesting columns and rename them
    df_animals_fin = df_animals[
        ['name_id',
         'db_animal',
         'breed_id',
         'ext_sex',
         'db_sire',
         'db_dam',
         'latitude',
         'longitude',
         'comment']]

    df_animals_fin = df_animals_fin.rename(
        columns={
            'db_animal': 'alternative_id',
            'ext_sex': 'sex_id',
            'db_sire': 'father_id',
            'db_dam': 'mother_id',
            'latitude': 'birth_location_latitude',
            'longitude': 'birth_location_longitude',
            'comment': 'description'
        }
    )

    # get male and female DictSex objects fomr database
    male = DictSex.objects.get(label="male")
    female = DictSex.objects.get(label="female")

    # HINT: here we can translate sex value in male.id or female.id
    df_animals_fin['sex_id'] = df_animals_fin['sex_id'].replace(
            {'m': male.id, 'f': female.id})

    # A dictionary of object to create
    to_create = {}

    # insert animal in database
    # HINT: ANIMAL:::ID:::Ramon_142436 is present two times in database
    # with this, the second entry will not be inserted into Animal table
    # Same way of fill_transfer
    queryset = Animal.objects.filter(name__submission=submission)
    in_table_name_ids = [animal.name_id for animal in queryset]

    logger.debug("read %s animals" % (queryset.count()))

    for row in df_animals_fin.itertuples():
        # skip duplicates (in the same bulk insert)
        if row.name_id in to_create:
            logger.warning("%s: already marked for insertion (%s)" % (
                    str(row), str(to_create[row.name_id])))

            msg = "Duplicated record %s" % (str(row))

            # add warning to context
            add_warnings(context, 'animal', msg)

        # get or create objects: check for existance if not create an
        # object for a bulk_insert
        elif row.name_id in in_table_name_ids:
            msg = "%s: already present in database" % (str(row))
            logger.warning(msg)

            # add warning to context
            add_warnings(context, 'animal', msg)

        else:
            # create a new object
            obj = Animal(
                name_id=row.name_id,
                alternative_id=row.alternative_id,
                breed_id=row.breed_id,
                sex_id=row.sex_id,
                father_id=row.father_id,
                mother_id=row.mother_id,
                birth_location_latitude=row.birth_location_latitude,
                birth_location_longitude=row.birth_location_longitude,
                description=row.description,
                owner=submission.owner)

            # append object to to_create list
            to_create[row.name_id] = obj

    # Now eval to_create list; if necessary, bulk_insert
    if len(to_create) > 0:
        Animal.objects.bulk_create(to_create.values(), batch_size=100)

    # debug
    logger.debug("%s animals added to database" % (len(to_create)))
    context['loaded']['animal'] = len(to_create)
    logger.info("fill_animals() finished")

    # return animal data frame
    return df_animals_fin


def get_protocols(engine_from_cryoweb):
    """helper function to deal with v_protocol table"""

    # debug
    logger.info("called get_protocols()")

    # read view in "cryoweb" db
    df_protocols = pd.read_sql_table(
            'v_protocols',
            con=engine_from_cryoweb,
            schema="apiis_admin")

    # keep only interesting columns and rename them
    df_protocols_fin = df_protocols[
        ['protocol_id',
         'protocol_name',
         'ext_material_type',
         'comment']]

    df_protocols_fin = df_protocols_fin.rename(
        columns={
            'protocol_name': 'name',
            'ext_material_type': 'organism_part',
            'comment': 'description'
        }
    )

    # add index
    df_protocols_fin.index = df_protocols_fin['protocol_id']
    del(df_protocols_fin['protocol_id'])

    # debug
    logger.debug("%s protocols read" % (df_protocols_fin.shape[0]))
    logger.info("get_protocols() finished")

    # return dataframe
    return df_protocols_fin


def fill_uid_samples(submission):
    """Helper function to fill animal data in UID animal table"""

    # debug
    logger.info("called fill_uid_samples()")

    for v_vessel in VVessels.objects.all():
        # get name for this sample. Need to insert it
        name, created = Name.objects.get_or_create(
            name=v_vessel.ext_vessel,
            submission=submission,
            owner=submission.owner)

        if created:
            logger.info("Created %s" % name)

        else:
            logger.debug("Found %s" % name)

        # get animal object using name
        animal = Animal.objects.get(
            name__name=v_vessel.ext_animal,
            name__submission=submission)

        sample, created = Sample.objects.get_or_create(
            name=name,
            alternative_id=v_vessel.db_vessel,
            collection_date=v_vessel.production_dt,
            protocol=v_vessel.get_protocol_name(),
            organism_part=v_vessel.get_organism_part(),
            animal=animal,
            description=v_vessel.comment,
            owner=submission.owner)

        if created:
            logger.info("Created %s" % sample)

        else:
            logger.debug("Found %s" % sample)

    # debug
    logger.info("fill_uid_samples() completed")


def fill_samples(engine_from_cryoweb, df_transfer_fin, submission, context):
    """Helper function to fill image samples table"""

    # debug
    logger.info("called fill_samples()")

    # read view in "cryoweb" db
    df_samples = pd.read_sql_table(
            'v_vessels',
            con=engine_from_cryoweb,
            schema="apiis_admin")

    logger.debug("Read %s records from v_vessels" % (
            df_samples.shape[0]))

    # get name to id relation
    name_to_id = {}

    # get all names for this submission
    for name in Name.objects.filter(submission=submission):
        name_to_id[name.name] = name.id

    logger.debug("read %s names" % (
            Name.objects.filter(submission=submission).count()))

    # get name_id from name table, using db_animal from df_transfer_fin
    df_samples['name_id'] = df_samples.apply(
            lambda row: getNameId(
                    row,
                    df_transfer_fin,
                    "db_animal",
                    name_to_id),
            axis=1)

    # get animal to id relation
    animal_to_id = {}

    queryset = Animal.objects.select_related('name').filter(
            name__submission=submission)

    # get all names for this submission
    for animal in queryset:
        animal_to_id[animal.name_id] = animal.id

    logger.debug("read %s animals" % (queryset.count()))

    # now get the corresponding animal_id using animal names
    df_samples['animal_id'] = df_samples.apply(
            lambda row: animal_to_id[row['name_id']],
            axis=1)

    # ext_protocol_id need to be resolved in protocol name
    df_protocols = get_protocols(engine_from_cryoweb)

    # helper function to get protocol name
    def getProtocolName(row, df_protocols):
        index = row['ext_protocol_id']
        return df_protocols.loc[index]['name']

    def getPartName(row, df_protocols):
        index = row['ext_protocol_id']
        return df_protocols.loc[index]['organism_part']

    df_samples['protocol'] = df_samples.apply(
            lambda row: getProtocolName(row, df_protocols),
            axis=1)

    df_samples['organism_part'] = df_samples.apply(
            lambda row: getPartName(row, df_protocols),
            axis=1)

    # keep only interesting columns and rename them
    df_samples_fin = df_samples[
        ['db_vessel',
         'ext_vessel',
         'production_dt',
         'protocol',
         'organism_part',
         'animal_id',
         'comment']]

    # add index
    df_samples_fin.index = df_samples_fin['db_vessel']

    df_samples_fin = df_samples_fin.rename(
        columns={
            'ext_vessel': 'name',
            'db_vessel': 'alternative_id',
            'production_dt': 'collection_date',
            'comment': 'description'
        }
    )

    # change some data values: replace spaces in names and notes
    df_samples_fin['name'] = df_samples_fin['name'].str.replace(
            ' +', '_')

    # call a function to fill name table
    fill_names(df_samples_fin, submission, context)

    # get name to id relation
    name_to_id = {}

    # get all names for this submission
    for name in Name.objects.filter(submission=submission):
        name_to_id[name.name] = name.id

    logger.debug("read %s names" % (
            Name.objects.filter(submission=submission).count()))

    df_samples_fin["name_id"] = df_samples_fin.apply(
            lambda row: name_to_id[row['name']],
            axis=1)

    # drop colunm name (cause now I have an ID)
    del(df_samples_fin["name"])

    # A dictionary of object to create
    to_create = {}

    # get list of breeds present in database
    queryset = Sample.objects.filter(name__submission=submission)
    in_table_name_ids = [sample.name_id for sample in queryset]

    # debug
    logger.debug("read %s samples" % (queryset.count()))

    # beware NaT
    def sanitizeTime(value):
        if value is pd.NaT:
            return None

        return value

    for row in df_samples_fin.itertuples():
        # skip duplicates (in the same bulk insert)
        if row.name_id in to_create:
            logger.warning("%s: already marked for insertion (%s)" % (
                    str(row), str(to_create[row.name_id])))

            msg = "Duplicated record %s" % (str(row))

            # add warning to context
            add_warnings(context, 'sample', msg)

        # get or create objects: check for existance if not create an
        # object for a bulk_insert
        elif row.name_id in in_table_name_ids:
            msg = "%s: already present in database" % (str(row))
            logger.warning(msg)

            # add warning to context
            add_warnings(context, 'sample', msg)

        else:
            # create a new object
            obj = Sample(
                name_id=row.name_id,
                alternative_id=row.alternative_id,
                collection_date=sanitizeTime(row.collection_date),
                protocol=row.protocol,
                organism_part=row.organism_part,
                animal_id=row.animal_id,
                description=row.description,
                owner=submission.owner)

            # append object to to_create list
            to_create[row.name_id] = obj

    # Now eval to_create list; if necessary, bulk_insert
    if len(to_create) > 0:
        Sample.objects.bulk_create(to_create.values(), batch_size=100)

    # debug
    logger.debug("%s samples added to database" % (len(to_create)))
    context['loaded']['sample'] = len(to_create)
    logger.info("fill_samples() finished")

    # return processed object
    return df_samples_fin


def cryoweb_import(submission):
    """Import data from cryoweb stage database into UID

    :submission: a submission instance
    """

    # debug
    logger.info("Importing from cryoweb staging area")

    # TODO: update those functions and avoid pandas
    # a Fake object in order to use old cryoweb functions
    context = {
        'username': None,
        'user': None,
        'loaded': {},
        'warnings': {},
        'has_warnings': False}

    # TODO: other stuff to remove
    # define helper database objects
    cryowebdb = CryowebDB(database=settings.DATABASES['cryoweb']['NAME'])

    # set those values using a function from helper objects
    engine_from_cryoweb = cryowebdb.get_engine()

    try:
        # BREEDS
        fill_uid_breeds(submission)

        # TODO: remove this function
        df_breeds_fin = fill_breeds(
            engine_from_cryoweb,
            context,
            submission)

        # NAME
        fill_uid_names(submission)

        # TODO: remove this function
        df_transfer_fin = fill_transfer(
            engine_from_cryoweb,
            submission,
            context)

        # ANIMALS
        fill_uid_animals(submission)

        # TODO: remove this function
        fill_animals(
            engine_from_cryoweb,
            df_breeds_fin,
            df_transfer_fin,
            submission,
            context)

        # SAMPLES
        fill_uid_samples(submission)

        # TODO: remove this function
        fill_samples(
            engine_from_cryoweb,
            df_transfer_fin,
            submission,
            context)

    except Exception as exc:
        # save a message in database
        submission.status = Submission.STATUSES.get_value('error')
        submission.message = str(exc)
        submission.save()

        # debug
        logger.error("error in importing from cryoweb: %s" % (exc))

        return False

    logger.info("Import from staging area is complete")

    return True
