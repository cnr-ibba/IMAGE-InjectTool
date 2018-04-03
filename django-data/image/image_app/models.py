from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


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

    # TODO: fk with Ontology table

    def __str__(self):
        return "{label} ({short_form})".format(
                label=self.label,
                short_form=self.short_form)

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "role"
        unique_together = (("label", "short_form"),)


class DictBreed(models.Model):
    # this was the description field in cryoweb v_breeds_species tables
    supplied_breed = models.CharField(max_length=255, blank=True)
    mapped_breed = models.CharField(max_length=255, blank=True, null=True)

    # TODO add Mapped breed ontology library FK To Ontology
#    mapped_breed_ontology_library = models.ForeignKey(
#            'Ontology',
#            db_index=True,
#            related_name='%(class)s_mapped_breed_ontology_library')

    mapped_breed_ontology_accession = models.CharField(
            max_length=255,
            blank=True,
            null=True,
            help_text="Example: LBO_0000347")

    # TODO: species and countries need to have a dictionary table

    # HINT: country is efabis_country. For chianina there are Germany and
    # Italy breeds. There are also for other countries. Are they the same
    # breed? Need I to store country for user or datasource (useful for
    # translation)?
    country = models.CharField(max_length=255, blank=True, null=True)
    country_ontology_accession = models.CharField(
            max_length=255,
            blank=True,
            null=True,
            help_text="Example: NCIT_C16636")

    species = models.CharField(max_length=255, blank=True, null=True)

    species_ontology_accession = models.CharField(
            max_length=255,
            blank=False,
            null=True,
            help_text="Example: NCBITaxon_9823")

    # TODO add Species ontology library FK To Term source (Ontology)
#    species_ontology_library = models.ForeignKey(
#            'Ontology',
#            db_index=True,
#            related_name='%(class)s_mapped_breed_ontology_library')

    def __str__(self):
        # HINT: should I return mapped breed instead?
        return str(self.supplied_breed)

    def to_biosample(self):
        result = {}

        result['suppliedBreed'] = self.supplied_breed
        result['mappedBreed'] = {
                'text': self.mapped_breed,
                'ontologyTerms': self.mapped_breed_ontology_accession}
        result['country'] = {
                'text': self.country,
                'ontologyTerms': self.country_ontology_accession}
        return result

    class Meta:
        verbose_name = 'Breed'

        # HINT: would mapped_breed ba a better choice to define a unique key
        # using breed and species? in that case, mapped breed need to have a
        # default value, ex the descricption (supplied_breed)
        unique_together = (("supplied_breed", "species"),)


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

    def __str__(self):
        return "{label} ({short_form})".format(
                label=self.label,
                short_form=self.short_form)

    def to_biosample(self):
        return dict(text=self.label, ontologyTerms=self.short_form)

    class Meta:
        verbose_name = 'sex'
        verbose_name_plural = 'sex'


class Name(models.Model):
    """Model UID names: define a name (sample or animal) unique for each
    data submission"""

    # two different animal may have the same name. Its unicity depens on
    # data source name and version
    name = models.CharField(
            max_length=255,
            blank=False,
            null=False)

    datasource = models.ForeignKey(
            'DataSource', db_index=True,
            related_name='%(class)s_datasource')

    # This need to be assigned after submission
    # HINT: this column should be UNIQUE?
    biosample_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        # HINT: shuold I return biosampleid if defined?
        return "%s (DataSource: %s)" % (self.name, self.datasource_id)

    class Meta:
        unique_together = (("name", "datasource"),)


class Animal(models.Model):
    # an animal name has a entry in name table
    name = models.OneToOneField(
            'Name',
            on_delete=models.PROTECT,
            related_name='%(class)s_name')

    # alternative id will store the internal id in data source
    alternative_id = models.CharField(max_length=255, blank=True, null=True)

    description = models.CharField(max_length=255, blank=True, null=True)

    material = models.CharField(
            max_length=255,
            default="Organism",
            editable=False,
            null=True)

    breed = models.ForeignKey('DictBreed', db_index=True,
                              related_name='%(class)s_breed')

    # species is in DictBreed table

    # using a constraint for sex
    sex = models.ForeignKey('DictSex', db_index=True, blank=True, null=True,
                            default=-1, related_name='%(class)s_sex')

    # check that father and mother are defined using Foreign Keys
    father = models.ForeignKey(
            'Name',
            on_delete=models.PROTECT,
            related_name='%(class)s_father')

    mother = models.ForeignKey(
            'Name',
            on_delete=models.PROTECT,
            related_name='%(class)s_mother')

    # HINT: and birth date?

    # TODO: need to set this value? How?
    birth_location = models.CharField(
            max_length=255,
            blank=True,
            null=True)

    birth_location_latitude = models.FloatField(blank=True, null=True)
    birth_location_longitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return str(self.name)

    def to_biosample(self):
        """Get a biosample representation of animal"""

        result = {}

        # get a biosample id or a default value
        biosample_id = self.name.biosample_id or "temp%s" % (
                self.alternative_id)

        result["biosampleId"] = biosample_id

        result["project"] = "IMAGE"
        result["description"] = self.description
        result["material"] = {
                "text": "organism",
                "ontologyTerms": "OBI_0100026"
        }

        result["name"] = self.name.name

        result["dataSourceName"] = self.name.datasource.name
        result["dataSourceVersion"] = self.name.datasource.version
        result["dataSourceId"] = self.alternative_id

        result["species"] = {
                "text": self.breed.species,
                "ontologyTerms": self.breed.species_ontology_accession
        }

        result["breed"] = self.breed.to_biosample()

        result["sex"] = self.sex.to_biosample()

        # TODO: were are father and mother? Should unknown return no fields?

        return result


