#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 10:43:37 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

In this module views regarding data import from cryoweb are described

"""

import shlex
import subprocess
import sys

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.shortcuts import redirect, render

from image_app import helper
from image_app.models import (Animal, DataSource, DictBreed, DictSex, Name,
                              Sample)


@login_required
def upload_cryoweb(request):
    """Imports backup into the imported_from_cryoweb db

    This function uses the container's installation of psql to import a backup
    file into the "imported_from_cryoweb" database. The imported backup file is
    the last inserted into the image's table image_app_datasource.

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page

    """

    # get a cryoweb helper instance
    cryowebdb = helper.CryowebDB()

    # test if cryoweb has data or not
    if cryowebdb.has_data(search_path='apiis_admin'):
        # TODO: give an error message
        # using admin urls
        # https://docs.djangoproject.com/en/dev/ref/contrib/admin/#admin-reverse-urls
        return redirect('admin:index')

    username = request.user.username
    context = {'username': username}

    # TODO: get datasource to load from link or admin
    datasource = DataSource.objects.order_by("-uploaded_at").first()

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

    try:
        result = subprocess.run(
            cmds,
            stdin=open(fullpath),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            env={'PGPASSWORD': '***REMOVED***'},
            encoding='utf8'
            )

    except subprocess.CalledProcessError as exc:
        context['returncode'] = exc.returncode
        context['stderr'] = exc.stderr

    else:
        context['output'] = result.stdout.split("\n")

    return render(request, 'image_app/upload_cryoweb.html', context)


@login_required
def import_from_cryoweb(request):
    """Reformats data and write it into the image database

    This fx reads the imported_from_cryoweb data,
    changes their format (i.e., changes field names and/or content) and
    writes data into the image database.

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    # TODO: check that database is initialized
    # check that dict sex table contains data
    if len(DictSex.objects.all()) == 0:
        raise Exception("You have to upload DictSex data")

    # define helper database objects
    cryowebdb = helper.CryowebDB()
    imagedb = helper.ImageDB()

    # set those values using a function
    engine_to_image = imagedb.get_engine()
    engine_from_cryoweb = cryowebdb.get_engine()

    # Read how many records are in the animal table.
    # TODO: What abount a second submission?
    # TODO: return an error, or something like this
    if imagedb.has_data():
        return redirect('admin:index')

    # TODO: get datasource to load from link or admin
    datasource = DataSource.objects.order_by("-uploaded_at").first()

    # define a function to get the row from database starting from dataframe
    def getDictBreedId(row, df_breeds_fin):
        """Returns DictBreed.id from a row from df_animals and df_breed"""

        # get db_breed index from row
        db_breed = row.db_breed

        # get data from df_breeds_fin using dataframr indexes
        data = df_breeds_fin.loc[db_breed].to_dict()

        # ok get an object from database. Only one result is expected
        dict_breed = DictBreed.objects.get(
                description__iexact=data["description"],
                species__iexact=data["species"])

        # return internal database id
        return dict_breed.id

    def getNameId(row, df_transfer_fin, tag, datasource=datasource):
        """Returns Name.di from df_animal, df_transfer and a tag like
        father_id, mother_id and animal_id"""

        if tag not in ["db_animal", "db_sire", "db_dam"]:
            raise Exception("Unknown tag: %s" % (tag))

        # get index from tag name (now is a row index)
        index = getattr(row, tag)

        # get data for index (using supplied datasource)
        data = df_transfer_fin.loc[index].to_dict()
        name = Name.objects.get(
                name__iexact=data["name"],
                datasource=datasource)

        # return key for requested tag
        return name.id

    # get username from context.
    # HINT: It is used?
    username = request.user.username
    context = {'username': username}

    # HINT: what about this try-except? why raising the same errors at the end?
    # TODO: model the issue at the end of the page
    try:
        # BREEDS

        # read the the v_breeds_species view in the "imported_from_cryoweb
        # database"
        df_breeds_species = pd.read_sql_table(
                'v_breeds_species',
                con=engine_from_cryoweb,
                schema="apiis_admin")

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

        # TRANSFER

        # in order to use relational constraints in animal relations (
        # mother, father) we need to 'register' an animal name into the
        # database
        df_transfer = pd.read_sql_table(
                'v_transfer',
                con=engine_from_cryoweb,
                schema="apiis_admin")

        # now derive animal names from columns
        df_transfer['name'] = (
                df_transfer['ext_unit'] + ':::' +
                df_transfer['ext_animal'])

        # subset of columns
        df_transfer_fin = df_transfer[['db_animal', 'name']]

        # remove empty spaces
        # HACK: this raise a warning in since df_transfer_fin['name'] is a
        # reference to df_transfer['name'] column, so also the original column
        # has its spaces removed. For the aim of this function this will be OK
        df_transfer_fin['name'] = df_transfer_fin['name'].str.replace(
                '\s+', '_')

        # set index to dataframe
        df_transfer_fin.index = df_transfer_fin["db_animal"]

        # insert dataframe as table into the UID database
        for row in df_transfer_fin.itertuples():
            obj, created = Name.objects.get_or_create(
                    name=row.name,
                    datasource=datasource)

            if created is False:
                print("%s: already present in database (%s)" % (
                        str(row), str(obj)),
                      file=sys.stderr)

        # ANIMALS
        # the same for animals:

        # read the v_animal view in the "imported_from_cryoweb" db
        df_animals = pd.read_sql_table(
                'v_animal',
                con=engine_from_cryoweb,
                schema="apiis_admin")

        # assign the breed_id column as DictBreed.id (will fill the)
        # breed id foreign key in animals table
        df_animals['breed_id'] = df_animals.apply(
                lambda row: getDictBreedId(row, df_breeds_fin), axis=1)

        # get internal keys from name
        df_animals['db_animal'] = df_animals.apply(
                lambda row: getNameId(
                        row,
                        df_transfer_fin,
                        "db_animal"),
                axis=1)

        # get internal keys from mother and father
        df_animals["db_sire"] = df_animals.apply(
                lambda row: getNameId(
                        row,
                        df_transfer_fin,
                        "db_sire"),
                axis=1)

        df_animals["db_dam"] = df_animals.apply(
                lambda row: getNameId(
                        row,
                        df_transfer_fin,
                        "db_dam"),
                axis=1)

        # keep only interesting columns and rename them
        df_animals_fin = df_animals[
            ['db_animal',
             'breed_id',
             'ext_sex',
             'db_sire',
             'db_dam',
             'latitude',
             'longitude']]

        df_animals_fin = df_animals_fin.rename(
            columns={
                'db_animal': 'name_id',
                'ext_sex': 'sex_id',
                'db_sire': 'father_id',
                'db_dam': 'mother_id',
                'latitude': 'farm_latitude',
                'longitude': 'farm_longitude',
            }
        )

        # get male and female DictSex objects fomr database
        male = DictSex.objects.get(label="male")
        female = DictSex.objects.get(label="female")

        # HINT: here we can translate sex value in male.id or female.id
        df_animals_fin['sex_id'] = df_animals_fin['sex_id'].replace(
                {'m': male.id, 'f': female.id})

        # insert animal in database
        # HINT: ANIMAL:::ID:::Ramon_142436 is present two times in database
        # with this, the second entry will not be inserted into Animal table
        for row in df_animals_fin.itertuples():
            obj, created = Animal.objects.get_or_create(
                    name_id=row.name_id,
                    breed_id=row.breed_id,
                    sex_id=row.sex_id,
                    father_id=row.father_id,
                    mother_id=row.mother_id,
                    farm_latitude=row.farm_latitude,
                    farm_longitude=row.farm_longitude)

            if created is False:
                print("%s: already present in database (%s)" % (
                        str(row), str(obj)),
                      file=sys.stderr)

        # SAMPLES
        # the same for samples

        # read view in "imported_from_cryoweb" db
        df_samples = pd.read_sql_table(
                'v_vessels',
                con=engine_from_cryoweb,
                schema="apiis_admin")

        # get internal keys from animal name
        df_samples['name_id'] = df_samples.apply(
                lambda row: getNameId(
                        row,
                        df_transfer_fin,
                        "db_animal"),
                axis=1)

        # now get a row in the animal table
        df_samples['animal_id'] = df_samples.apply(
                lambda row: Name.objects.get(
                        id=row['name_id'],
                        datasource=datasource).animal_name.id,
                axis=1)

        # keep only interesting columns and rename them
        df_samples_fin = df_samples[
            ['db_vessel',
             'ext_vessel',
             'production_dt',
             'ext_protocol_id',
             'animal_id']]

        # TODO: ext_protocol_id need to be resolved in protocol name

        df_samples_fin = df_samples_fin.rename(
            columns={
                'ext_vessel': 'name',
                'production_dt': 'collection_date',
                'ext_protocol_id': 'protocol',
            }
        )

        # change some data values: replace spaces in names and notes
        df_samples_fin['name'] = df_samples_fin['name'].str.replace(
                '\s+', '_')

        # add index
        df_samples_fin.index = df_samples_fin['db_vessel']
        del(df_samples_fin['db_vessel'])

        # insert sample names in Name table into the UID database
        for row in df_samples_fin.itertuples():
            obj, created = Name.objects.get_or_create(
                    name=row.name,
                    datasource=datasource)

            if created is False:
                print("%s: already present in database (%s)" % (
                        str(row), str(obj)),
                      file=sys.stderr)

        # now get Name.id from table
        df_samples_fin["name_id"] = df_samples_fin.apply(
                lambda row: Name.objects.get(
                        name=row['name'],
                        datasource=datasource).id,
                axis=1)

        # drop colunm name (cause now I have an ID)
        del(df_samples_fin["name"])

        # insert dataframe as table into the UID database
        df_samples_fin.to_sql(
                name=Sample._meta.db_table,
                con=engine_to_image,
                if_exists='append',
                index=False)

        # TODO: organization, persons and so on were filled using
        # login information or template excel files
        context['fullpath'] = "OK"

    except Exception:
        context['fullpath'] = "ERROR!"
        raise

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
    return redirect('admin:index')
