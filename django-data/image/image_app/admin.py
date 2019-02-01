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
                     Name, Ontology, Organization, Person, Publication, Sample,
                     Submission, DictSex, DictUberon, DictStage)


class DictBreedAdmin(admin.ModelAdmin):
    search_fields = ['supplied_breed']
    list_per_page = 9
    list_display = (
        'supplied_breed', 'mapped_breed', 'mapped_breed_term', 'confidence',
        'country', 'specie')


class NameAdmin(admin.ModelAdmin):
    """A class to deal with animal names"""

    list_display = (
        'name', 'submission', 'biosample_id', 'owner', 'status',
        'last_changed', 'last_submitted')

    list_filter = ('owner', 'submission')

    # join immediately name with DataSouce, in order to speed up name rendering
    list_select_related = (
        'submission',
    )


# redefine form to edit Sample. Link animal to names in order to speed up
# name rendering
class SampleAdminForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(SampleAdminForm, self).__init__(*args, **kwargs)

        # This is the bit that matters:
        self.fields['animal'].queryset = Animal.objects.select_related('name')


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
            'animal').select_related(
                'name').filter(animal=animal)


class SampleInline(admin.StackedInline):
    formset = SampleInLineFormSet

    fields = (
        ('name', 'alternative_id', 'description', 'owner'),
        ('animal', 'protocol', 'organism_part'),
        ('collection_date', 'collection_place_latitude',
         'collection_place_longitude', 'collection_place'),
        ('developmental_stage', 'physiological_stage',
         'animal_age_at_collection', 'availability'),
        ('storage_processing', 'preparation_interval')
    )

    # manage a fields with many FK keys
    # https://books.agiliq.com/projects/django-admin-cookbook/en/latest/many_fks.html
    raw_id_fields = ("name", "animal")

    model = Sample
    extra = 0


class SampleAdmin(admin.ModelAdmin):
    form = SampleAdminForm

    # exclude = ('author',)
    # prepopulated_fields = {'name': ['description']}
    search_fields = ['name__name']
    list_per_page = 9
    list_display = (
        'name', 'alternative_id', 'animal',
        'protocol', 'collection_date', 'collection_place_latitude',
        'collection_place_longitude', 'collection_place', 'organism_part',
        'developmental_stage', 'physiological_stage',
        'animal_age_at_collection', 'availability', 'storage_processing',
        'preparation_interval', 'description', 'owner'
    )

    # To tell Django we want to perform a join instead of fetching the names of
    # the categories one by one
    list_select_related = ('name', 'animal__name')

    list_filter = ('owner', 'name__submission')

    fields = (
        ('name', 'alternative_id', 'description', 'owner'),
        ('animal', 'protocol', 'organism_part', 'organism_part_term'),
        ('collection_date', 'collection_place_latitude',
         'collection_place_longitude', 'collection_place'),
        ('developmental_stage', 'developmental_stage_term',
         'physiological_stage', 'animal_age_at_collection', 'availability'),
        ('storage_processing', 'preparation_interval')
    )

    # manage a fields with many FK keys
    # https://books.agiliq.com/projects/django-admin-cookbook/en/latest/many_fks.html
    raw_id_fields = ("name", "animal")


class AnimalAdmin(admin.ModelAdmin):
    search_fields = ['name__name']

    list_per_page = 9

    list_display = (
        'name', 'alternative_id', 'breed', 'sex',
        'father', 'mother', 'birth_location', 'birth_location_latitude',
        'birth_location_longitude', 'description', 'owner'
        )

    list_filter = ('owner', 'name__submission')

    fields = (
        'name', 'alternative_id', 'breed', 'sex', 'father',
        'mother', ('birth_location', 'birth_location_latitude',
                   'birth_location_longitude'),
        'description', 'owner'
        )

    # I can add manually an item if it is a readonly field
    # readonly_fields = ("name",)

    # manage a fields with many FK keys
    # https://books.agiliq.com/projects/django-admin-cookbook/en/latest/many_fks.html
    raw_id_fields = ("name", "father", "mother", "breed")

    # https://medium.com/@hakibenita/things-you-must-know-about-django-admin-as-your-app-gets-bigger-6be0b0ee9614
    list_select_related = ('name', 'breed', 'sex', 'father', 'mother')

    inlines = [SampleInline]


class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'gene_bank_name', 'gene_bank_country', 'datasource_type',
        'datasource_version', 'organization', 'status', 'owner',
        'biosample_submission_id'
    )

    list_filter = ('owner', 'status')


class PersonAdmin(admin.ModelAdmin):
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
    search_fields = ['name']
    list_display = (
        'name', 'address', 'country', 'URI', 'role',
    )


class OntologyAdmin(admin.ModelAdmin):
    search_fields = ['library_name']
    list_display = (
        'library_name', 'library_uri', 'comment',
    )


class DictCountryAdmin(admin.ModelAdmin):
    list_display = ('label', 'term', 'confidence')


class DictSpecieAdmin(admin.ModelAdmin):
    list_display = ('label', 'taxon_id', 'term', 'confidence')


# --- registering applications

# default admin class
admin.site.register(DictRole, admin.ModelAdmin)
admin.site.register(DictSex, admin.ModelAdmin)
admin.site.register(DictUberon, admin.ModelAdmin)
admin.site.register(DictStage, admin.ModelAdmin)

# Custom admin class
admin.site.register(DictSpecie, DictSpecieAdmin)
admin.site.register(DictCountry, DictCountryAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Animal, AnimalAdmin)
admin.site.register(Sample, SampleAdmin)
admin.site.register(Name, NameAdmin)
admin.site.register(DictBreed, DictBreedAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Publication, admin.ModelAdmin)
admin.site.register(Ontology, OntologyAdmin)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
