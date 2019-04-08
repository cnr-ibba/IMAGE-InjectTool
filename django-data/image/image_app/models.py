
import logging
import os
import shlex

from django.contrib.auth.models import User
from django.db import connections, models
from django.db.models import Func, Value, F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from common.fields import ProtectedFileField
from common.constants import (
    OBO_URL, STATUSES, CONFIDENCES, NAME_STATUSES, ACCURACIES, WAITING, LOADED,
    MISSING, DATA_TYPES, TIME_UNITS)

from .helpers import format_attribute

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Replace(Func):
    function = 'REPLACE'


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

    @property
    def gene_bank_name(self):
        return self.name.submission.gene_bank_name

    @property
    def data_source_id(self):
        return self.name.name

    @property
    def submission(self):
        return self.name.submission

    @property
    def specie(self):
        raise NotImplementedError(
            "You need to define this method in your class")

    def get_biosample_id(self):
        """Get the biosample id or a temporary name"""

        return self.name.biosample_id or self.biosample_alias

    def get_attributes(self):
        """Common attribute definition. Attribute name is the name in
        metadata rules"""

        attributes = {}

        attributes['Data source ID'] = format_attribute(
            value=self.data_source_id)

        attributes['Alternative id'] = format_attribute(
            value=self.alternative_id)

        # HINT: this is a mandatory biosample field: could be removed from
        # attributes?
        attributes['Description'] = format_attribute(
            value=self.description)

        attributes["Project"] = format_attribute(
            value="IMAGE")

        attributes['Submission title'] = format_attribute(
            value=self.submission.title)

        attributes['Submission description'] = format_attribute(
            value=self.submission.description)

        attributes['Person last name'] = format_attribute(
            value=self.owner.last_name)

        attributes['Person initial'] = format_attribute(
            value=self.person.initials)

        attributes['Person first name'] = format_attribute(
            value=self.owner.first_name)

        attributes['Person email'] = format_attribute(
            value="mailto:%s" % (self.owner.email))

        attributes['Person affiliation'] = format_attribute(
            value=self.person.affiliation.name)

        attributes['Person role'] = self.person.role.format_attribute()

        attributes['Organization name'] = format_attribute(
            value=self.organization.name)

        attributes['Organization address'] = format_attribute(
            value=self.organization.address)

        attributes['Organization uri'] = format_attribute(
            value=self.organization.URI)

        attributes['Organization country'] = \
            self.organization.country.format_attribute()

        attributes[
            'Organization role'] = self.organization.role.format_attribute()

        # this could be present or not
        if self.name.publication:
            attributes['Publication DOI'] = format_attribute(
                value=self.name.publication.doi)

        attributes['Gene bank name'] = format_attribute(
            value=self.gene_bank_name)

        attributes[
            'Gene bank country'] = self.gene_bank_country.format_attribute()

        attributes['Data source type'] = format_attribute(
            value=self.submission.get_datasource_type_display())

        attributes['Data source version'] = format_attribute(
            value=self.submission.datasource_version)

        attributes['Species'] = self.specie.format_attribute()

        return attributes

    def __can_I(self, names):
        """Return True id self.status in statuses"""

        statuses = [x.value[0] for x in STATUSES if x.name in names]

        if self.submission.status not in statuses:
            return True

        else:
            return False

    def can_edit(self):
        """Returns True if I can edit a sample/animal"""

        names = ['waiting', 'submitted']

        return self.__can_I(names)

    def can_delete(self):
        """Returns True if I can delete a sample/animal"""

        names = ['waiting', 'submitted']

        return self.__can_I(names)


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
            library_uri=library_uri,
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


# --- dictionary tables


class DictRole(DictBase):
    """A class to model roles defined as childs of
    http://www.ebi.ac.uk/efo/EFO_0002012"""

    library_name = 'EFO'

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "role"
        unique_together = (("label", "term"),)


class DictCountry(DictBase, Confidence):
    """A class to model contries defined by NCI Thesaurus OBO Edition
    https://www.ebi.ac.uk/ols/ontologies/ncit"""

    library_name = 'NCIT'

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "country"
        verbose_name_plural = "countries"
        unique_together = (("label", "term"),)
        ordering = ['label']


class DictSex(DictBase):
    """A class to model sex as defined in PATO"""

    library_name = "PATO"

    class Meta:
        verbose_name = 'sex'
        verbose_name_plural = 'sex'
        unique_together = (("label", "term"),)


class DictUberon(DictBase, Confidence):
    """A class to model anatomies modeled in uberon"""

    library_name = "UBERON"

    class Meta:
        verbose_name = 'organism part'
        unique_together = (("label", "term"),)


class DictStage(DictBase, Confidence):
    """A class to developmental stages defined as descendants of
    descendants of EFO_0000399"""

    library_name = 'EFO'

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "developmental stage"
        unique_together = (("label", "term"),)


