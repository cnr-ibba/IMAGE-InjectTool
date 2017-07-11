from django.contrib import admin
from image_app.models import Animals, DictBreeds, \
    Samples, Submission, Person, Organization, Publication, Database, \
    Term_source, Dict_organization_roles, Backup

# from import_export import resources
# from import_export.admin import ExportMixin, ExportActionModelAdmin


# class SampletabResource(resources.ModelResource):
# 	class Meta:
# 		model = Sampletab
class Dict_organization_rolesAdmin(admin.ModelAdmin):
    pass


class BackupAdmin(admin.ModelAdmin):
    list_display = ('description', 'backup', 'uploaded_at')


class DictBreedsAdmin(admin.ModelAdmin):
    search_fields = ['description']
    list_per_page = 9
    list_display = ('description', 'species', 'country', 'language',
                    'api_url', 'notes')

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


class SamplesInline(admin.StackedInline):
    fields = (
        ('name', 'description', 'production_data'),
        ('organism_part',
         'collection_date', 'animal_age_at_collection', 'developmental_stage'),
        ('availability', 'animal', 'notes'),
    )

    model = Samples
    extra = 0


class AnimalsAdmin(admin.ModelAdmin):
    # exclude = ('author',)
    search_fields = ['name']
    list_per_page = 9
    list_display = (
        'name', 'description', 'breed', 'sex', 'father', 'mother',
        'birth_date', 'birth_year', 'breed_standard', 'submission_date',
        'farm_latitude', 'farm_longitude', 'reproduction_place', 'notes'
    )
    fields = (
        'name', 'description', ('breed', 'breed_standard'), 'sex', 'father',
        'mother', 'birth_date', 'birth_year', 'submission_date',
        ('farm_latitude', 'farm_longitude', 'reproduction_place'), 'notes'
    )
    inlines = [SamplesInline]


class SamplesAdmin(admin.ModelAdmin):
    # exclude = ('author',)
    # prepopulated_fields = {'name': ['description']}
    search_fields = ['name']
    list_per_page = 9
    list_display = (
        'name', 'description', 'production_data', 'organism_part',
        'collection_date', 'protocol', 'animal_age_at_collection',
        'developmental_stage', 'availability', 'animal', 'notes',
    )

    # def has_change_permission(self, request, obj=None):
    #     has_class_permission = super(SamplesAdmin, self).has_change_permission(request, obj)
    #     if not has_class_permission:
    #         return False
    #     if obj is not None and not request.user.is_superuser
    #       and request.user.id != obj.author.id:
    #         return False
    #     return True
    #
    # def get_queryset(self, request):
    #     if request.user.is_superuser:
    #         return Samples.objects.all()
    #     return Samples.objects.filter(author=request.user)
    #

    # def save_model(self, request, obj, form, change):
    #     if not change:
    #         obj.author = request.user
    #     obj.save()


class SubmissionAdmin(admin.ModelAdmin):
    search_fields = ['title']
    list_display = (
        'title', 'description', 'version', 'reference_layer', 'update_date',
        'release_date',
    )


class PersonAdmin(admin.ModelAdmin):
    search_fields = ['last_name']
    list_display = (
        'last_name', 'initials', 'first_name', 'email', 'role',
    )


class OrganizationAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'name', 'address', 'URI', 'role',
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


admin.site.register(Animals, AnimalsAdmin)
admin.site.register(Samples, SamplesAdmin)

admin.site.register(DictBreeds, DictBreedsAdmin)
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
admin.site.register(Dict_organization_roles, Dict_organization_rolesAdmin)
admin.site.register(Backup, BackupAdmin)
