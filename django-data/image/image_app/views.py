from django.shortcuts import get_list_or_404, render, redirect
import os
from image_app.forms import BackupForm
from django.conf import settings
import codecs
# from django.http import HttpResponse
from image_app.models import Animals
from image_app.models import Submission, Person, Organization, Publication, \
    Database, Term_source, Backup
import subprocess
import pandas as pd
from sqlalchemy import create_engine
import numpy

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
    :param record: a tab separated string to be added, in append mode, in the file
    """

    global codecs

    with codecs.open(myfile, "a", encoding="utf-8") as f:
        f.write(record)
        f.write("\n")


def sampletab2(request):
    """Creates the Sampletab file

    This function creates the sampletab file. It is an unusually long fx, but
    made of a relatively simple structure:
    It creates the header of the file, containing data coming from the organisms
    and persons tables. Once finished writes the true data: writes the field names row, then
    for each animal it reads all animal's samples
    and write all (1 animal row + n sample rows) into the csv file, and does it for all animals.

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    # filelink = ''
    username = None

    if request.user.is_authenticated():
        myusername = request.user.username

        filename = "Sampletab_{}.csv".format(myusername)  # il solo nome
        fileroot = os.path.join(settings.MEDIA_ROOT, filename)  # con path
        fileurl = os.path.join(settings.MEDIA_URL, filename)  # URL

        context = {'username': username, 'fileurl': "cippalippa"}

        # TEMP

        return render(request, 'image_app/sampletab2.html', context)

        # TEMP
    #     with codecs.open(fileroot, 'w', encoding="utf-8") as f:
    #         f.write('[MSI]\n')
    #         f.write('...\n')
    #         f.write('[SCD]\n')
    #         f.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
    #                     'Sample Name',
    #                     'Sample Accession',
    #                     'Sample Description',
    #                     'Characteristic[project]',
    #                     'Material',
    #                     'Organism',
    #                     'Sex',
    #                     'Characteristic[breed]',
    #                     'Derived From',
    #                     'Characteristic[father]',
    #                     'Characteristic[mother]',
    #                     'Characteristic[organism part]',
    #                     'Characteristic[specimen collection date]',
    #                     'Unit',
    #                     'Characteristic[animal age at collection]',
    #                     'Unit',
    #                     'Characteristic[developmental stage]',
    #                     'Characteristic[animal farm latitude]',
    #                     'Characteristic[animal farm longitude]',
    #                     'Characteristic[biobank description]',
    #                     'Characteristic[biobank address]',
    #                     'Characteristic[biobank contacts]',
    #
    #                     ))
    #     # animals = get_list_or_404(Animals)
    #     # queryset = Animals.objects.filter(author=request.user.id)
    #     # animals = get_list_or_404(Animals, id='763')
    #     animals = get_list_or_404(Animals)
    #
    #     for a in animals:
    #         # buffer = a.name
    #
    #         try:
    #             father = Animals.objects.get(pk=a.father_id).name
    #         except Animals.DoesNotExist:
    #             father = ''
    #         try:
    #             mother = Animals.objects.get(pk=a.mother_id).name
    #         except Animals.DoesNotExist:
    #             mother = ''
    #
    #         # eva = a.eva.all()
    #         # eva_str = ';'.join([e.description for e in eva])
    #         record = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
    #                 a.name,
    #                 # a.name,
    #                 "IMAGE-a{0:05d}".format(a.id),
    #                 a.description,
    #                 'Image',
    #                 'organism',
    #                 a.breed.species,
    #                 a.sex.description,
    #                 a.breed.description,
    #                 '',
    #                 father,
    #                 mother,
    #                 '',
    #                 '',
    #                 '',
    #                 '',
    #                 '',
    #                 '',
    #                 a.farm_latitude,
    #                 a.farm_longitude,
    #                 '',
    #                 '',
    #                 '',
    #                 # '', # eva_str,
    #                 )
    #         write_record(fileroot, record)
    #         samples = a.samples.all()
    #         for s in samples:
    #             record = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
    #                     # "{}_{}".format(a.name, s.name),
    #                     s.name,
    #                     "IMAGE-s{0:05d}".format(s.id),
    #                     s.description,
    #                     'Image',
    #                     'specimen from organism',
    #                     '',
    #                     '',
    #                     '',
    #                     "IMAGE-a{0:05d}".format(a.id),
    #                     '',
    #                     '',
    #                     s.organism_part,
    #                     s.collection_date,
    #                     'YYYY-MM-DD',
    #                     s.animal_age_at_collection,
    #                     'year',
    #                     s.developmental_stage,
    #                     '',
    #                     '',
    #                     '',
    #                     )
    #             write_record(fileroot, record)
    #
    # else:
    #     context = {'error_message': 'You are not authenticated'}
    # return render(request, 'image_app/sampletab2.html', context)


