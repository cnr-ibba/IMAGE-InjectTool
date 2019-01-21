
import logging
import os
import shlex
from enum import Enum

from django.contrib.auth.models import User
from django.db import connections, models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from common.fields import ProtectedFileField

from .helpers import format_attribute
from .constants import OBO_URL

# Get an instance of a logger
logger = logging.getLogger(__name__)


# --- Enums


class ACCURACIES(Enum):
    missing = (0, 'missing geographic information')
    country = (1, 'country level')
    region = (2, 'region level')
    precise = (3, 'precise coordinates')
    unknown = (4, 'unknown accuracy level')

    @classmethod
    def get_value(cls, member):
        return cls[member].value[0]


# 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
class CONFIDENCES(Enum):
    high = (0, 'High')
    good = (1, 'Good')
    medium = (2, 'Medium')
    low = (3, 'Low')
    curated = (4, 'Manually Curated')

    @classmethod
    def get_value(cls, member):
        return cls[member].value[0]


# 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
# waiting: waiting to upload data (or process them!)
# loaded: data loaded into UID, can validate
# error: error in uploading data into UID or in submission
# ready: validated data ready for submission
# need_revision: validated data need checks before submission
# submitted: submitted to biosample
# completed: finalized submission with biosample id
class STATUSES(Enum):
    waiting = (0, 'Waiting')
    loaded = (1, 'Loaded')
    submitted = (2, 'Submitted')
    error = (3, 'Error')
    need_revision = (4, 'Need Revision')
    ready = (5, "Ready")
    completed = (6, "Completed")

    @classmethod
    def get_value(cls, member):
        return cls[member].value[0]


# a list of a valid statuse for names
NAME_STATUSES = [
    'loaded',
    'ready',
    'need_revision',
    'submitted',
    'completed'
]


# --- Mixins


# Adding a classmethod to Category if you want to enable truncate
# https://books.agiliq.com/projects/django-orm-cookbook/en/latest/truncate.html
class BaseMixin(object):
    "Base class for cryoweb tables"

    @classmethod
    def truncate(cls):
        """Truncate table"""

        # Django.db.connections is a dictionary-like object that allows you
        # to retrieve a specific connection using its alias
        with connections["default"].cursor() as cursor:
            statement = "TRUNCATE TABLE {0} RESTART IDENTITY CASCADE".format(
                cls._meta.db_table)
            logger.debug(statement)
            cursor.execute(statement)


class BioSampleMixin(BaseMixin):
    """Common methods for animal and samples"""

    def __str__(self):
        return str(self.name)

    @property
    def person(self):
        return self.owner.person

    @property
    def organization(self):
        return self.name.submission.organization

    @property
    def gene_bank_country(self):
        return self.name.submission.gene_bank_country

    def get_attributes(self):
        """Common attribute definition. Attribute name is the name in
        metadata rules"""

        attributes = {}

        attributes["Project"] = format_attribute(
            value="IMAGE")

        attributes['Data source ID'] = format_attribute(
            value=self.name.name)

        attributes['Alternative id'] = format_attribute(
            value=self.alternative_id)

        attributes['Submission title'] = format_attribute(
            value=self.name.submission.title)

        attributes['Person last name'] = format_attribute(
            value=self.owner.last_name)

        attributes['Person email'] = format_attribute(
            value="mailto:%s" % (self.owner.email))

        attributes['Person affiliation'] = format_attribute(
            value=self.owner.person.affiliation.name)

        attributes['Person role'] = self.person.role.format_attribute()

        attributes['Organization name'] = format_attribute(
            value=self.name.submission.organization.name)

        attributes[
            'Organization role'] = self.organization.role.format_attribute()

        attributes['Gene bank name'] = format_attribute(
            value=self.name.submission.gene_bank_name)

        attributes[
            'Gene bank country'] = self.gene_bank_country.format_attribute()

        attributes['Data source type'] = format_attribute(
            value=self.name.submission.get_datasource_type_display())

        attributes['Data source version'] = format_attribute(
            value=self.name.submission.datasource_version)

        return attributes


# --- Abstract classes


# helper classes
class DictBase(BaseMixin, models.Model):
    """Base class for dictionary tables"""

    library_name = None

    # if not defined, this table will have an own primary key
    label = models.CharField(
            max_length=255,
            blank=False,
            help_text="Example: submitter")

    term = models.CharField(
            max_length=255,
            blank=False,
            null=True,
            help_text="Example: EFO_0001741")

    class Meta:
        # Abstract base classes are useful when you want to put some common
        # information into a number of other models
        abstract = True

    def __str__(self):
        return "{label} ({term})".format(
                label=self.label,
                term=self.term)

    def format_attribute(self):
        if self.library_name is None:
            logger.warning("library_name not defined")
            library_uri = OBO_URL

        else:
            library = Ontology.objects.get(library_name=self.library_name)
            library_uri = library.library_uri

        return format_attribute(
            value=self.label,
            obo_url=library_uri,
            terms=self.term)


