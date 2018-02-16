#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 15:04:32 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

In this module, all function useful to export data are defined

"""

import os

import pandas as pd
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_list_or_404, render

from image_app import helper
from image_app.models import (Animal, Database, Organization, Person,
                              Publication, Submission, Ontology)


@login_required
def check_metadata(request):
    # username = None
    check_passed = True
    submissions = persons = organizations = 'static/admin/img/icon-no.svg'
    publications = databases = ontologies = 'static/admin/img/icon-yes.svg'

    username = request.user.username
    context = {'username': username}

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
    if len(Ontology.objects.all()) > 0:
        ontologies = 'static/admin/img/icon-yes.svg'

    context['submissions'] = submissions
    context['persons'] = persons
    context['organizations'] = organizations
    context['publications'] = publications
    context['databases'] = databases
    context['ontologies'] = ontologies
    context['check_passed'] = check_passed

    return render(request, 'image_app/check_metadata.html', context)


@login_required
def sampletab1(request):
    # username = None

    username = request.user.username
    context = {'username': username}

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


@login_required
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

    myusername = request.user.username

    filename = "Sampletab_{}.txt".format(myusername)  # il solo nome
    fileroot = os.path.join(settings.MEDIA_ROOT, filename)  # con path
    fileurl = os.path.join(settings.MEDIA_URL, filename)  # URL

    # ???: why username and not myusername
    context = {'username': username, 'fileurl': fileurl}

    # connect to image database and get engine object
    imagedb = helper.ImageDB()
    engine = imagedb.get_engine()

    # HEADER

    # --- Submission ---
    df_submission = pd.read_sql_table(
            Submission._meta.db_table,
            con=engine,
            schema='public')

    df_submission = df_submission.drop(
            ['id', 'identifier', 'version', 'reference_layer',
             'update_date', 'release_date'], 1).head(1)

    df_submission = df_submission.rename(
        columns={
            'title': 'Submission Title',
            'description': 'Submission Description',
        }
    )

    # Diverse persone sono indicate in colonne
    # con nomi 0, 1, 2 ecc..., che trasformo
    # in col0, col1, col2, ecc...
    cols_as_strings = ["col" + str(ind) for ind in
                       df_submission.index]
    df_submission.index = cols_as_strings

    # voglio una tabella come
    # name pippo
    # address via carducci
    # ecc...
    # perciò devo trasporre la tab del database
    df_submission_T = df_submission.transpose()

    # name, address, ecc... sono l'index (df.index)
    # io li trasformo in una colonna vera df['index1']
    df_submission_T['index1'] = df_submission_T.index

    # inverto l'ordine delle colonne per
    # avere index1 come prima
    df_submission_T = df_submission_T[df_submission_T.columns[::-1]]

    # se non metto il nome del file
    # mi restituisce una stringa
    submission_tbl = df_submission_T.to_csv(
            sep="\t", encoding="utf-8", index=False,
            header=False)

    # --- Organizations ---
    df_organizations = pd.read_sql_table(
            'organizations', con=engine, schema='public')

    df_organizations = df_organizations.drop(
            ['id', 'role_id'], 1).head(5)  # oppure tail(5)

    df_organizations = df_organizations.rename(
        columns={
            'name': 'Organization Name',
            'address': 'Organization Address',
            'URI': 'Organization URI',
        }
    )

    # Diverse organizzazioni sono indicate in colonne
    # con nomi 0, 1, 2 ecc..., che trasformo
    # in col0, col1, col2, ecc...
    cols_as_strings = ["col" + str(ind) for ind in
                       df_organizations.index]
    df_organizations.index = cols_as_strings

    # voglio una tabella come
    # name pippo
    # address via carducci
    # ecc...
    # perciò devo trasporre la tab del database
    df_organizations_T = df_organizations.transpose()

    # name, address, ecc... sono l'index (df.index)
    # io li trasformo in una colonna vera df['index1']
    df_organizations_T['index1'] = df_organizations_T.index

    # inverto l'ordine delle colonne per
    # avere index1 come prima
    df_organizations_T = df_organizations_T[
            df_organizations_T.columns[::-1]]

    # se non metto il nome del file mi restituisce una stringa
    organizations_tbl = df_organizations_T.to_csv(
            sep="\t", encoding="utf-8", index=False, header=False)

    # --- Persons ---
    df_persons = pd.read_sql_table('persons', con=engine, schema='public')
    df_persons = df_persons.drop(
            ['id', 'initials', 'role_id'], 1).head(5)  # oppure tail(5)

    df_persons = df_persons.rename(
        columns={
            'last_name': 'Person Last Name',
            'first_name': 'Person First Name',
            'email': 'Person Email',
        }
    )

    # Convert indexes from integers to strings starting with "col"
    # e.g., 0, 1, 2 to col0, col1, col2
    cols_as_strings = ["col" + str(ind) for ind in
                       df_persons.index]

    df_persons.index = cols_as_strings

    # Transpose the persons table content to meet the header format
    # e.g.,
    # name\tjohn
    # address\tFirst Street
    df_persons_T = df_persons.transpose()

    # name, address, ecc... sono l'index (df.index)
    # io li trasformo in una colonna vera df['index1']
    df_persons_T['index1'] = df_persons_T.index

    # inverto l'ordine delle colonne per
    # avere index1 come prima
    df_persons_T = df_persons_T[df_persons_T.columns[::-1]]

    # se non metto il nome del file
    # mi restituisce una stringa
    persons_tbl = df_persons_T.to_csv(
            sep="\t", encoding="utf-8", index=False, header=False)

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
    # animals = get_list_or_404(Animal)
    # queryset = Animal.objects.filter(author=request.user.id)
    # animals = get_list_or_404(Animal, id='763')
    animals = get_list_or_404(Animal)

    for a in animals:
        # buffer = a.name

        try:
            father = Animal.objects.get(pk=a.father_id).name
        except Animal.DoesNotExist:
            father = ''
        try:
            mother = Animal.objects.get(pk=a.mother_id).name
        except Animal.DoesNotExist:
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

    return render(request, 'image_app/sampletab2.html', context)
