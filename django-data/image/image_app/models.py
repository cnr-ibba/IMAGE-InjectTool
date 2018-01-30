from django.db import models
# from django.contrib.auth.models import User
import datetime
# from django.core.exceptions import ValidationError
# from django.utils.translation import ugettext_lazy as _


YEAR_CHOICES = []
for r in range(1980, (datetime.datetime.now().year+1)):
    YEAR_CHOICES.append((r, r))


class DictRole(models.Model):
    """A class to model roles defined as childs of
    http://www.ebi.ac.uk/efo/EFO_0002012"""

    # if not defined, this table will have an own primary key
    label = models.CharField(
            max_length=255,
            blank=False,
            help_text="Example: submitter")

    short_form = models.CharField(
            max_length=255,
            blank=False,
            help_text="Example: EFO_0001741")

    def __str__(self):
        return "{label} ({short_form})".format(
                label=self.label,
                short_form=self.short_form)

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "dict role"
        unique_together = (("label", "short_form"),)


class DictBreed(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    db_breed = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    mapped_breed = models.CharField(max_length=255, blank=True, null=True)
    species = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    language = models.CharField(max_length=255, blank=True, null=True)
    api_url = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.description)

    class Meta:
        verbose_name = 'Breed'

        # HINT: would mapped_breed ba a better choice to define a unique key
        # using breed and species? in that case, mapped breed need to have a
        # default value, ex the descricption (breed_name)
        unique_together = (("description", "species"),)


class DictSex(models.Model):
    """A class to model sex as defined in PATO"""

    label = models.CharField(
            max_length=255,
            blank=False,
            unique=True,
            help_text="Example: male")

    short_form = models.CharField(
            max_length=255,
            blank=False,
            help_text="Example: PATO_0000384")

    # HINT: model translation in database?

    def __str__(self):
        return "{label} ({short_form})".format(
                label=self.label,
                short_form=self.short_form)

    class Meta:
        verbose_name = 'sex'
        verbose_name_plural = 'sex'


