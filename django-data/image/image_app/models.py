from django.db import models
# from django.contrib.auth.models import User
import datetime
# from django.core.exceptions import ValidationError
# from django.utils.translation import ugettext_lazy as _


YEAR_CHOICES = []
for r in range(1980, (datetime.datetime.now().year+1)):
    YEAR_CHOICES.append((r, r))


class Dict_organization_roles(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    description = models.CharField(max_length=255)

    def __str__(self):
        return str(self.description)

    class Meta:
        # managed = False
        db_table = 'dict_organization_roles'
        verbose_name = 'Organization role'
        verbose_name_plural = 'Organization roles'


class DictBreeds(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    db_breed = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    species = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    language = models.CharField(max_length=255, blank=True, null=True)
    api_url = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.description)

    class Meta:
        # managed = False
        db_table = 'dict_breeds'
        verbose_name = 'Breed'
        verbose_name_plural = 'Breeds'


class DictSex(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return str(self.description)

    class Meta:
        # managed = False
        db_table = 'dict_sex'
        verbose_name = 'sex'
        verbose_name_plural = 'sex'


class Animals(models.Model):
    # id = models.IntegerField(primary_key=True)
    biosampleid = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    breed = models.ForeignKey('DictBreeds', db_index=True,
                              related_name='%(class)s_breed')
    sex = models.ForeignKey('DictSex', db_index=True, blank=True, null=True,
                            default=-1, related_name='%(class)s_sex')
    father = models.ForeignKey('Animals', db_index=True, blank=True,
                               null=True, related_name='%(class)s_father')
    mother = models.ForeignKey('Animals', db_index=True, blank=True,
                               null=True, related_name='%(class)s_mother')
    birth_date = models.DateField(blank=True, null=True)
    birth_year = models.IntegerField(choices=YEAR_CHOICES, blank=True,
                                     null=True)
    breed_standard = models.CharField(max_length=255, blank=True, null=True)
    submission_date = models.DateField(blank=True, null=True)
    farm_latitude = models.FloatField(blank=True, null=True)
    farm_longitude = models.FloatField(blank=True, null=True)
    reproduction_place = models.CharField(max_length=255, blank=True, null=True)
    # author = models.ForeignKey(User, related_name='authoranimals')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(str(self.id) + ", " + str(self.name) + ", " +
                   str(self.description))

    class Meta:
        # managed = False
        db_table = 'animals'
        verbose_name = 'Animal'
        verbose_name_plural = 'Animals'


class Samples(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    biosampleid = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    production_data = models.CharField(max_length=255, blank=True, null=True)
    organism_part = models.CharField(max_length=255, blank=True, null=True)
    collection_date = models.DateField(blank=True, null=True)
    animal_age_at_collection = models.IntegerField(null=True, blank=True)
    developmental_stage = models.CharField(max_length=255, blank=True,
                                           null=True)
    # biobank = models.ForeignKey(DictBiobanks, blank=True, null=True)
    availability = models.CharField(max_length=5, blank=True, null=True)
    protocol = models.CharField(max_length=255, blank=True, null=True)
    # animal_farm_latitude = models.FloatField(blank=True, null=True)
    # animal_farm_longitude = models.FloatField(blank=True, null=True)
    # biosample = models.ForeignKey(DictBiosample, blank=True, null=True)
    # eva = models.ForeignKey(DictEVA, blank=True, null=True)
    # ena = models.ForeignKey(DictENA, blank=True, null=True)
    # animal = models.ForeignKey('Animals', blank=True, null=True,
    # related_name='%(class)s_animal')
    animal = models.ForeignKey('Animals', db_index=True,
                               related_name='samples')
    # author = models.ForeignKey(User, related_name='authorsamples')
    notes = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return str(str(self.id) + ", " + str(self.name))

    class Meta:
        # managed = False
        db_table = 'samples'
        verbose_name = 'Sample'
        verbose_name_plural = 'Samples'


class Submission(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    title = models.CharField(max_length=255,
                             help_text='Example: Roslin Sheep Atlas')
    identifier = models.CharField(max_length=255, blank=True, null=True,
                                  help_text='Must be blank if not assigned ' +
                                  'by BioSamples Database')
    description = models.CharField(max_length=255,
                                   help_text='Example: The Roslin Institute ' +
                                   'Sheep Gene Expression Atlas Project')
    version = models.CharField(max_length=255, blank=True, null=True)
    reference_layer = models.CharField(max_length=255, blank=True, null=True)
    update_date = models.DateField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return str(str(self.id) + ", " + str(self.title))

    class Meta:
        # managed = False
        db_table = 'submissions'
        verbose_name = 'Submission'
        verbose_name_plural = 'Submissions'


class Person(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    last_name = models.CharField(max_length=255, blank=True, null=True)
    initials = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=70, blank=True, null=True)
    # role = models.CharField(max_length=255, blank=True, null=True)
    role = models.ForeignKey('Dict_organization_roles',
                             blank=True, null=True,
                             related_name='%(class)s_role')

    def __str__(self):
        if str(self.first_name):
            return str(str(self.id) + ", " + str(self.first_name) + " " +
                       str(self.last_name))
        else:
            return str(str(self.id) + ", " + str(self.last_name))

    class Meta:
        # managed = False
        db_table = 'persons'
        verbose_name = 'Person'
        verbose_name_plural = 'Persons'


class Organization(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True,
                               help_text='One line, comma separated')
    URI = models.URLField(max_length=500, blank=True, null=True,
                          help_text='Web site')
    # role = models.CharField(max_length=255, blank=True, null=True)
    role = models.ForeignKey('Dict_organization_roles', blank=True, null=True,
                             related_name='%(class)s_role')

    def __str__(self):
        return str(str(self.id) + ", " + str(self.name))

    class Meta:
        # managed = False
        db_table = 'organizations'
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'


class Database(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    name = models.CharField(max_length=255)
    DB_ID = models.CharField(max_length=255)
    URI = models.URLField(max_length=500, blank=True, null=True,
                          help_text='Database URI for this entry, ' +
                          'typically a web page.')

    def __str__(self):
        return str(str(self.id) + ", " + str(self.name))

    class Meta:
        # managed = False
        db_table = 'databases'
        verbose_name = 'Database'
        verbose_name_plural = 'Databases'


class Publication(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    pubmed_id = models.CharField(max_length=255,
                                 help_text='Valid PubMed ID, numeric only')
    doi = models.CharField(max_length=255,
                           help_text='Valid Digital Object Identifier')

    def __str__(self):
        return str(str(self.id) + ", " + str(self.pubmed_id))

    class Meta:
        # managed = False
        db_table = 'publications'
        verbose_name = 'Publication'
        verbose_name_plural = 'Publications'


class Term_source(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    name = models.CharField(max_length=255,
                            help_text='Each value must be unique')
    URI = models.URLField(max_length=500, blank=True, null=True,
                          help_text='Each value must be unique ' +
                          'and with a valid URL')
    version = models.CharField(max_length=255, blank=True, null=True,
                               help_text='If version is unknown, ' +
                               'then last access date should be provided. ' +
                               'If no date is provided, one will be assigned' +
                               ' at submission.')

    def __str__(self):
        return str(str(self.id) + ", " + str(self.name))

    class Meta:
        # managed = False
        db_table = 'term_sources'
        verbose_name = 'Term Source'
        verbose_name_plural = 'Term Sources'


class Backup(models.Model):
    description = models.CharField(max_length=255, blank=True)
    backup = models.FileField(upload_to='backups/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
