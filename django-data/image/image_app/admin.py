
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from image_app.models import (Animal, Database, DataSource, DictBreed,
                              DictRole, Name, Organization, Person,
                              Publication, Sample, Submission, Term_source)


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

    list_select_related = (
        'datasource',
    )

    # remove this admin class from admin page, even if such class is registered
    # however this class will be editable from classes using Foreign Keys
    # TODO: expose this class?
    def get_model_perms(self, request):
        return {}


class SampleAdminForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(SampleAdminForm, self).__init__(*args, **kwargs)
        # This is the bit that matters:
        self.fields['animal'].queryset = Animal.objects.select_related('name')


class SampleInLineFormset(forms.BaseInlineFormSet):
    ''' Base Inline formset for Sample Model'''

    def __init__(self, *args, **kwargs):
        super(SampleInLineFormset, self).__init__(*args, **kwargs)

        # Animal will be a Animal object called when editing animal
        animal = kwargs["instance"]

        self.queryset = Sample.objects.select_related(
                'animal').select_related(
                        'name').filter(animal=animal)


class SampleInline(admin.StackedInline):
    formset = SampleInLineFormset

    fields = (
        ('name', 'biosampleid', 'alternative_id', 'description'),
        ('animal', 'protocol', 'organism_part'),
        ('collection_date', 'collection_place_latitude',
         'collection_place_longitude', 'collection_place'),
        ('developmental_stage', 'physiological_stage',
         'animal_age_at_collection', 'availability'),
        ('storage_processing', 'preparation_interval')
    )

    model = Sample
    extra = 0


class SampleAdmin(admin.ModelAdmin):
    form = SampleAdminForm

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
        'preparation_interval', 'description'
    )

    # To tell Django we want to perform a join instead of fetching the names of
    # the categories one by one
    list_select_related = ('name', 'animal__name')

    fields = (
        ('name', 'biosampleid', 'alternative_id', 'description'),
        ('animal', 'protocol', 'organism_part'),
        ('collection_date', 'collection_place_latitude',
         'collection_place_longitude', 'collection_place'),
        ('developmental_stage', 'physiological_stage',
         'animal_age_at_collection', 'availability'),
        ('storage_processing', 'preparation_interval')
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


class AnimalAdmin(admin.ModelAdmin):
    search_fields = ['name__name']

    list_per_page = 9

    list_display = (
        'name', 'biosampleid', 'alternative_id', 'material', 'breed', 'sex',
        'father', 'mother', 'birth_location', 'farm_latitude',
        'farm_longitude', 'description'
        )

    fields = (
        'biosampleid', 'name', 'alternative_id', 'breed', 'sex', 'father',
        'mother', ('birth_location', 'farm_latitude', 'farm_longitude'),
        'description'
        )

    # ???: is this a readonly field
    # readonly_fields = ('name')

    # https://medium.com/@hakibenita/things-you-must-know-about-django-admin-as-your-app-gets-bigger-6be0b0ee9614
    list_select_related = ('name', 'breed', 'sex', 'father', 'mother')

    inlines = [SampleInline]


class SubmissionAdmin(admin.ModelAdmin):
    search_fields = ['title']
    list_display = (
        'title', 'project', 'description', 'version', 'reference_layer',
        'update_date', 'release_date',
    )


class PersonAdmin(admin.ModelAdmin):
    list_display = (
        'user_name', 'initials', 'affiliation', 'role', 'get_organizations'
    )

    def user_name(self, obj):
        return "%s %s" % (obj.user.first_name, obj.user.last_name)

    # rename column in admin
    user_name.short_description = "User"

    def get_organizations(self, obj):
        return obj.get_organizations()

    # rename column in admin
    get_organizations.short_description = 'Organizations'


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
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Publication, PublicationAdmin)
admin.site.register(Database, DatabaseAdmin)
admin.site.register(Term_source, Term_sourceAdmin)
admin.site.register(DictRole, DictRoleAdmin)
admin.site.register(DataSource, DataSourceAdmin)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