class Transfer(models.Model):
    """Model cryoweb transfer view: define all animal names in order to be
    referenced by Animal classes"""

    # ???: Is cryoweb internal animal_id important?
    db_animal = models.IntegerField(blank=True, null=True)

    # HINT: can two different animal have the same name? if yes, How I can
    # find its mother and father?
    name = models.CharField(
            max_length=255,
            blank=False,
            unique=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Animal name'


class Animals(models.Model):
    # id = models.IntegerField(primary_key=True)
    biosampleid = models.CharField(max_length=255, blank=True, null=True)

    # an animal name has a entry in transfer table
    name = models.ForeignKey(
            'Transfer',
            on_delete=models.PROTECT,
            related_name='%(class)s_name')

    material = models.CharField(
            max_length=255,
            default="Organism",
            editable=False,
            null=True)

    description = models.CharField(max_length=255, blank=True, null=True)
    breed = models.ForeignKey('DictBreed', db_index=True,
                              related_name='%(class)s_breed')

    # HINT: need sex a constraint?
    sex = models.ForeignKey('DictSex', db_index=True, blank=True, null=True,
                            default=-1, related_name='%(class)s_sex')

    # Need I check if animals father and mother are already present in
    # database? shuold I check relationship by constraints?
    father = models.ForeignKey(
            'Transfer',
            on_delete=models.PROTECT,
            related_name='%(class)s_father')

    mother = models.ForeignKey(
            'Transfer',
            on_delete=models.PROTECT,
            related_name='%(class)s_mother')

    birth_date = models.DateField(blank=True, null=True)
    birth_year = models.IntegerField(choices=YEAR_CHOICES, blank=True,
                                     null=True)
    breed_standard = models.CharField(max_length=255, blank=True, null=True)
    submission_date = models.DateField(blank=True, null=True)
    birth_location = models.CharField(max_length=255, blank=True, null=True)
    farm_latitude = models.FloatField(blank=True, null=True)
    farm_longitude = models.FloatField(blank=True, null=True)
    reproduction_place = models.CharField(
            max_length=255,
            blank=True,
            null=True)

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
    biosampleid = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True)
    material = models.CharField(
            max_length=255,
            default="Specimen from Organism",
            editable=False,
            null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    production_data = models.CharField(max_length=255, blank=True, null=True)
    organism_part = models.CharField(max_length=255, blank=True, null=True)
    collection_date = models.DateField(blank=True, null=True)
    collection_place_latitude = models.FloatField(blank=True, null=True)
    collection_place_longitude = models.FloatField(blank=True, null=True)
    collection_place = models.CharField(max_length=255, blank=True, null=True)
    animal_age_at_collection = models.IntegerField(null=True, blank=True)
    specimen_volume = models.IntegerField(null=True, blank=True)
    developmental_stage = models.CharField(max_length=255, blank=True,
                                           null=True)
    # biobank = models.ForeignKey(DictBiobanks, blank=True, null=True)
    availability = models.CharField(max_length=255, blank=True, null=True)
    protocol = models.CharField(max_length=255, blank=True, null=True)
    # animal_farm_latitude = models.FloatField(blank=True, null=True)
    # animal_farm_longitude = models.FloatField(blank=True, null=True)
    # biosample = models.ForeignKey(DictBiosample, blank=True, null=True)
    # eva = models.ForeignKey(DictEVA, blank=True, null=True)
    # ena = models.ForeignKey(DictENA, blank=True, null=True)
    # animal = models.ForeignKey('Animals', blank=True, null=True,
    # related_name='%(class)s_animal')
    animal = models.ForeignKey(
            'Animals',
            on_delete=models.PROTECT,
            related_name='%(class)s_animal')

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
    project = models.CharField(
            max_length=25,
            default="IMAGE",
            editable=False)

    title = models.CharField(
            max_length=255,
            help_text='Example: Roslin Sheep Atlas')

    # Assigned by BioSample. Not specified in ruleset
    identifier = models.CharField(
            max_length=255, blank=True, null=True,
            help_text='Must be blank if not assigned ' +
                      'by BioSamples Database')

    description = models.CharField(
            max_length=255,
            help_text='Example: The Roslin Institute ' +
                      'Sheep Gene Expression Atlas Project')

    # Not specified in ruleset
    version = models.CharField(
            max_length=255, blank=True, null=True,
            default=1.2)

    reference_layer = models.CharField(
            max_length=255, blank=True, null=True,
            help_text=('If this submission is part of the reference layer, '
                       'this will be "true". Otherwise it will be "false"'))

    update_date = models.DateField(
            blank=True, null=True,
            help_text="Date this submission was last modified")

    release_date = models.DateField(
            blank=True, null=True,
            help_text=("Date to be made public on. If blank, it will be "
                       "public immediately"))

    def __str__(self):
        return str(str(self.id) + ", " + str(self.title))

    class Meta:
        # managed = False
        db_table = 'submissions'
        verbose_name = 'submission'
        verbose_name_plural = 'submissions'


class Person(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    last_name = models.CharField(max_length=255, blank=True, null=True)
    initials = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=70, blank=True, null=True)
    # role = models.CharField(max_length=255, blank=True, null=True)
    affiliation = models.CharField(max_length=255, blank=True, null=True)

    role = models.ForeignKey(
            'DictRole',
            on_delete=models.PROTECT,
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
    country = models.CharField(max_length=255, blank=True, null=True)
    URI = models.URLField(max_length=500, blank=True, null=True,
                          help_text='Web site')

    role = models.ForeignKey(
            'DictRole',
            on_delete=models.PROTECT,
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


class DataSource(models.Model):
    upload_dir = 'data_source/'
    uploaded_file = models.FileField(upload_to=upload_dir)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # TODO: find a Biosample Key for this column
    name = models.CharField(
            max_length=255,
            blank=False,
            null=False,
            help_text='example: Cryoweb IBBA')

    # TODO: find a Biosample Key for this column
    version = models.CharField(
            max_length=255,
            blank=False,
            null=False,
            help_text='examples: 2017-04, version 1.1')

    def __str__(self):
        return "%s, %s" % (self.name, self.version)

    class Meta:
        # HINT: can I put two files for my cryoweb instance? May they have two
        # different version
        unique_together = (("name", "version"),)
