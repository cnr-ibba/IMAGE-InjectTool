#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  7 11:54:15 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import (Animal, DictBreed, DictCountry, DictRole, DictSpecie,
                     Ontology, Organization, Person, Publication, Sample,
                     Submission, DictSex, DictUberon, DictDevelStage,
                     DictPhysioStage)


class DictBreedAdmin(admin.ModelAdmin):
    search_fields = ['supplied_breed']
    list_per_page = 25
    list_display = (
        'supplied_breed', 'get_label', 'get_term', 'mapped_breed',
        'mapped_breed_term', 'confidence', 'country', 'specie')

    # override label and term verbose names
    def get_label(self, instance):
        return instance.label
    get_label.short_description = "label"

    def get_term(self, instance):
        return instance.term
    get_term.short_description = "term"

    list_filter = ('country', 'specie')


# inspired from here:
# https://github.com/geex-arts/django-jet/issues/244#issuecomment-325001298
class SampleInLineFormSet(forms.BaseInlineFormSet):
    ''' Base Inline formset for Sample Model'''

    def __init__(self, *args, **kwargs):
        super(SampleInLineFormSet, self).__init__(*args, **kwargs)

        # Animal will be a Animal object called when editing animal
        animal = kwargs["instance"]

        # get all Sample names from a certain animal with a unique query
        # HINT: all problems related to subquery when displaying names arise
        # from my __str__s methods, which display Sample and Animal name
        # and the relation between table Name. In order to have all sample
        # names for each animal, I need a join with three tables
        self.queryset = Sample.objects.select_related(
            'animal').filter(animal=animal)


class SampleInline(admin.StackedInline):
    formset = SampleInLineFormSet

    fields = (
        ('name', 'alternative_id', 'biosample_id'),
        ('submission', 'owner', 'status'),
        ('description', 'publication'),
        ('animal', 'protocol', 'organism_part'),
        ('collection_date', 'collection_place', 'collection_place_latitude',
         'collection_place_longitude', 'collection_place_accuracy'),
        ('developmental_stage',
         'physiological_stage', 'animal_age_at_collection',
         'animal_age_at_collection_units', 'availability'),
        ('storage', 'storage_processing', 'preparation_interval',
         'preparation_interval_units'),
        'last_submitted',
    )

    # manage a fields with many FK keys
    # https://books.agiliq.com/projects/django-admin-cookbook/en/latest/many_fks.html
    raw_id_fields = ("animal", "submission", "publication")

    model = Sample
    extra = 0


class SampleAdmin(admin.ModelAdmin):
    # exclude = ('author',)
    # prepopulated_fields = {'name': ['description']}
    search_fields = ['name', 'biosample_id']
    list_per_page = 25

    list_display = (
        'name', 'biosample_id', 'submission', 'status', 'last_changed',
        'last_submitted', 'alternative_id', 'animal', 'collection_date',
        'collection_place', 'collection_place_latitude',
        'collection_place_longitude', 'collection_place_accuracy',
        'organism_part', 'developmental_stage', 'physiological_stage',
        'animal_age_at_collection', 'animal_age_at_collection_units',
        'availability', 'storage', 'storage_processing',
        'preparation_interval', 'preparation_interval_units',
        'description', 'publication', 'owner'
        )

    # To tell Django we want to perform a join instead of fetching the names of
    # the categories one by one
    # https://medium.com/@hakibenita/things-you-must-know-about-django-admin-as-your-app-gets-bigger-6be0b0ee9614
    list_select_related = (
        'submission', 'submission__gene_bank_country', 'animal',
        'organism_part', 'developmental_stage', 'physiological_stage', 'owner'
    )

    list_filter = ('owner', 'status')

    fields = (
        ('name', 'alternative_id', 'biosample_id'),
        ('submission', 'owner', 'status'),
        ('description', 'publication'),
        ('animal', 'protocol', 'organism_part'),
        ('collection_date', 'collection_place', 'collection_place_latitude',
         'collection_place_longitude', 'collection_place_accuracy'),
        ('developmental_stage',
         'physiological_stage', 'animal_age_at_collection',
         'animal_age_at_collection_units', 'availability'),
        ('storage', 'storage_processing', 'preparation_interval',
         'preparation_interval_units'),
        'last_submitted',
    )

    # manage a fields with many FK keys
    # https://books.agiliq.com/projects/django-admin-cookbook/en/latest/many_fks.html
    raw_id_fields = ("animal", "submission", "publication")