class Confidence(BaseMixin, models.Model):
    """Add confidence to models"""

    # confidence field (enum)
    confidence = models.SmallIntegerField(
        choices=[x.value for x in CONFIDENCES],
        help_text='example: Manually Curated',
        null=True)

    class Meta:
        # Abstract base classes are useful when you want to put some common
        # information into a number of other models
        abstract = True


# --- database models


class DictRole(DictBase):
    """A class to model roles defined as childs of
    http://www.ebi.ac.uk/efo/EFO_0002012"""

    library_name = 'EFO'

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "role"
        unique_together = (("label", "term"),)


class DictCountry(DictBase, Confidence):
    """A class to model contries defined by Gazetteer
    https://www.ebi.ac.uk/ols/ontologies/gaz"""

    library_name = 'NCIT'

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "country"
        verbose_name_plural = "countries"
        unique_together = (("label", "term"),)


class DictSpecie(DictBase, Confidence):
    """A class to model species defined by NCBI organismal classification
    http://www.ebi.ac.uk/ols/ontologies/ncbitaxon"""

    @property
    def taxon_id(self):
        if not self.term or self.term == '':
            return None

        return int(self.term.split("_")[-1])

    # TODO: fk with Ontology table

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "specie"
        unique_together = (("label", "term"),)

    @classmethod
    def get_by_synonim(cls, synonim, language):
        """return an instance by synonim in supplied language or default one"""

        try:
            specie = cls.objects.get(
                speciesynonim__word=synonim,
                speciesynonim__language__label=language)

        except cls.DoesNotExist:
            specie = cls.objects.get(
                speciesynonim__word=synonim,
                speciesynonim__language__label="United Kingdom")

        return specie


class DictBreed(Confidence):
    # this was the description field in cryoweb v_breeds_species tables
    supplied_breed = models.CharField(max_length=255, blank=False)
    mapped_breed = models.CharField(max_length=255, blank=False, null=True)

    # TODO add Mapped breed ontology library FK To Ontology
#    mapped_breed_ontology_library = models.ForeignKey(
#            'Ontology',
#            db_index=True)

    mapped_breed_term = models.CharField(
            max_length=255,
            blank=False,
            null=True,
            help_text="Example: LBO_0000347")

    # using a constraint for country.
    country = models.ForeignKey(
        'DictCountry',
        on_delete=models.PROTECT)

    # using a constraint for specie
    specie = models.ForeignKey(
        'DictSpecie',
        on_delete=models.PROTECT)

    def __str__(self):
        # return mapped breed if defined
        if self.mapped_breed:
            return str(self.mapped_breed)

        else:
            return str(self.supplied_breed)

    class Meta:
        verbose_name = 'Breed'

        # HINT: would mapped_breed ba a better choice to define a unique key
        # using breed and species? in that case, mapped breed need to have a
        # default value, ex the descricption (supplied_breed)
        unique_together = (("supplied_breed", "specie"),)


class DictSex(DictBase):
    """A class to model sex as defined in PATO"""

    class Meta:
        verbose_name = 'sex'
        verbose_name_plural = 'sex'


class Name(BaseMixin, models.Model):
    """Model UID names: define a name (sample or animal) unique for each
    data submission"""

    # two different animal may have the same name. Its unicity depens on
    # data source name and version
    name = models.CharField(
            max_length=255,
            blank=False,
            null=False)

    submission = models.ForeignKey(
        'Submission',
        db_index=True,
        related_name='name_set',
        on_delete=models.CASCADE)

    # This need to be assigned after submission
    # HINT: this column should be UNIQUE?
    biosample_id = models.CharField(max_length=255, blank=True, null=True)

    # '+' instructs Django that we don’t need this reverse relationship
    owner = models.ForeignKey(
        User,
        related_name='+',
        on_delete=models.CASCADE)

    # a column to track submission status
    status = models.SmallIntegerField(
            choices=[x.value for x in STATUSES if x.name in NAME_STATUSES],
            help_text='example: Submitted',
            default=STATUSES.get_value('loaded'))

    last_changed = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True)

    last_submitted = models.DateTimeField(
        blank=True,
        null=True)

    class Meta:
        unique_together = (("name", "submission"),)

    def __str__(self):
        # HINT: should I return biosampleid if defined?
        return "%s (Submission: %s)" % (self.name, self.submission_id)


