from django.views import View
from django.http import HttpResponseRedirect
from django.shortcuts import get_list_or_404, render, redirect
from django.contrib.auth.decorators import login_required
import os
import shlex
from image_app.forms import DataSourceForm
from django.conf import settings
import codecs
# from django.http import HttpResponse
from image_app.models import (
        Animals, Submission, Person, Organization, Publication, Database,
        Term_source, DataSource, DictSex, DictBreed, Transfer)
import subprocess
import pandas as pd
from sqlalchemy import create_engine
# import numpy
from django.core.management import call_command

# from django.views import generic
# import sys


def check_metadata(request):
    # username = None
    check_passed = True
    submissions = persons = organizations = 'static/admin/img/icon-no.svg'
    publications = databases = term_sources = 'static/admin/img/icon-yes.svg'

    if request.user.is_authenticated():
        username = request.user.username
        context = {'username': username}
    else:
        context = {'error_message': 'You are not authenticated'}

    if len(Submission.objects.all()) > 0:
        submissions = 'static/admin/img/icon-yes.svg'
        if len(Submission.objects.all()) > 1:
            context['submissions_warning'] = 'Note: you have more than one' + \
                ' submission record. Only the most recent will be used.'
    else:
        check_passed = False

    if len(Person.objects.all()) > 0:
        persons = 'static/admin/img/icon-yes.svg'
    else:
        check_passed = False
    if len(Organization.objects.all()) > 0:
        organizations = 'static/admin/img/icon-yes.svg'
    else:
        check_passed = False
    if len(Publication.objects.all()) > 0:
        publications = 'static/admin/img/icon-yes.svg'
    if len(Database.objects.all()) > 0:
        databases = 'static/admin/img/icon-yes.svg'
    if len(Term_source.objects.all()) > 0:
        term_sources = 'static/admin/img/icon-yes.svg'

    context['submissions'] = submissions
    context['persons'] = persons
    context['organizations'] = organizations
    context['publications'] = publications
    context['databases'] = databases
    context['term_sources'] = term_sources
    context['check_passed'] = check_passed

    return render(request, 'image_app/check_metadata.html', context)


def sampletab1(request):
    # username = None

    if request.user.is_authenticated():
        username = request.user.username
        context = {'username': username}
    else:
        context = {'error_message': 'You are not authenticated'}

    return render(request, 'image_app/sampletab1.html', context)


def write_record(myfile, record):
    """Writes a string into a file, then newline

    :param myfile: a file opened in append mode
    :param record: a tab separated string to be added, in append mode,
                   in the file
    """

    global codecs

    with codecs.open(myfile, "a", encoding="utf-8") as f:
        f.write(record)
        f.write("\n")