class AnimalAdmin(admin.ModelAdmin):
    search_fields = ['name', 'biosample_id']

    list_per_page = 25
    list_display = (
        'name', 'biosample_id', 'submission', 'status', 'last_changed',
        'last_submitted', 'alternative_id', 'breed', 'sex', 'father', 'mother',
        'birth_date', 'birth_location', 'birth_location_latitude',
        'birth_location_longitude', 'birth_location_accuracy', 'description',
        'publication', 'owner'
        )

    list_filter = ('owner', 'status')

    # I don't want to change this
    readonly_fields = ("owner",)

    fields = (
        ('name', 'alternative_id', 'biosample_id'),
        ('submission', 'owner', 'status'),
        ('description', 'publication'),
        ('breed', 'sex'),
        ('father', 'mother'),
        ('birth_date', 'birth_location'),
        ('birth_location_latitude',
         'birth_location_longitude', 'birth_location_accuracy'),
        'last_submitted',
    )

    # manage a fields with many FK keys
    # https://books.agiliq.com/projects/django-admin-cookbook/en/latest/many_fks.html
    raw_id_fields = ("father", "mother", "breed", "submission", "publication")

    # https://medium.com/@hakibenita/things-you-must-know-about-django-admin-as-your-app-gets-bigger-6be0b0ee9614
    list_select_related = (
        'submission', 'submission__gene_bank_country', 'breed',
        'breed__specie', 'breed__country', 'sex', 'father', 'mother', 'owner')

    inlines = [SampleInline]


class SubmissionAdmin(admin.ModelAdmin):
    list_per_page = 25
    list_display = (
        'title', 'description', 'gene_bank_name', 'gene_bank_country',
        'datasource_type', 'datasource_version', 'organization', 'created_at',
        'updated_at', 'status', 'owner'
    )

    # manage a fields with many FK keys
    # https://books.agiliq.com/projects/django-admin-cookbook/en/latest/many_fks.html
    raw_id_fields = ("gene_bank_country", "organization")

    # I cannot edit a auto_add_now field
    readonly_fields = ('owner', 'created_at', 'updated_at')

    list_filter = ('owner', 'status')


class PersonAdmin(admin.ModelAdmin):
    list_per_page = 25
    list_display = (
        'user_name', 'full_name', 'initials', 'affiliation', 'role',
    )

    def user_name(self, obj):
        return obj.user.username

    # rename column in admin
    user_name.short_description = "User Name"

    def full_name(self, obj):
        return "%s %s" % (obj.user.first_name, obj.user.last_name)

    full_name.short_description = "Full Name"


# https://simpleisbetterthancomplex.com/tutorial/2016/11/23/how-to-add-user-profile-to-django-admin.html
class PersonInLine(admin.StackedInline):
    model = Person
    can_delete = False
    verbose_name_plural = 'Person'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    inlines = (PersonInLine, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff',
                    'get_role')
    list_select_related = ('person', )

    # this will display a column Role in User admin
    def get_role(self, instance):
        return instance.person.role
    get_role.short_description = 'Role'

    # display the inlines only in the edit form
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(UserAdmin, self).get_inline_instances(request, obj)


class OrganizationAdmin(admin.ModelAdmin):
    list_per_page = 25
    search_fields = ['name']
    list_display = (
        'name', 'address', 'country', 'URI', 'role',
    )


class OntologyAdmin(admin.ModelAdmin):
    list_per_page = 25
    search_fields = ['library_name']
    list_display = (
        'library_name', 'library_uri', 'comment',
    )


class DictCountryAdmin(admin.ModelAdmin):
    list_per_page = 25
    list_display = ('label', 'term', 'confidence')


class DictSpecieAdmin(admin.ModelAdmin):
    list_per_page = 25
    list_display = (
        'label', 'term', 'confidence', 'general_breed_label',
        'general_breed_term')


# --- registering applications

# default admin class
admin.site.register(DictRole, admin.ModelAdmin)
admin.site.register(DictSex, admin.ModelAdmin)
admin.site.register(DictUberon, admin.ModelAdmin)
admin.site.register(DictDevelStage, admin.ModelAdmin)
admin.site.register(DictPhysioStage, admin.ModelAdmin)

# Custom admin class
admin.site.register(DictSpecie, DictSpecieAdmin)
admin.site.register(DictCountry, DictCountryAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Animal, AnimalAdmin)
admin.site.register(Sample, SampleAdmin)
# admin.site.register(Name, NameAdmin)
admin.site.register(DictBreed, DictBreedAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Publication, admin.ModelAdmin)
admin.site.register(Ontology, OntologyAdmin)

# Re-register UserAdmin (to see related person data)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