class Animal(BioSampleMixin, models.Model):
    # an animal name has a entry in name table
    name = models.OneToOneField(
        'Name',
        on_delete=models.CASCADE)

    # alternative id will store the internal id in data source
    alternative_id = models.CharField(max_length=255, blank=True, null=True)

    description = models.CharField(max_length=255, blank=True, null=True)

    # HINT: link to a term list table?
    material = models.CharField(
        max_length=255,
        default="Organism",
        editable=False,
        null=True)

    breed = models.ForeignKey(
        'DictBreed',
        db_index=True,
        on_delete=models.PROTECT)

    # species is in DictBreed table

    # using a constraint for sex
    sex = models.ForeignKey(
        'DictSex',
        blank=True,
        null=True,
        default=-1,
        on_delete=models.PROTECT)

    # check that father and mother are defined using Foreign Keys
    # HINT: mother and father are not mandatory in all datasource
    father = models.ForeignKey(
        'Name',
        on_delete=models.CASCADE,
        null=True,
        related_name='father_set')

    mother = models.ForeignKey(
        'Name',
        on_delete=models.CASCADE,
        null=True,
        related_name='mother_set')

    # HINT: and birth date?

    # TODO: need to set this value? How?
    birth_location = models.CharField(
        max_length=255,
        blank=True,
        null=True)

    birth_location_latitude = models.FloatField(blank=True, null=True)
    birth_location_longitude = models.FloatField(blank=True, null=True)

    # accuracy field (enum)
    birth_location_accuracy = models.SmallIntegerField(
        choices=[x.value for x in ACCURACIES],
        help_text='example: unknown accuracy level, country level',
        null=False,
        blank=False,
        default=ACCURACIES.get_value('missing'))

    owner = models.ForeignKey(
        User,
        related_name='animals',
        on_delete=models.CASCADE)

    def get_biosample_id(self):
        """Get the biosample id or a temporary name"""

        return self.name.biosample_id or "animal_%s" % (
                self.id)

    def get_attributes(self):
        """Return attributes like biosample needs"""

        attributes = super().get_attributes()

        attributes["Material"] = format_attribute(
            value="organism", terms="OBI_0100026")

        attributes['Species'] = format_attribute(
            value=self.breed.specie.label,
            terms=self.breed.specie.term)

        attributes['Supplied breed'] = format_attribute(
            value=self.breed.supplied_breed)

        attributes[
            'EFABIS Breed country'] = self.breed.country.format_attribute()

        attributes['Sex'] = format_attribute(
            value=self.sex.label,
            terms=self.sex.term)

        attributes["Birth location accuracy"] = format_attribute(
            value=self.get_birth_location_accuracy_display())

        # filter out empty values
        attributes = {k: v for k, v in attributes.items() if v is not None}

        return attributes

    def to_biosample(self, release_date=None):
        """get a json from animal for biosample submission"""

        result = {}

        # define mandatory fields
        result['alias'] = self.get_biosample_id()
        result['title'] = self.name.name

        if release_date:
            result['releaseDate'] = release_date
        else:
            now = timezone.now()
            result['releaseDate'] = str(now.date())

        result['taxonId'] = self.breed.specie.taxon_id

        result['taxon'] = self.breed.specie.label

        # define optinal fields
        if self.description:
            result['description'] = self.description

        # define attributes
        result['attributes'] = self.get_attributes()

        # TODO: define relationship
        result['sampleRelationships'] = []

        return result


