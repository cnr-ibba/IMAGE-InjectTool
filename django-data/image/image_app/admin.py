
from django.contrib import admin

from image_app.models import (Animal, Database, DataSource, DictBreed,
                              DictRole, Name, Organization, Person,
                              Publication, Sample, Submission, Term_source)

# from import_export import resources
# from import_export.admin import ExportMixin, ExportActionModelAdmin


# class SampletabResource(resources.ModelResource):
# 	class Meta:
# 		model = Sampletab


class DictRoleAdmin(admin.ModelAdmin):
    pass


class DataSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'uploaded_file', 'uploaded_at')


class DictBreedAdmin(admin.ModelAdmin):
    search_fields = ['description']
    list_per_page = 9
    list_display = ('description', 'mapped_breed', 'species', 'country',
                    'language', 'api_url', 'notes')

# class DictBiobanksAdmin(admin.ModelAdmin):
#     search_fields = ['description']
#     list_display = ('description', 'address', 'contacts',
#                     'collection_institution', 'notes')

# class DictBiosampleAdmin(admin.ModelAdmin):
#     search_fields = ['description']
#     list_display = ('description', 'api_url', 'notes')

# class DictEVAAdmin(admin.ModelAdmin):
#     search_fields = ['description']
#     list_display = ('description', 'animal', 'api_url', 'notes')
#
# class DictENAAdmin(admin.ModelAdmin):
#     search_fields = ['description']
#     list_display = ('description', 'animal', 'api_url', 'notes')


class NameAdmin(admin.ModelAdmin):
    """A class to deal with animal names"""

    # TODO: remove this column
    exclude = ('db_animal',)

    # remove this admin class from admin page, even if such class is registered
    # however this class will be editable from classes using Foreign Keys
    # TODO: expose this class?
    def get_model_perms(self, request):
        return {}


class SampleInline(admin.StackedInline):
    fields = (
        ('name', 'biosampleid', 'alternative_id'),
        ('animal', 'protocol', 'organism_part'),
        ('collection_date', 'collection_place_latitude',
         'collection_place_longitude', 'collection_place'),
        ('developmental_stage', 'physiological_stage',
         'animal_age_at_collection', 'availability'),
        ('storage_processing', 'preparation_interval')
    )

    model = Sample
    extra = 0


class AnimalAdmin(admin.ModelAdmin):
    search_fields = ['name__name']
    list_per_page = 9
    list_display = (
        'name', 'biosampleid', 'alternative_id', 'material', 'breed', 'sex',
        'father', 'mother', 'birth_location', 'farm_latitude',
        'farm_longitude'
        )
    fields = (
        'biosampleid', 'name', 'alternative_id', 'breed', 'sex', 'father',
        'mother', ('birth_location', 'farm_latitude', 'farm_longitude'),
        )
    inlines = [SampleInline]


class SampleAdmin(admin.ModelAdmin):
    # exclude = ('author',)
    # prepopulated_fields = {'name': ['description']}
    search_fields = ['name']
    list_per_page = 9
    list_display = (
        'name', 'biosampleid', 'alternative_id', 'material', 'animal',
        'protocol', 'collection_date', 'collection_place_latitude',
        'collection_place_longitude', 'collection_place', 'organism_part',
        'developmental_stage', 'physiological_stage',
        'animal_age_at_collection', 'availability', 'storage_processing',
        'preparation_interval'
    )

    # def has_change_permission(self, request, obj=None):
    #     has_class_permission = super(
    #         SampleAdmin, self).has_change_permission(request, obj)
    #     if not has_class_permission:
    #         return False
    #     if obj is not None and not request.user.is_superuser
    #       and request.user.id != obj.author.id:
    #         return False
    #     return True
    #
    # def get_queryset(self, request):
    #     if request.user.is_superuser:
    #         return Sample.objects.all()
    #     return Sample.objects.filter(author=request.user)
    #

    # def save_model(self, request, obj, form, change):
    #     if not change:
    #         obj.author = request.user
    #     obj.save()


class SubmissionAdmin(admin.ModelAdmin):
    search_fields = ['title']
    list_display = (
        'title', 'project', 'description', 'version', 'reference_layer',
        'update_date', 'release_date',
    )


class PersonAdmin(admin.ModelAdmin):
    search_fields = ['last_name']
    list_display = (
        'last_name', 'initials', 'first_name', 'email', 'affiliation', 'role',
    )


class OrganizationAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'name', 'address', 'country', 'URI', 'role',
    )


class PublicationAdmin(admin.ModelAdmin):
    search_fields = ['pubmed_id']
    list_display = (
        'pubmed_id', 'doi',
    )


class DatabaseAdmin(admin.ModelAdmin):
    search_fields = ['name', 'DB_ID']
    list_display = (
        'name', 'DB_ID', 'URI',
    )


class Term_sourceAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'name', 'URI', 'version',
    )


admin.site.register(Animal, AnimalAdmin)
admin.site.register(Sample, SampleAdmin)
admin.site.register(Name, NameAdmin)

admin.site.register(DictBreed, DictBreedAdmin)
# admin.site.register(DictBiobanks, DictBiobanksAdmin)
# admin.site.register(DictBiosample, DictBiosampleAdmin)
# admin.site.register(DictEVA, DictEVAAdmin)
# admin.site.register(DictENA, DictENAAdmin)

admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Publication, PublicationAdmin)
admin.site.register(Database, DatabaseAdmin)
admin.site.register(Term_source, Term_sourceAdmin)
admin.site.register(DictRole, DictRoleAdmin)
admin.site.register(DataSource, DataSourceAdmin)