class Sample(models.Model):
    # a sample name has a entry in name table
    name = models.ForeignKey(
            'Name',
            on_delete=models.PROTECT,
            related_name='%(class)s_name')

    # db_vessel in data source
    alternative_id = models.CharField(max_length=255, blank=True, null=True)

    description = models.CharField(max_length=255, blank=True, null=True)

    material = models.CharField(
        max_length=255,
        default="Specimen from Organism",
        editable=False,
        null=True)

    animal = models.ForeignKey(
            'Animal',
            on_delete=models.PROTECT,
            related_name='%(class)s_animal')

    protocol = models.CharField(max_length=255, blank=True, null=True)

    collection_date = models.DateField(blank=True, null=True)
    collection_place_latitude = models.FloatField(blank=True, null=True)
    collection_place_longitude = models.FloatField(blank=True, null=True)
    collection_place = models.CharField(max_length=255, blank=True, null=True)

    organism_part = models.CharField(max_length=255, blank=True, null=True)

    developmental_stage = models.CharField(
            max_length=255,
            blank=True,
            null=True)
    physiological_stage = models.CharField(
            max_length=255,
            blank=True,
            null=True)

    animal_age_at_collection = models.IntegerField(null=True, blank=True)

    availability = models.CharField(max_length=255, blank=True, null=True)

    storage = models.CharField(max_length=255, blank=True, null=True)

    storage_processing = models.CharField(
            max_length=255,
            blank=True,
            null=True)

    preparation_interval = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return str(self.name)


class Submission(models.Model):
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

    # the following three attributes are related to Biosample submission
    # in general. Not in ruleset
    reference_layer = models.CharField(
            max_length=255, blank=True, null=True,
            help_text=('If this submission is part of the reference layer, '
                       'this will be "true". Otherwise it will be "false"'))

    # Not in ruleset
    update_date = models.DateField(
            blank=True, null=True,
            help_text="Date this submission was last modified")

    # Not in ruleset
    release_date = models.DateField(
            blank=True, null=True,
            help_text=("Date to be made public on. If blank, it will be "
                       "public immediately"))

    def __str__(self):
        return str(str(self.id) + ", " + str(self.title))


class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    initials = models.CharField(max_length=255, blank=True, null=True)
    affiliation = models.CharField(max_length=255, blank=True, null=True)

    # last_name, first_name and email comes from User model

    role = models.ForeignKey(
            'DictRole',
            on_delete=models.PROTECT,
            related_name='%(class)s_role',
            null=True)

    organizations = models.ManyToManyField('Organization')

    def get_organizations(self):
        return ", ".join([p.name for p in self.organizations.all()])

    def __str__(self):
        return "{name} {surname} ({affiliation})".format(
                name=self.user.first_name,
                surname=self.user.last_name,
                affiliation=self.affiliation)


# https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
# we will now define signals so our Person model will be automatically
# created/updated when we create/update User instances.
# Basically we are hooking the create_user_person and save_user_person
# methods to the User model, whenever a save event occurs. This kind of signal
# is called post_save.
# TODO: add default values when creating a superuser
@receiver(post_save, sender=User)
def create_user_person(sender, instance, created, **kwargs):
    if created:
        Person.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_person(sender, instance, **kwargs):
    instance.person.save()


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
        return self.name


class Database(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    name = models.CharField(max_length=255)
    DB_ID = models.CharField(max_length=255)
    URI = models.URLField(max_length=500, blank=True, null=True,
                          help_text='Database URI for this entry, ' +
                          'typically a web page.')

    def __str__(self):
        return str(str(self.id) + ", " + str(self.name))


class Publication(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    pubmed_id = models.CharField(max_length=255,
                                 help_text='Valid PubMed ID, numeric only')

    # This column is in submission sheet of template file
    doi = models.CharField(max_length=255,
                           help_text='Valid Digital Object Identifier')

    def __str__(self):
        return str(str(self.id) + ", " + str(self.pubmed_id))


class Ontology(models.Model):
    library_name = models.CharField(
            max_length=255,
            help_text='Each value must be unique',
            unique=True)

    library_uri = models.URLField(
            max_length=500, blank=True, null=True,
            help_text='Each value must be unique ' +
                      'and with a valid URL')

    comment = models.CharField(
            max_length=255, blank=True, null=True)

    def __str__(self):
        return self.library_name

    class Meta:
        verbose_name_plural = "ontologies"


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

    # internal column to check if data were uploaded in image db or not
    loaded = models.BooleanField(default=False)

    # need I store country here?

    def __str__(self):
        return "%s, %s" % (self.name, self.version)

    class Meta:
        # HINT: can I put two files for my cryoweb instance? May they have two
        # different version
        unique_together = (("name", "version"),)