class Sample(BioSampleMixin, models.Model):
    # a sample name has a entry in name table
    # this is a One2One foreign key
    name = models.OneToOneField(
        'Name',
        on_delete=models.CASCADE)

    # db_vessel in data source
    alternative_id = models.CharField(max_length=255, blank=True, null=True)

    description = models.CharField(max_length=255, blank=True, null=True)

    # HINT: link to a term list table?
    material = models.CharField(
        max_length=255,
        default="Specimen from Organism",
        editable=False,
        null=True)

    animal = models.ForeignKey(
        'Animal',
        on_delete=models.CASCADE)

    protocol = models.CharField(max_length=255, blank=True, null=True)

    collection_date = models.DateField(blank=True, null=True)
    collection_place_latitude = models.FloatField(blank=True, null=True)
    collection_place_longitude = models.FloatField(blank=True, null=True)
    collection_place = models.CharField(max_length=255, blank=True, null=True)

    # accuracy field (enum)
    collection_place_accuracy = models.SmallIntegerField(
        choices=[x.value for x in ACCURACIES],
        help_text='example: unknown accuracy level, country level',
        null=False,
        blank=False,
        default=ACCURACIES.get_value('missing'))

    # TODO: move those fields to dictionary tables
    organism_part = models.CharField(max_length=255, blank=True, null=True)

    organism_part_term = models.CharField(
            max_length=255,
            blank=False,
            null=True,
            help_text="Example: UBERON_0001968")

    developmental_stage = models.CharField(
            max_length=255,
            blank=True,
            null=True)

    developmental_stage_term = models.CharField(
            max_length=255,
            blank=False,
            null=True,
            help_text="Example: EFO_0001272")

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

    owner = models.ForeignKey(
        User,
        related_name='samples',
        on_delete=models.CASCADE)

    def get_biosample_id(self):
        """Get the biosample id or a temporary name"""

        return self.name.biosample_id or "sample_%s" % (
                self.id)

    def get_attributes(self):
        """Return attributes like biosample needs"""

        attributes = super().get_attributes()

        attributes["Material"] = format_attribute(
            value="specimen from organism", terms="OBI_0001479")

        attributes['Species'] = format_attribute(
            value=self.animal.breed.specie.label,
            terms=self.animal.breed.specie.term)

        # HINT: this won't to be a biosample id in the first submission.
        # How to fix it? can be removed from mandatory attributes
        attributes['Derived from'] = format_attribute(
            value=self.animal.name.name)

        attributes['Collection date'] = format_attribute(
            value=str(self.collection_date), units="YYYY-MM-DD")

        attributes['Collection place'] = format_attribute(
            value=self.collection_place)

        # TODO: this will point to a correct term dictionary table
        attributes['Organism part'] = format_attribute(
            value=self.organism_part,
            terms=self.organism_part_term)

        attributes["Collection place accuracy"] = format_attribute(
            value=self.get_collection_place_accuracy_display())

        # filter out empty values
        attributes = {k: v for k, v in attributes.items() if v is not None}

        return attributes

    def to_biosample(self, release_date=None):
        """get a json from sample for biosample submission"""

        result = {}

        # define mandatory fields
        result['alias'] = self.get_biosample_id()
        result['title'] = self.name.name

        if release_date:
            result['releaseDate'] = release_date
        else:
            now = timezone.now()
            result['releaseDate'] = str(now.date())

        result['taxonId'] = self.animal.breed.specie.taxon_id

        result['taxon'] = self.animal.breed.specie.label

        # define optinal fields
        if self.description:
            result['description'] = self.description

        # define attributes
        result['attributes'] = self.get_attributes()

        # define relationship
        result['sampleRelationships'] = [{
            "alias": self.animal.get_biosample_id(),
            "relationshipNature": "derived from",
        }]

        return result