def model_form_upload(request):
    """Creates the upload form

    This function creates the BackupForm, defined in the forms.py file.
    This form adds a file to the Backups table, together with a description string.

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    if request.user.is_authenticated():
        username = request.user.username
        # context = {'username': username}

        if request.method == 'POST':
            form = BackupForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return redirect('../../')
        else:
            form = BackupForm()
        return render(request, 'image_app/model_form_upload.html', {
            'form': form, 'username': username, })

    else:
        return redirect('../../')


def dump_reading(request):
    """Imports backup into the received_from_cryoweb db

    This function uses the container's installation of psql to import a backup file into the
    "imported_from_cryoweb" database.
    The imported backup file is the last inserted into the image's table Backups.

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page

    """

    if request.user.is_authenticated():
        username = request.user.username
        context = {'username': username}
        last_backup = list(Backup.objects.all())[-1]

        fullpath = last_backup.backup.file
        context['fullpath'] = fullpath
        output = ''
        try:
            cmd_line = "export PGPASSWORD='***REMOVED***'; /usr/bin/psql -U postgres -h db " +\
                       "imported_from_cryoweb < {}".format(fullpath)
            try:
                output = subprocess.call(cmd_line, stderr=subprocess.STDOUT, 
                                         shell=True)
            except subprocess.CalledProcessError as e:
                print(e.output)
                
            context['fullpath'] = output
        except:
            context['fullpath'] = "ERROR!"
            raise

        return render(request, 'image_app/dump_reading.html', context)

    else:
        return redirect('../../')


def dump_reading2(request):
    """Reformats data and write it into the image database

    This fx reads the imported_from_cryoweb data,
    changes their format (i.e., changes field names and/or content) and
    writes data into the image database.

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    def get_breed_id(row, df_breeds_species):
        # global df_breeds_species
        breed_id = df_breeds_species.loc[(df_breeds_species['db_breed'] == row['db_breed']) & (
            df_breeds_species['db_species'] == row['db_species']), 'breed_id']

        return int(breed_id)

    if request.user.is_authenticated():
        username = request.user.username
        context = {'username': username}
        try:
            engine_from_cryoweb = create_engine('postgresql://postgres:***REMOVED***@db:5432/imported_from_cryoweb')
            engine_to_sampletab = create_engine('postgresql://postgres:***REMOVED***@db:5432/image')

            pd.set_option("display.max_columns", None)
            pd.set_option("display.max_rows", None)

            df_breeds_species = pd.read_sql_table('v_breeds_species', con=engine_from_cryoweb, schema='public')
            # df_breeds_species.head()
            df_breeds_fin = df_breeds_species[
                ['breed_id', 'db_breed', 'efabis_mcname', 'efabis_species', 'efabis_country', 'efabis_lang']]
            df_breeds_fin = df_breeds_fin.rename(
                columns={
                    'breed_id': 'id',
                    'efabis_mcname': 'description',
                    'efabis_species': 'species',
                    'efabis_country': 'country',
                    'efabis_lang': 'language',
                }
            )
            # df_breeds_fin.to_sql(name='dict_breeds', con=engine_to_sampletab, if_exists='append', index=False)

            # ANIMALS

            df_animals = pd.read_sql_table('v_animal', con=engine_from_cryoweb, schema='public')
            df_animals['breed_id'] = df_animals.apply(lambda row: get_breed_id(row, df_breeds_species), axis=1)

            df_animals_fin = df_animals[
                ['db_animal', 'ext_animal', 'breed_id', 'ext_sex', 'db_sire', 'db_dam', 'birth_dt', 'birth_year',
                 'last_change_dt', 'latitude', 'longitude']]

            df_animals_fin = df_animals_fin.rename(
                columns={
                    'db_animal': 'id',
                    'ext_animal': 'name',
                    'ext_sex': 'sex_id',
                    'db_sire': 'father_id',
                    'db_dam': 'mother_id',
                    'birth_dt': 'birth_date',
                    'last_change_dt': 'submission_date',
                    'latitude': 'farm_latitude',
                    'longitude': 'farm_longitude',
                }
            )
            df_animals_fin['sex_id'] = df_animals_fin['sex_id'].replace({'m': 1, 'f': 2})
            df_animals_fin['name'] = df_animals_fin['name'].str.replace('\t', '')
            # df_animals_fin.to_sql(name='animals', con=engine_to_sampletab, if_exists='append', index=False)

            # SAMPLES

            df_samples = pd.read_sql_table('v_vessels', con=engine_from_cryoweb, schema='public')
            # df_samples.head()
            df_samples_fin = df_samples[
                ['db_vessel', 'ext_vessel', 'production_dt', 'ext_protocol_id', 'db_animal', 'comment']]
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

            df_samples_fin['name'] = df_samples_fin['name'].str.replace('\t', '')

            # df_samples_fin.to_sql(name='samples', con=engine_to_sampletab, if_exists='append', index=False)

            # ORGANIZATIONS

            df_contacts = pd.read_sql_table('v_contacts', con=engine_from_cryoweb, schema='public')

            df_contacts['address'] = df_contacts['street'] + ", " + \
                                          df_contacts['zip'] + " " + \
                                          df_contacts['town'] + ", " + \
                                          df_contacts['ext_country']

            df_contacts['URI'] = "emailto:" + df_contacts['email']
            df_contacts = df_contacts.rename(
                columns={
                    'third_name': 'name',
                }
            )

            df_organizations = df_contacts[
                ['name', 'address', 'URI']]

            # df_organizations.to_sql(name='organizations', con=engine_to_sampletab, if_exists='append', index=False)

            df_persons = df_contacts[
                ['first_name', 'second_name', 'email']]

            df_persons = df_persons.rename(
                columns={
                    'second_name': 'last_name',
                }
            )
            df_persons.to_sql(name='persons', con=engine_to_sampletab, if_exists='append', index=False)

            context['fullpath'] = "OK"

        except:
            context['fullpath'] = "ERROR!"
            raise

        return render(request, 'image_app/dump_reading2.html', context)
    else:
        return redirect('../../')
