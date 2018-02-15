#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 10:43:37 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

In this module views regarding data import from cryoweb are described

"""

import logging
import shlex
import subprocess

import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.shortcuts import redirect, render

from image_app import helper
from image_app.models import (Animal, DataSource, DictBreed, DictSex, Name,
                              Sample)

# Get an instance of a logger
logger = logging.getLogger(__name__)


@login_required
def upload_cryoweb(request):
    """Imports backup into the imported_from_cryoweb db

    This function uses the container's installation of psql to import a backup
    file into the "imported_from_cryoweb" database. The imported backup file is
    the last inserted into the image's table image_app_datasource.

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page

    """

    logger.info("called upload_cryoweb with request: %s" % (request))

    # get a cryoweb helper instance
    cryowebdb = helper.CryowebDB()

    # test if cryoweb has data or not
    if cryowebdb.has_data(search_path='apiis_admin'):
        # give an error message
        logger.warn("cryoweb mirror database has data. Ignoring data load")
        messages.warning(request, "cryoweb mirror database has data. Ignoring"
                                  " data load")
        return redirect('admin:index')

    username = request.user.username
    context = {'username': username}

    # TODO: get datasource to load from link or admin
    datasource = DataSource.objects.order_by("-uploaded_at").first()

    logger.debug("Got DataSource %s" % (datasource))

    # this is not only database value, but the full path in docker
    # container
    fullpath = datasource.uploaded_file.file

    # get a string and quote fullpath
    fullpath = shlex.quote(str(fullpath))

    # append fullpath to context
    context['fullpath'] = fullpath

    # define command line
    cmd_line = ("/usr/bin/psql -U cryoweb_insert_only -h db "
                "imported_from_cryoweb")

    cmds = shlex.split(cmd_line)

    logger.debug("Executing: %s" % " ".join(cmds))

    try:
        result = subprocess.run(
            cmds,
            stdin=open(fullpath),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            env={'PGPASSWORD': helper.config('CRYOWEB_INSERT_ONLY_PW')},
            encoding='utf8'
            )

    except Exception as exc:
        context['returncode'] = -1
        context['stderr'] = str(exc)
        messages.error(request, "error in calling upload_cryoweb")
        logger.error("error in calling upload_cryoweb: %s" % (exc))

    else:
        context['returncode'] = result.returncode
        context['output'] = result.stderr.split("\n")
        n_of_statements = len(result.stdout.split("\n"))

        messages.success(request, '%s statement executed' % (n_of_statements))
        logger.debug("%s statement executed" % n_of_statements)

    logger.info("upload_cryoweb finished")

    return render(request, 'image_app/upload_cryoweb.html', context)


def fill_breeds(engine_from_cryoweb, engine_to_image):
    """Helper function to upload breeds data in image database"""

    # debug
    logger.info("called fill_breeds()")

    # read the the v_breeds_species view in the "imported_from_cryoweb
    # database"
    df_breeds_species = pd.read_sql_table(
            'v_breeds_species',
            con=engine_from_cryoweb,
            schema="apiis_admin")

    logger.debug("Read %s records from v_breeds_species" % (
            df_breeds_species.shape[0]))

    # keep only interesting columns and rename them
    df_breeds_fin = df_breeds_species[
        ['db_breed',
         'efabis_mcname',
         'efabis_species',
         'efabis_country',
         'efabis_lang']]

    df_breeds_fin = df_breeds_fin.rename(
        columns={
            'efabis_mcname': 'description',
            'efabis_species': 'species',
            'efabis_country': 'country',
            'efabis_lang': 'language',
        }
    )

    # set index to dataframe. Index will be internal cryoweb id
    df_breeds_fin.index = df_breeds_fin["db_breed"]

    # HINT: the internal cryoweb id has no sense in the UID, since the same
    # breed, for example, may have two different cryoweb id in two
    # different cryoweb instances

    # TODO: db_breed column need to be removed from DictBreed model

    # insert dataframe as table into the UID database; data are
    # inserted (append) into the existing table
    # breeds have their internal ids
    # HINT: if we don't truncate any data, I can't put all breeds as they
    # are in database, but I need to check and add only new breeds
    # TODO: check data before insert
    df_breeds_fin.to_sql(
            name=DictBreed._meta.db_table,
            con=engine_to_image,
            if_exists='append',
            index=False)  # don't write DataFrame index as a column

    logger.debug("%s breeds added into database" % (df_breeds_fin.shape[0]))
    logger.info("fill_breeds() completed")

    # return processed dataframe
    return df_breeds_fin


def fill_names(dataframe, datasource):
    """A generic function to fill Name table starting from a dataframe and
    datasource"""

    # debug
    logger.info("called fill_names()")

    # A dictionary of object to create
    to_create = {}

    # get list of names of already inserted animals
    queryset = Name.objects.filter(datasource=datasource)
    in_table_names = [name.name for name in queryset]

    # debug
    logger.debug("read %s names" % (queryset.count()))

    # insert dataframe as table into the UID database
    for row in dataframe.itertuples():
        # skip duplicates (in the same bulk insert)
        if row.name in to_create:
            logger.warn("%s: already marked for insertion (%s)" % (
                    str(row), str(to_create[row.name])))

        # get or create objects: check for existance if not create an
        # object for a bulk_insert
        elif row.name in in_table_names:
            logger.warn("%s: already present in database" % (
                    str(row)))

        else:
            # create a new object
            obj = Name(name=row.name,
                       datasource=datasource)

            # append object to to_create list
            to_create[row.name] = obj

    # Now eval to_create list; if necessary, bulk_insert
    if len(to_create) > 0:
        Name.objects.bulk_create(to_create.values(), batch_size=100)

    logger.debug("%s names added to database" % (len(to_create)))
    logger.info("fill_names() finished")


def fill_transfer(engine_from_cryoweb, datasource):
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
            '\s+', '_')

    # set index to dataframe
    df_transfer_fin.index = df_transfer_fin["db_animal"]

    # call a function to fill name table
    fill_names(df_transfer_fin, datasource)

    # debug
    logger.info("fill_transfer() finished")

    # return processed objects
    return df_transfer_fin


# define a function to get the row from a dictionary of
# {(species, description: dictbreed.id} starting from dataframe
def getDictBreedId(row, df_breeds_fin, breed_to_id):
    """Returns DictBreed.id from a row from df_animals and df_breed"""

    # get db_breed index from row
    db_breed = row.db_breed

    # get data from df_breeds_fin using dataframr indexes
    data = df_breeds_fin.loc[db_breed].to_dict()

    # ok get dictbreed.id from dictionary
    key = (data['description'], data['species'])
    return breed_to_id[key]


def getNameId(row, df_transfer_fin, tag, name_to_id):
    """Returns Name.id from df_animal, df_transfer and a tag like
    father_id, mother_id and animal_id"""

    if tag not in ["db_animal", "db_sire", "db_dam"]:
        raise Exception("Unknown tag: %s" % (tag))

    # get index from tag name (now is a row index)
    index = getattr(row, tag)

    # get data for index (using supplied datasource)
    data = df_transfer_fin.loc[index].to_dict()

    # get name.id from dictionary
    return name_to_id[data["name"]]


def fill_animals(engine_from_cryoweb, df_breeds_fin, df_transfer_fin,
                 datasource):
    """Helper function to fill animal data in image animal table"""

    # debug
    logger.info("called fill_animals()")

    # read the v_animal view in the "imported_from_cryoweb" db
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
        breed_to_id[(dictbreed.description, dictbreed.species)] = dictbreed.id

    logger.debug("read %s breeds" % (DictBreed.objects.count()))

    # assign the breed_id column as DictBreed.id (will fill the)
    # breed id foreign key in animals table
    df_animals['breed_id'] = df_animals.apply(
            lambda row: getDictBreedId(
                    row, df_breeds_fin, breed_to_id),
            axis=1)

    # get name to id relation
    name_to_id = {}

    # get all names for this datasource
    for name in Name.objects.filter(datasource=datasource):
        name_to_id[name.name] = name.id

    logger.debug("read %s names" % (
            Name.objects.filter(datasource=datasource).count()))

    # get internal keys from name
    df_animals['db_animal'] = df_animals.apply(
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
        ['db_animal',
         'breed_id',
         'ext_sex',
         'db_sire',
         'db_dam',
         'latitude',
         'longitude',
         'comment']]

    df_animals_fin = df_animals_fin.rename(
        columns={
            'db_animal': 'name_id',
            'ext_sex': 'sex_id',
            'db_sire': 'father_id',
            'db_dam': 'mother_id',
            'latitude': 'farm_latitude',
            'longitude': 'farm_longitude',
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
    queryset = Animal.objects.filter(name__datasource=datasource)
    in_table_name_ids = [animal.name_id for animal in queryset]

    for row in df_animals_fin.itertuples():
        # skip duplicates (in the same bulk insert)
        if row.name_id in to_create:
            logger.warn("%s: already marked for insertion (%s)" % (
                    str(row), str(to_create[row.name_id])))

        # get or create objects: check for existance if not create an
        # object for a bulk_insert
        elif row.name_id in in_table_name_ids:
            logger.warn("%s: already present in database" % (
                    str(row)))

        else:
            # create a new object
            obj = Animal(
                name_id=row.name_id,
                breed_id=row.breed_id,
                sex_id=row.sex_id,
                father_id=row.father_id,
                mother_id=row.mother_id,
                farm_latitude=row.farm_latitude,
                farm_longitude=row.farm_longitude,
                description=row.description)

            # append object to to_create list
            to_create[row.name_id] = obj

    # Now eval to_create list; if necessary, bulk_insert
    if len(to_create) > 0:
        Animal.objects.bulk_create(to_create.values(), batch_size=100)

    # debug
    logger.debug("%s animals added to database" % (len(to_create)))
    logger.info("fill_animals() finished")

    # return animal data frame
    return df_animals_fin


def fill_samples(engine_from_cryoweb, engine_to_image, df_transfer_fin,
                 datasource):
    """Helper function to fill image samples table"""

    # debug
    logger.info("called fill_samples()")

    # read view in "imported_from_cryoweb" db
    df_samples = pd.read_sql_table(
            'v_vessels',
            con=engine_from_cryoweb,
            schema="apiis_admin")

    logger.debug("Read %s records from v_vessels" % (
            df_samples.shape[0]))

    # get name to id relation
    name_to_id = {}

    # get all names for this datasource
    for name in Name.objects.filter(datasource=datasource):
        name_to_id[name.name] = name.id

    logger.debug("read %s names" % (
            Name.objects.filter(datasource=datasource).count()))

    # get internal keys from animal name
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
            name__datasource=datasource)

    # get all names for this datasource
    for animal in queryset:
        animal_to_id[animal.name_id] = animal.id

    logger.debug("read %s animals" % (queryset.count()))

    # now get a row in the animal table
    df_samples['animal_id'] = df_samples.apply(
            lambda row: animal_to_id[row['name_id']],
            axis=1)

    # keep only interesting columns and rename them
    df_samples_fin = df_samples[
        ['db_vessel',
         'ext_vessel',
         'production_dt',
         'ext_protocol_id',
         'animal_id',
         'comment']]

    # TODO: ext_protocol_id need to be resolved in protocol name

    df_samples_fin = df_samples_fin.rename(
        columns={
            'ext_vessel': 'name',
            'production_dt': 'collection_date',
            'ext_protocol_id': 'protocol',
            'comment': 'description'
        }
    )

    # change some data values: replace spaces in names and notes
    df_samples_fin['name'] = df_samples_fin['name'].str.replace(
            '\s+', '_')

    # add index
    df_samples_fin.index = df_samples_fin['db_vessel']
    del(df_samples_fin['db_vessel'])

    # call a function to fill name table
    fill_names(df_samples_fin, datasource)

    # get name to id relation
    name_to_id = {}

    # get all names for this datasource
    for name in Name.objects.filter(datasource=datasource):
        name_to_id[name.name] = name.id

    logger.debug("read %s names" % (
            Name.objects.filter(datasource=datasource).count()))

    df_samples_fin["name_id"] = df_samples_fin.apply(
            lambda row: name_to_id[row['name']],
            axis=1)

    # drop colunm name (cause now I have an ID)
    del(df_samples_fin["name"])

    # insert dataframe as table into the UID database
    # TODO: using ORM to fill tables
    df_samples_fin.to_sql(
            name=Sample._meta.db_table,
            con=engine_to_image,
            if_exists='append',
            index=False)

    # debug
    logger.debug("%s samples added to database" % (df_samples_fin.shape[0]))
    logger.info("fill_samples() finished")

    # return processed object
    return df_samples_fin


@login_required
def import_from_cryoweb(request):
    """Reformats data and write it into the image database

    This fx reads the imported_from_cryoweb data,
    changes their format (i.e., changes field names and/or content) and
    writes data into the image database.

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    # debug
    logger.info("called import_from_cryoweb with request: %s" % (request))

    # TODO: check that database is initialized
    # check that dict sex table contains data
    if len(DictSex.objects.all()) == 0:
        raise Exception("You have to upload DictSex data")

    # define helper database objects
    cryowebdb = helper.CryowebDB()
    imagedb = helper.ImageDB()

    # set those values using a function from helper objects
    engine_to_image = imagedb.get_engine()
    engine_from_cryoweb = cryowebdb.get_engine()

    # Read how many records are in the animal table.
    # TODO: What abount a second submission?
    # TODO: return an error, or something like this
    if imagedb.has_data():
        logger.warn("image database has data. For the moment, I do nothing")
        messages.warning(request, "image database has data! please implement"
                                  " this feature")
        return redirect('admin:index')

    # TODO: get datasource to load from link or admin
    datasource = DataSource.objects.order_by("-uploaded_at").first()

    logger.debug("Got DataSource %s" % (datasource))

    # get username from context.
    # HINT: It is used?
    username = request.user.username
    context = {'username': username}

    # HINT: what about this try-except? why raising the same errors at the end?
    # TODO: model the issue at the end of the page
    try:
        # BREEDS
        df_breeds_fin = fill_breeds(engine_from_cryoweb, engine_to_image)

        # TRANSFER
        df_transfer_fin = fill_transfer(engine_from_cryoweb, datasource)

        # ANIMALS
        fill_animals(engine_from_cryoweb, df_breeds_fin, df_transfer_fin,
                     datasource)

        # SAMPLES
        fill_samples(engine_from_cryoweb, engine_to_image, df_transfer_fin,
                     datasource)

        # organization, persons are filled using
        # login information or template excel files
        context['fullpath'] = "OK"

    except Exception as e:
        context['fullpath'] = "ERROR!: %s" % (e)
        logger.error(e)

    logger.info("import_from_cryoweb finished")

    # TODO: render a better page
    return render(request, 'image_app/import_from_cryoweb.html', context)


@login_required
def truncate_cryoweb_tables(request):
    """ truncate cryoweb tables

    this fx calls the custom function truncate_cryoweb_tables, defined in
    image_app/management/commands/truncate_cryoweb_tables.py
    this fx can also be called command line as
    $ docker-compose run --rm uwsgi python manage.py truncate_cryoweb_tables

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    call_command('truncate_cryoweb_tables')

    messages.success(request, 'imported_from_cryoweb database was truncated '
                              'with success')

    return redirect('admin:index')