class Person(BaseMixin, models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    initials = models.CharField(max_length=255, blank=True, null=True)

    # HINT: with a OneToOneField relation, there will be only one user for
    # each organization
    affiliation = models.ForeignKey(
        'Organization',
        null=True,
        on_delete=models.PROTECT,
        help_text="The institution you belong to")

    # last_name, first_name and email come from User model

    role = models.ForeignKey(
        'DictRole',
        on_delete=models.PROTECT,
        null=True)

    def __str__(self):
        return "{name} {surname} ({affiliation})".format(
                name=self.user.first_name,
                surname=self.user.last_name,
                affiliation=self.affiliation)


class Organization(BaseMixin, models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    name = models.CharField(max_length=255)
    address = models.CharField(
        max_length=255, blank=True, null=True,
        help_text='One line, comma separated')

    country = models.ForeignKey(
        'DictCountry',
        on_delete=models.PROTECT)

    URI = models.URLField(
        max_length=500, blank=True, null=True,
        help_text='Web site')

    role = models.ForeignKey(
        'DictRole',
        on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class Publication(BaseMixin, models.Model):
    submission = models.ForeignKey(
        'Submission',
        db_index=True,
        related_name='publications',
        on_delete=models.CASCADE)

    # this is a non mandatory fields in ruleset
    doi = models.CharField(
        max_length=255,
        help_text='Valid Digital Object Identifier')

    def __str__(self):
        return self.doi


# HINT: do I need this table?
class Ontology(BaseMixin, models.Model):
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


class Submission(BaseMixin, models.Model):
    title = models.CharField(
        "Submission title",
        max_length=255,
        help_text='Example: Roslin Sheep Atlas')

    project = models.CharField(
        max_length=25,
        default="IMAGE",
        editable=False)

    description = models.CharField(
        max_length=255,
        help_text='Example: The Roslin Institute ' +
                  'Sheep Gene Expression Atlas Project')

    # gene bank fields
    gene_bank_name = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        help_text='example: CryoWeb')

    gene_bank_country = models.ForeignKey(
        'DictCountry',
        on_delete=models.PROTECT)

    # 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
    class TYPES(Enum):
        cryoweb = (0, 'CryoWeb')
        template = (1, 'Template')
        crb_anim = (2, 'CRB-Anim')

        @classmethod
        def get_value(cls, member):
            return cls[member].value[0]

    # datasource field
    datasource_type = models.SmallIntegerField(
        choices=[x.value for x in TYPES],
        help_text='example: CryoWeb')

    datasource_version = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        help_text='examples: "2018-04-27", "version 1.5"')

    # HINT: can this field be NULL?
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.PROTECT,
        help_text="Who owns the data")

    # custom fields for datasource
    upload_dir = 'data_source/'

    # File will be stored to PROTECTED_MEDIA_ROOT + upload_to
    # https://gist.github.com/cobusc/ea1d01611ef05dacb0f33307e292abf4
    uploaded_file = ProtectedFileField(upload_to=upload_dir)

    # when submission is created
    created_at = models.DateTimeField(auto_now_add=True)

    # TODO: add a field for last update

    # a column to track submission status
    status = models.SmallIntegerField(
            choices=[x.value for x in STATUSES],
            help_text='example: Waiting',
            default=STATUSES.get_value('waiting'))

    # a field to track errors in UID loading. Should be blank if no errors
    # are found
    message = models.TextField(
        null=True,
        blank=True)

    # track biosample submission id in a field
    # HINT: if I update a completed submision, shuold I track the
    # last submission id?
    biosample_submission_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        unique=True,
        help_text='Biosample submission id')

    owner = models.ForeignKey(
        User,
        related_name='submissions',
        on_delete=models.CASCADE)

    class Meta:
        # HINT: can I put two files for my cryoweb instance? May they have two
        # different version
        unique_together = ((
            "gene_bank_name",
            "gene_bank_country",
            "datasource_type",
            "datasource_version"),)

    def __str__(self):
        return "%s (%s, %s)" % (
            self.gene_bank_name,
            self.gene_bank_country.label,
            self.datasource_version
        )

    def get_uploaded_file_basename(self):
        return os.path.basename(self.uploaded_file.name)

    def get_uploaded_file_path(self):
        """Return uploaded file path in docker container"""

        # this is the full path in docker container
        fullpath = self.uploaded_file.file

        # get a string and quote fullpath
        return shlex.quote(str(fullpath))

    def get_absolute_url(self):
        return reverse("submissions:detail", kwargs={"pk": self.pk})


# --- Custom functions


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


# A method to truncate database
def truncate_database():
    """Truncate image database"""

    logger.warning("Truncating ALL image tables")

    # call each class and truncate its table by calling truncate method
    Animal.truncate()
    DictBreed.truncate()
    DictCountry.truncate()
    DictRole.truncate()
    DictSex.truncate()
    DictSpecie.truncate()
    Name.truncate()
    Ontology.truncate()
    Organization.truncate()
    Person.truncate()
    Publication.truncate()
    Sample.truncate()
    Submission.truncate()

    logger.warning("All cryoweb tables were truncated")


def truncate_filled_tables():
    """Truncate filled tables by import processes"""

    logger.warning("Truncating filled tables tables")

    # call each class and truncate its table by calling truncate method
    Animal.truncate()
    DictBreed.truncate()
    DictSpecie.truncate()
    Name.truncate()
    Publication.truncate()
    Sample.truncate()
    Submission.truncate()

    logger.warning("All filled tables were truncated")


def uid_report(user):
    """Performs a statistic on UID database to find issues. require user as
    request.user"""

    report = {}

    # get n_of_animals
    report['n_of_animals'] = Animal.objects.filter(
        owner=user).count()

    # get n_of_samples
    report['n_of_samples'] = Sample.objects.filter(
        owner=user).count()

    # HINT: have they sense in a per user statistic?

    # check breeds without ontologies
    breed = DictBreed.objects.filter(mapped_breed_term=None)
    report['breeds_without_ontology'] = breed.count()

    # check countries without ontology
    country = DictCountry.objects.filter(term=None)
    report['countries_without_ontology'] = country.count()

    # check species without ontology
    species = DictSpecie.objects.filter(term=None)
    report['species_without_ontology'] = species.count()

    return report


# A method to discover is image database has data or not
def db_has_data():
    # Test only tables I read data to fill UID
    if (Animal.objects.exists() or Sample.objects.exists() or
            Name.objects.exists()):
        return True

    else:
        return False