class DictSpecie(DictBase, Confidence):
    """A class to model species defined by NCBI organismal classification
    http://www.ebi.ac.uk/ols/ontologies/ncbitaxon"""

    library_name = "NCBITaxon"

    @property
    def taxon_id(self):
        if not self.term or self.term == '':
            return None

        return int(self.term.split("_")[-1])

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "specie"
        unique_together = (("label", "term"),)

    @classmethod
    def get_by_synonym(cls, synonym, language):
        """return an instance by synonym in supplied language or default one"""

        # get a queryset with speciesynonym
        qs = cls.objects.prefetch_related('speciesynonym_set')

        # annotate queryset by removing spaces from speciesynonym word
        qs = qs.annotate(
            new_word=Replace('speciesynonym__word', Value(" "), Value("")),
            language=F('speciesynonym__language__label'))

        # now remove spaces from synonym
        synonym = synonym.replace(" ", "")

        try:
            specie = qs.get(
                new_word=synonym,
                language=language)

        except cls.DoesNotExist:
            specie = qs.get(
                new_word=synonym,
                language="United Kingdom")

        return specie


class DictBreed(Confidence):
    """A class to deal with breed objects and their ontologies"""

    library_name = "LBO"

    # this was the description field in cryoweb v_breeds_species tables
    supplied_breed = models.CharField(max_length=255, blank=False)
    mapped_breed = models.CharField(max_length=255, blank=False, null=True)

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

    class Meta:
        verbose_name = 'Breed'
        unique_together = (("supplied_breed", "specie", "country"),)

    def __str__(self):
        return "{supplied} ({mapped}, {specie})".format(
            supplied=self.supplied_breed,
            mapped=self.mapped_breed,
            specie=self.specie.label)

    def format_attribute(self):
        """Format mapped_breed attribute (with its ontology). Return None if
        no mapped_breed"""

        if not self.mapped_breed or not self.mapped_breed_term:
            return None

        library = Ontology.objects.get(library_name=self.library_name)
        library_uri = library.library_uri

        return format_attribute(
            value=self.mapped_breed,
            library_uri=library_uri,
            terms=self.mapped_breed_term)