def sampletab2(request):
    """Creates the Sampletab file

    This function creates the sampletab file. It is an unusually long fx, but
    made of a relatively simple structure:
    It creates the header of the file, containing data coming from the
    organisms and persons tables. Once finished writes the true data:
    writes the field names row, then for each animal it reads all animal's
    samples and write all (1 animal row + n sample rows) into the csv file,
    and does it for all animals.

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    # filelink = ''
    username = None

    if request.user.is_authenticated():
        myusername = request.user.username

        filename = "Sampletab_{}.txt".format(myusername)  # il solo nome
        fileroot = os.path.join(settings.MEDIA_ROOT, filename)  # con path
        fileurl = os.path.join(settings.MEDIA_URL, filename)  # URL

        context = {'username': username, 'fileurl': fileurl}

        # HEADER

        engine = create_engine(
                'postgresql://postgres:***REMOVED***@db:5432/image')

        pd.set_option("display.max_columns", None)
        pd.set_option("display.max_rows", None)



        # --- Submission ---
        df_submission = pd.read_sql_table('submissions', con=engine, schema='public')
        df_submission = df_submission.drop(['id', 'identifier', 'version', 'reference_layer',
                                            'update_date', 'release_date'], 1).head(1)
        df_submission = df_submission.rename(
            columns={
                'title': 'Submission Title',
                'description': 'Submission Description',
            }
        )

        cols_as_strings = ["col" + str(ind) for ind in
                           df_submission.index]  # Diverse persone sono indicate in colonne
                                                    # con nomi 0, 1, 2 ecc..., che trasformo
                                                    # in col0, col1, col2, ecc...
        df_submission.index = cols_as_strings

        # voglio una tabella come
        # name pippo
        # address via carducci
        # ecc...
        # perciò devo trasporre la tab del database
        df_submission_T = df_submission.transpose()
        df_submission_T['index1'] = df_submission_T.index # name, address, ecc... sono l'index (df.index)
                                                                # io li trasformo in una colonna vera df['index1']
        df_submission_T = df_submission_T[df_submission_T.columns[::-1]]   # inverto l'ordine delle colonne per
                                                                                    # avere index1 come prima

        submission_tbl = df_submission_T.to_csv(sep="\t", encoding="utf-8", index=False,
                                                     header=False)  # se non metto il nome del file
                                                                    # mi restituisce una stringa






        # --- Organizations ---
        df_organizations = pd.read_sql_table('organizations', con=engine, schema='public')
        df_organizations = df_organizations.drop(['id', 'role_id'], 1).head(5)  # oppure tail(5)
        df_organizations = df_organizations.rename(
            columns={
                'name': 'Organization Name',
                'address': 'Organization Address',
                'URI': 'Organization URI',
            }
        )
        cols_as_strings = ["col" + str(ind) for ind in
                           df_organizations.index]  # Diverse organizzazioni sono indicate in colonne
                                                    # con nomi 0, 1, 2 ecc..., che trasformo
                                                    # in col0, col1, col2, ecc...
        df_organizations.index = cols_as_strings

        # voglio una tabella come
        # name pippo
        # address via carducci
        # ecc...
        # perciò devo trasporre la tab del database
        df_organizations_T = df_organizations.transpose()
        df_organizations_T['index1'] = df_organizations_T.index # name, address, ecc... sono l'index (df.index)
                                                                # io li trasformo in una colonna vera df['index1']
        df_organizations_T = df_organizations_T[df_organizations_T.columns[::-1]]   # inverto l'ordine delle colonne per
                                                                                    # avere index1 come prima

        organizations_tbl = df_organizations_T.to_csv(sep="\t", encoding="utf-8", index=False,
                                                     header=False)  # se non metto il nome del file
                                                                    # mi restituisce una stringa



        # --- Persons ---
        df_persons = pd.read_sql_table('persons', con=engine, schema='public')
        df_persons = df_persons.drop(['id', 'initials', 'role_id'], 1).head(5)  # oppure tail(5)
        df_persons = df_persons.rename(
            columns={
                'last_name': 'Person Last Name',
                'first_name': 'Person First Name',
                'email': 'Person Email',
            }
        )

        cols_as_strings = ["col" + str(ind) for ind in
                           df_persons.index]        # Convert indexes from integers to strings starting with "col"
                                                    # e.g., 0, 1, 2 to col0, col1, col2

        df_persons.index = cols_as_strings

        # Transpose the persons table content to meet the header format
        # e.g.,
        # name\tjohn
        # address\tFirst Street
        df_persons_T = df_persons.transpose()
        df_persons_T['index1'] = df_persons_T.index # name, address, ecc... sono l'index (df.index)
                                                                # io li trasformo in una colonna vera df['index1']
        df_persons_T = df_persons_T[df_persons_T.columns[::-1]]   # inverto l'ordine delle colonne per
                                                                                    # avere index1 come prima

        persons_tbl = df_persons_T.to_csv(sep="\t", encoding="utf-8", index=False,
                                                     header=False)  # se non metto il nome del file
                                                                    # mi restituisce una stringa





        with codecs.open(fileroot, 'w', encoding="utf-8") as f:
            f.write('[MSI]\n')
            f.write(submission_tbl)
            f.write(organizations_tbl)
            f.write(persons_tbl)
            f.write('\n')


        with codecs.open(fileroot, 'a', encoding="utf-8") as f:
            # f.write('[MSI]\n')
            # f.write('...\n')
            f.write('[SCD]\n')
            f.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                        'Sample Name',
                        'Sample Accession',
                        'Sample Description',
                        'Characteristic[project]',
                        'Material',
                        'Organism',
                        'Sex',
                        'Characteristic[breed]',
                        'Derived From',
                        'Characteristic[father]',
                        'Characteristic[mother]',
                        'Characteristic[organism part]',
                        'Characteristic[specimen collection date]',
                        'Unit',
                        'Characteristic[animal age at collection]',
                        'Unit',
                        'Characteristic[developmental stage]',
                        'Characteristic[animal farm latitude]',
                        'Characteristic[animal farm longitude]',
                        'Characteristic[biobank description]',
                        'Characteristic[biobank address]',
                        'Characteristic[biobank contacts]',

                        ))
        # animals = get_list_or_404(Animals)
        # queryset = Animals.objects.filter(author=request.user.id)
        # animals = get_list_or_404(Animals, id='763')
        animals = get_list_or_404(Animals)

        for a in animals:
            # buffer = a.name

            try:
                father = Animals.objects.get(pk=a.father_id).name
            except Animals.DoesNotExist:
                father = ''
            try:
                mother = Animals.objects.get(pk=a.mother_id).name
            except Animals.DoesNotExist:
                mother = ''

            # eva = a.eva.all()
            # eva_str = ';'.join([e.description for e in eva])
            record = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                    a.name,
                    # a.name,
                    "IMAGE-a{0:05d}".format(a.id),
                    a.description,
                    'Image',
                    'organism',
                    a.breed.species,
                    a.sex.description,
                    a.breed.description,
                    '',
                    father,
                    mother,
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    a.farm_latitude,
                    a.farm_longitude,
                    '',
                    '',
                    '',
                    # '', # eva_str,
                    )
            write_record(fileroot, record)
            samples = a.samples.all()
            for s in samples:
                record = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                        # "{}_{}".format(a.name, s.name),
                        s.name,
                        "IMAGE-s{0:05d}".format(s.id),
                        s.description,
                        'Image',
                        'specimen from organism',
                        '',
                        '',
                        '',
                        "IMAGE-a{0:05d}".format(a.id),
                        '',
                        '',
                        s.organism_part,
                        s.collection_date,
                        'YYYY-MM-DD',
                        s.animal_age_at_collection,
                        'year',
                        s.developmental_stage,
                        '',
                        '',
                        '',
                        )
                write_record(fileroot, record)

    else:
        context = {'error_message': 'You are not authenticated'}
    return render(request, 'image_app/sampletab2.html', context)


class DataSourceView(View):
    """Handling DataSource forms with class based views"""

    form_class = DataSourceForm
    template_name = "image_app/data_upload.html"

    def get(self, request, *args, **kwargs):
        """Return this when accessing form through GET method"""

        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        """Return this when accessing form through POST method"""

        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            # <process form cleaned data>
            return HttpResponseRedirect('../../')

        return render(request, self.template_name, {'form': form})


def dump_reading(request):
    """Imports backup into the received_from_cryoweb db

    This function uses the container's installation of psql to import a backup
    file into the "imported_from_cryoweb" database. The imported backup file is
    the last inserted into the image's table image_app_datasource.

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page

    """

    if request.user.is_authenticated():
        # TODO: read parameters from file?
        engine_from_cryoweb = create_engine(
            'postgresql://postgres:***REMOVED***@db:5432/imported_'
            'from_cryoweb')

        # change default schema
        conn = engine_from_cryoweb.connect()
        conn.execute("SET search_path TO apiis_admin, public")

        num_animals = pd.read_sql_query(
            'select count(*) as num from animal',
            con=conn)

        num_animals = num_animals['num'].values[0]
        # print("animals num:\n{}".format(num_animals))

        username = request.user.username
        context = {'username': username}
        last_backup = list(DataSource.objects.all())[-1]

        fullpath = last_backup.backup.file

        # get a string and quote fullpath
        fullpath = shlex.quote(str(fullpath))

        # append fullpath to context
        context['fullpath'] = fullpath

        if num_animals > 0:
            # TODO: give an error message
            return redirect('../../')

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

        return render(request, 'image_app/dump_reading.html', context)

    else:
        # redirect if not authenticated
        return redirect('../../')


@login_required
def dump_reading2(request):
    """Reformats data and write it into the image database

    This fx reads the imported_from_cryoweb data,
    changes their format (i.e., changes field names and/or content) and
    writes data into the image database.

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    # TODO: set those values using a function
    engine_to_image = create_engine(
        'postgresql://postgres:***REMOVED***@db:5432/image')

    engine_from_cryoweb = create_engine(
        'postgresql://postgres:***REMOVED***@db:5432/imported_from_cryoweb')

    # Read how many records are in the animal table.
    # TODO: What abount a second submission?
    num_animals = Animals.objects.count()

    # TODO: return an error, or something like this
    if num_animals > 0:
        return redirect('../../')

    # define a function to get the row from database starting from dataframe
    def getDictBreedId(row, df_breeds_fin):
        """Returns DictBreed.id from a row from df_animals and df_breed"""

        # get db_breed index from row
        db_breed = row.db_breed.values[0]

        # get data from df_breeds_fin using dataframr indexes
        data = df_breeds_fin.loc[db_breed].to_dict()

        # ok get an object from database. Only one result is expected
        dict_breed = DictBreed.objects.get(
                description__iexact=data["description"],
                species__iexact=data["species"])

        # return internal database id
        return dict_breed.id

    def getTransferId(row, df_transfer_fin, tag):
        """Returns Transfer.di from df_animal, df_transfer and a tag like
        father_id, mother_id and animal_id"""

        if tag not in ["db_animal", "db_sire", "db_dam"]:
            raise Exception("Unknown tag: %s" % (tag))

        # get index from tag name
        index = getattr(row, tag).values[0]

        # get data for index
        data = df_transfer_fin.loc[index].to_dict()
        transfer = Transfer.objects.get(
                name__iexact=data["name"])

        # return key for requested tag
        return transfer.id

    # get username from context.
    # HINT: It is used?
    username = request.user.username
    context = {'username': username}

    # HINT: what about this try-except? why raising the same errors at the end?
    # TODO: model the issue at the end of the page
    try:
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
                name='dict_breeds',
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
        # TODO: check animal in database and fill only missing names
        df_transfer_fin.to_sql(
                name='image_app_transfer',
                con=engine_to_image,
                if_exists='append',
                index=False)

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
                lambda row: getTransferId(
                        row,
                        df_transfer_fin,
                        "db_animal"),
                axis=1)

        # get internal keys from mother and father
        df_animals["db_sire"] = df_animals.apply(
                lambda row: getTransferId(
                        row,
                        df_transfer_fin,
                        "db_sire"),
                axis=1)

        df_animals["db_dam"] = df_animals.apply(
                lambda row: getTransferId(
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
             'birth_dt',
             'birth_year',
             'last_change_dt',
             'latitude',
             'longitude']]

        df_animals_fin = df_animals_fin.rename(
            columns={
                'db_animal': 'name_id',
                'ext_sex': 'sex_id',
                'db_sire': 'father_id',
                'db_dam': 'mother_id',
                'birth_dt': 'birth_date',
                'last_change_dt': 'submission_date',
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

        # insert dataframe as table into the UID database
        df_animals_fin.to_sql(
                name='animals',
                con=engine_to_image,
                if_exists='append',
                index=False)

        # debug: arrive here
        return render(request, 'image_app/dump_reading2.html', context)

        # SAMPLES
        # the same for samples

        # read view in "imported_from_cryoweb" db
        df_samples = pd.read_sql_table(
                'v_vessels',
                con=engine_from_cryoweb,
                schema="apiis_admin")

        # keep only interesting columns and rename them
        df_samples_fin = df_samples[
            ['db_vessel',
             'ext_vessel',
             'production_dt',
             'ext_protocol_id',
             'db_animal',
             'comment']]

        df_samples_fin = df_samples_fin.rename(
            columns={
                'db_vessel': 'id',
                'ext_vessel': 'name',
                'production_dt': 'collection_date',
                'ext_protocol_id': 'protocol',
                'db_animal': 'animal_id',
                'comment': 'notes'
            }
        )

        # change some data values:
        df_samples_fin['name'] = df_samples_fin['name'].str.replace(
                '\t', '')

        # insert dataframe as table into the UID database
        df_samples_fin.to_sql(
                name='samples',
                con=engine_to_image,
                if_exists='append',
                index=False)

        # ORGANIZATIONS
        df_contacts = pd.read_sql_table(
                'v_contacts',
                con=engine_from_cryoweb,
                schema="apiis_admin")

        df_contacts['address'] = (df_contacts['street'] + ", " +
                                  df_contacts['zip'] + " " +
                                  df_contacts['town'] + ", " +
                                  df_contacts['ext_country'])

        df_contacts['URI'] = "emailto:" + df_contacts['email']
        df_contacts = df_contacts.rename(
            columns={
                'third_name': 'name',
            }
        )

        df_organizations = df_contacts[
            ['name', 'address', 'URI']]

        df_organizations.to_sql(
                name='organizations',
                con=engine_to_image,
                if_exists='append',
                index=False)

        df_persons = df_contacts[
            ['first_name', 'second_name', 'email']]

        df_persons = df_persons.rename(
            columns={
                'second_name': 'last_name',
            }
        )

        df_persons.to_sql(
                name='persons',
                con=engine_to_image,
                if_exists='append',
                index=False)

        context['fullpath'] = "OK"

    except Exception:
        context['fullpath'] = "ERROR!"
        raise

    return render(request, 'image_app/dump_reading2.html', context)


def truncate_databases(request):
    """ truncate cryoweb and image tables

    this fx calls the custom functions truncate_cryoweb_tables and truncate_image_tables,
    defined in
    image_app/management/commands/truncate_cryoweb_tables.py and
    image_app/management/commands/truncate_image_tables.py
    in order to have the same fx "command line" is necessary to call both
    $ docker-compose run --rm uwsgi python manage.py truncate_cryoweb_tables
    $ docker-compose run --rm uwsgi python manage.py truncate_image_tables

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    if request.user.is_authenticated():
        username = request.user.username
        # context = {'username': username}

        call_command('truncate_cryoweb_tables')
        call_command('truncate_image_tables')
        return redirect('../../')

    else:
        return redirect('../../')


def truncate_image_tables(request):
    """ truncate image tables

    this fx calls the custom function truncate_image_tables, defined in
    image_app/management/commands/truncate_image_tables.py
    this fx can also be called command line as
    $ docker-compose run --rm uwsgi python manage.py truncate_image_tables

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    if request.user.is_authenticated():
        username = request.user.username
        # context = {'username': username}

        call_command('truncate_image_tables')

        return redirect('../../')

    else:
        return redirect('../../')


def truncate_cryoweb_tables(request):
    """ truncate cryoweb tables

    this fx calls the custom function truncate_cryoweb_tables, defined in
    image_app/management/commands/truncate_cryoweb_tables.py
    this fx can also be called command line as
    $ docker-compose run --rm uwsgi python manage.py truncate_cryoweb_tables

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    if request.user.is_authenticated():
        username = request.user.username
        # context = {'username': username}

        call_command('truncate_cryoweb_tables')
        return redirect('../../')

    else:
        return redirect('../../')
