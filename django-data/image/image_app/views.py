from django.shortcuts import render
from django.http import HttpResponse
from image_app.models import Animals
from image_app.models import Submission, Person, Organization, Publication, Database, Term_source
from django.shortcuts import get_list_or_404
from django.views import generic
import os
from django.conf import settings
import sys
import codecs
import pandas


def check_metadata(request):
    username = None
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
            context['submissions_warning'] = 'Note: you have more than one submission record. Only the most recent will be used.'
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
    username = None

    if request.user.is_authenticated():
        username = request.user.username
        context = {'username': username}
    else:
        context = {'error_message': 'You are not authenticated'}

    return render(request, 'image_app/sampletab1.html', context)



def write_record(myfile, record):
    global codecs

    with codecs.open(myfile, "a", encoding="utf-8") as f:
        f.write(record)
        f.write("\n")



def sampletab2(request):
    filelink = ''
    username = None

    if request.user.is_authenticated():
        myusername = request.user.username

        filename = "Sampletab_{}.csv".format(myusername) # il solo nome, senza path
        fileroot = os.path.join(settings.MEDIA_ROOT, filename) # con path assoluto
        fileurl = os.path.join(settings.MEDIA_URL, filename) # indirizzo del file sul webserver

        context = {'username': username, 'fileurl': fileurl}


        with codecs.open(fileroot, 'w', encoding="utf-8") as f:
            f.write('[MSI]\n')
            f.write('...\n')
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