# --- Other tables tables


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
            default=LOADED)

    last_changed = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True)

    last_submitted = models.DateTimeField(
        blank=True,
        null=True)

    publication = models.ForeignKey(
        'Publication',
        null=True,
        related_name='name_set',
        on_delete=models.SET_NULL)

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
        editable=False)

    breed = models.ForeignKey(
        'DictBreed',
        db_index=True,
        on_delete=models.PROTECT)

    # species is in DictBreed table

    # using a constraint for sex
    sex = models.ForeignKey(
        'DictSex',
        null=True,
        on_delete=models.PROTECT)

    # check that father and mother are defined using Foreign Keys
    # HINT: mother and father are not mandatory in all datasource
    father = models.ForeignKey(
        'Name',
        on_delete=models.CASCADE,
        null=True,
        related_name='father_of')

    mother = models.ForeignKey(
        'Name',
        on_delete=models.CASCADE,
        null=True,
        related_name='mother_of')

    birth_date = models.DateField(
        blank=True,
        null=True,
        help_text='example: 2019-04-01')

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
        default=MISSING)

    owner = models.ForeignKey(
        User,
        related_name='animals',
        on_delete=models.CASCADE)

    @property
    def specie(self):
        return self.breed.specie

    @property
    def biosample_alias(self):
        return 'IMAGEA{0:09d}'.format(self.id)

    def get_attributes(self):
        """Return attributes like biosample needs"""

        attributes = super().get_attributes()

        attributes["Material"] = format_attribute(
            value="organism", terms="OBI_0100026")

        # TODO: how to model derived from (mother/father)?

        attributes['Supplied breed'] = format_attribute(
            value=self.breed.supplied_breed)

        # HINT: Ideally, I could retrieve an ontology id for countries
        attributes['EFABIS Breed country'] = format_attribute(
            value=self.breed.country.label)

        attributes['Mapped breed'] = self.breed.format_attribute()

        attributes['Sex'] = self.sex.format_attribute()

        # a datetime object should be not be converted in string here,
        # otherwise will not be filtered if NULL
        attributes['Birth date'] = format_attribute(
            value=self.birth_date, units="YYYY-MM-DD")

        attributes["Birth location"] = format_attribute(
            value=self.birth_location)

        attributes["Birth location longitude"] = format_attribute(
            value=self.birth_location_longitude,
            units="decimal degrees")

        attributes["Birth location latitude"] = format_attribute(
            value=self.birth_location_latitude,
            units="decimal degrees")

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

        result['taxonId'] = self.specie.taxon_id

        result['taxon'] = self.specie.label

        # define optinal fields
        if self.description:
            result['description'] = self.description

        # define attributes
        result['attributes'] = self.get_attributes()

        # TODO: define relationship
        result['sampleRelationships'] = []

        return result

    def get_absolute_url(self):
        return reverse("animals:detail", kwargs={"pk": self.pk})


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
        editable=False)

    animal = models.ForeignKey(
        'Animal',
        on_delete=models.CASCADE)

    protocol = models.CharField(max_length=255, blank=True, null=True)

    collection_date = models.DateField(
        blank=True,
        null=True,
        help_text='example: 2019-04-01')
    collection_place_latitude = models.FloatField(blank=True, null=True)
    collection_place_longitude = models.FloatField(blank=True, null=True)
    collection_place = models.CharField(max_length=255, blank=True, null=True)

    # accuracy field (enum)
    collection_place_accuracy = models.SmallIntegerField(
        choices=[x.value for x in ACCURACIES],
        help_text='example: unknown accuracy level, country level',
        null=False,
        blank=False,
        default=MISSING)

    # using a constraint for organism (DictUberon)
    organism_part = models.ForeignKey(
        'DictUberon',
        null=True,
        on_delete=models.PROTECT)

    # using a constraint for developmental stage (DictStage)
    developmental_stage = models.ForeignKey(
        'DictStage',
        null=True,
        blank=True,
        on_delete=models.PROTECT)

    physiological_stage = models.CharField(
            max_length=255,
            blank=True,
            null=True)

    animal_age_at_collection = models.IntegerField(
        null=True,
        blank=True)

    animal_age_at_collection_units = models.SmallIntegerField(
        choices=[x.value for x in TIME_UNITS],
        help_text='example: years',
        null=True,
        blank=True)

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

    @property
    def specie(self):
        return self.animal.breed.specie

    @property
    def biosample_alias(self):
        return 'IMAGES{0:09d}'.format(self.id)

    def get_attributes(self):
        """Return attributes like biosample needs"""

        attributes = super().get_attributes()

        attributes["Material"] = format_attribute(
            value="specimen from organism", terms="OBI_0001479")

        # The data source id or alternative id of the animal from which
        # the sample was collected (see Animal.to_biosample())
        attributes['Derived from'] = format_attribute(
            value=self.animal.name.name)

        # a datetime object should be not be converted in string here,
        # otherwise will not be filtered if NULL
        attributes['Collection date'] = format_attribute(
            value=self.collection_date, units="YYYY-MM-DD")

        attributes['Collection place'] = format_attribute(
            value=self.collection_place)

        attributes["Collection place longitude"] = format_attribute(
            value=self.collection_place_longitude,
            units="decimal degrees")

        attributes["Collection place latitude"] = format_attribute(
            value=self.collection_place_latitude,
            units="decimal degrees")

        attributes["Collection place accuracy"] = format_attribute(
            value=self.get_collection_place_accuracy_display())

        # this will point to a correct term dictionary table
        if self.organism_part:
            attributes['Organism part'] = self.organism_part.format_attribute()

        if self.developmental_stage:
            attributes['Developmental stage'] = \
                self.developmental_stage.format_attribute()

        attributes['Physiological stage'] = format_attribute(
            value=self.physiological_stage)

        attributes['Animal age at collection'] = format_attribute(
            value=self.animal_age_at_collection,
            units=self.get_animal_age_at_collection_units_display())

        attributes['Availability'] = format_attribute(
            value=self.availability)

        attributes['Sample storage'] = format_attribute(
            value=self.storage)

        attributes['Sample storage processing'] = format_attribute(
            value=self.storage_processing)

        attributes['Sampling to preparation interval'] = format_attribute(
            value=self.preparation_interval)

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

        result['taxonId'] = self.specie.taxon_id

        result['taxon'] = self.specie.label

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

    def get_absolute_url(self):
        return reverse("samples:detail", kwargs={"pk": self.pk})


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
        return "%s (%s)" % (self.name, self.country.label)

    class Meta:
        ordering = ['name', 'country']


class Publication(BaseMixin, models.Model):
    # this is a non mandatory fields in ruleset
    doi = models.CharField(
        max_length=255,
        help_text='Valid Digital Object Identifier')

    def __str__(self):
        return self.doi


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

    # datasource field
    datasource_type = models.SmallIntegerField(
        "Data source type",
        choices=[x.value for x in DATA_TYPES],
        help_text='example: CryoWeb')

    datasource_version = models.CharField(
        "Data source version",
        max_length=255,
        blank=False,
        null=False,
        help_text='examples: "2018-04-27", "version 1.5"')

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

    # https://simpleisbetterthancomplex.com/tips/2016/05/23/django-tip-4-automatic-datetime-fields.html
    updated_at = models.DateTimeField(auto_now=True)

    # a column to track submission status
    status = models.SmallIntegerField(
            choices=[x.value for x in STATUSES],
            help_text='example: Waiting',
            default=WAITING)

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
            "datasource_version",
            "owner"),)

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

    def __can_I(self, names):
        """Return True id self.status in statuses"""

        statuses = [x.value[0] for x in STATUSES if x.name in names]

        if self.status not in statuses:
            return True

        else:
            return False

    def can_edit(self):
        """Returns True if I can edit a submission"""

        names = ['waiting', 'submitted']

        return self.__can_I(names)

    def can_validate(self):
        names = ['error', 'waiting', 'submitted', 'completed']

        return self.__can_I(names)

    def can_submit(self):
        names = ['ready']

        # this is the opposite of self.__can_I
        statuses = [x.value[0] for x in STATUSES if x.name in names]

        # self.status need to be in statuses for submitting
        if self.status in statuses:
            return True

        else:
            return False


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
    DictUberon.truncate()
    DictStage.truncate()
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
