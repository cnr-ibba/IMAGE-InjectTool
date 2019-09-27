
import logging
import os
import shlex

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Func, Value, F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from common.fields import ProtectedFileField
from common.constants import (
    OBO_URL, STATUSES, CONFIDENCES, NAME_STATUSES, ACCURACIES, WAITING, LOADED,
    MISSING, DATA_TYPES, TIME_UNITS, SAMPLE_STORAGE, SAMPLE_STORAGE_PROCESSING)
from common.helpers import format_attribute

from .mixins import BaseMixin, BioSampleMixin

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Replace(Func):
    function = 'REPLACE'


# --- Abstract classes


# helper classes
class DictBase(BaseMixin, models.Model):
    """
    Abstract class to be inherited to all dictionary tables. It models fields
    like ``label`` (the revised term like submitter or blood) and
    ``term`` (the ontology id as the final part of the URI link)

    The fixed part of the URI could be customized from :py:class:`Ontology`
    by setting ``library_name`` class attribute accordingly::

        class DictRole(DictBase):
            library_name = 'EFO'
    """

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
        """
        Format an object instance as a dictionary used by biosample, for
        example::

            [{
                'value': 'submitter',
                'terms': [{'url': 'http://www.ebi.ac.uk/efo/EFO_0001741'}]
            }]

        the fixed part of URI link is defined by ``library_name`` class
        attribute
        """

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
    """
    Abstract class which add :ref:`confidence <Common confidences>`
    to models
    """

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


class DictDevelStage(DictBase, Confidence):
    """A class to developmental stages defined as descendants of
    descendants of EFO_0000399"""

    library_name = 'EFO'

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "developmental stage"
        unique_together = (("label", "term"),)


class DictPhysioStage(DictBase, Confidence):
    """A class to physiological stages defined as descendants of
    descendants of PATO_0000261"""

    library_name = 'PATO'

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "physiological stage"
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

    @classmethod
    def get_specie_check_synonyms(cls, species_label, language):
        """get a DictSpecie object. Species are in latin names, but I can
        find also a common name in translation tables"""

        try:
            specie = cls.objects.get(label=species_label)

        except cls.DoesNotExist:
            logger.info("Search %s in %s synonyms" % (species_label, language))
            # search for language synonym (if I arrived here a synonym should
            # exists)
            specie = cls.get_by_synonym(
                synonym=species_label,
                language=language)

        return specie


class DictBreed(Confidence):
    """A class to deal with breed objects and their ontologies"""

    library_name = "LBO"

    # this was the description field in cryoweb v_breeds_species tables
    supplied_breed = models.CharField(max_length=255, blank=False)

    # those can't be null like other DictBase classes
    # HINT: if every breed should have a mapped breed referring a specie
    # at least, could I inherit from DictBase class?
    label = models.CharField(max_length=255, blank=False, null=True)

    # old mapped_breed_term
    term = models.CharField(
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
        verbose_name = 'breed'
        unique_together = (("supplied_breed", "specie", "country"),)

    def __str__(self):
        return "{supplied} ({mapped}, {specie})".format(
            supplied=self.supplied_breed,
            mapped=self.mapped_breed,
            specie=self.specie.label)

    @property
    def mapped_breed(self):
        """Alias for label attribute"""

        return self.label

    @mapped_breed.setter
    def mapped_breed(self, label):
        """Alias for label attribute"""

        self.label = label

    @property
    def mapped_breed_term(self):
        """Alias for term attribute"""

        return self.term

    @mapped_breed_term.setter
    def mapped_breed_term(self, term):
        """Alias for label attribute"""

        self.term = term

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
        blank=True,
        related_name='name_set',
        on_delete=models.SET_NULL)

    class Meta:
        unique_together = (("name", "submission"),)

    def __str__(self):
        # HINT: should I return biosampleid if defined?
        return "%s (Submission: %s)" % (self.name, self.submission_id)


class Animal(BioSampleMixin, models.Model):
    """
    Class to model Animal (Organism). Inherits from :py:class:`BioSampleMixin`,
    related to :py:class:`Name` through ``OneToOne`` relationship to model
    Animal name (Data source id), and with the same relationship to model
    ``mother`` and ``father`` of such animal. In case that parents are unknown,
    could be linked with Unkwnon animals for cryoweb data or doens't have
    relationship.Linked to :py:class:`DictBreed` dictionary
    table to model info on species and breed. Linked to
    :py:class:`Sample` to model Samples (Specimen from organims)::

        from image_app.models import Animal

        # get animal using primary key
        animal = Animal.objects.get(pk=1)

        # get animal name
        data_source_id = animal.name.name

        # get animal's parents
        mother = animal.mother
        father = animal.father

        # get breed and species info
        print(animal.breed.supplied_breed)
        print(animal.breed.specie.label)

        # get all samples (specimen) for this animals
        samples = animal.sample_set.all()
    """

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

    def get_relationship(self):
        """Get a relationship to this animal (call this method from a related
        object to get a connection to this element)"""

        # if animal is already uploaded I will use accession as
        # relationship key. This biosample id could be tested in validation
        if self.biosample_id and self.biosample_id != '':
            return {
                "accession": self.biosample_id,
                "relationshipNature": "derived from",
            }
        else:
            return {
                "alias": self.biosample_alias,
                "relationshipNature": "derived from",
            }

    def get_father_relationship(self):
        """Get a relationship with father if possible"""

        # get father of this animal
        if self.father is None:
            return None

        # cryoweb could have unkwown animals. They are Names without
        # relationships with Animal table
        if not hasattr(self.father, "animal"):
            return None

        else:
            return self.father.animal.get_relationship()

    def get_mother_relationship(self):
        """Get a relationship with mother if possible"""

        # get mother of this animal
        if self.mother is None:
            return None

        # cryoweb could have unkwown animals. They are Names without
        # relationships with Animal table
        if not hasattr(self.mother, "animal"):
            return None

        else:
            return self.mother.animal.get_relationship()

    def to_biosample(self, release_date=None):
        """get a json from animal for biosample submission"""

        # call methods defined in BioSampleMixin and get result
        # with USI mandatory keys and attributes
        result = super().to_biosample(release_date)

        # define relationship with mother and father (if possible)
        result['sampleRelationships'] = []

        father_relationship = self.get_father_relationship()

        if father_relationship is not None:
            result['sampleRelationships'].append(father_relationship)

        mother_relationship = self.get_mother_relationship()

        if mother_relationship is not None:
            result['sampleRelationships'].append(mother_relationship)

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

    # HINT: should this be a protocol?
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

    # using a constraint for developmental stage (DictDevelStage)
    developmental_stage = models.ForeignKey(
        'DictDevelStage',
        null=True,
        blank=True,
        on_delete=models.PROTECT)

    physiological_stage = models.ForeignKey(
        'DictPhysioStage',
        null=True,
        blank=True,
        on_delete=models.PROTECT)

    animal_age_at_collection = models.IntegerField(
        null=True,
        blank=True)

    animal_age_at_collection_units = models.SmallIntegerField(
        choices=[x.value for x in TIME_UNITS],
        help_text='example: years',
        null=True,
        blank=True)

    availability = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=(
            "Either a link to a web page giving information on who to contact "
            "or an e-mail address to contact about availability. If neither "
            "available, please use the value no longer available")
    )

    storage = models.SmallIntegerField(
        choices=[x.value for x in SAMPLE_STORAGE],
        help_text='How the sample was stored',
        null=True,
        blank=True)

    storage_processing = models.SmallIntegerField(
        choices=[x.value for x in SAMPLE_STORAGE_PROCESSING],
        help_text='How the sample was prepared for storage',
        null=True,
        blank=True)

    preparation_interval = models.IntegerField(
        blank=True,
        null=True)

    preparation_interval_units = models.SmallIntegerField(
        choices=[x.value for x in TIME_UNITS],
        help_text='example: years',
        null=True,
        blank=True)

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

        attributes["Specimen collection protocol"] = format_attribute(
            value=self.protocol)

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

        if self.physiological_stage:
            attributes['Physiological stage'] = \
                self.physiological_stage.format_attribute()

        attributes['Animal age at collection'] = format_attribute(
            value=self.animal_age_at_collection,
            units=self.get_animal_age_at_collection_units_display())

        attributes['Availability'] = format_attribute(
            value=self.availability)

        attributes['Sample storage'] = format_attribute(
            value=self.get_storage_display())

        attributes['Sample storage processing'] = format_attribute(
            value=self.get_storage_processing_display())

        attributes['Sampling to preparation interval'] = format_attribute(
            value=self.preparation_interval,
            units=self.get_preparation_interval_units_display())

        # filter out empty values
        attributes = {k: v for k, v in attributes.items() if v is not None}

        return attributes

    def to_biosample(self, release_date=None):
        """get a json from sample for biosample submission"""

        # call methods defined in BioSampleMixin and get result
        # with USI mandatory keys and attributes
        result = super().to_biosample(release_date)

        # define relationship to the animal where this sample come from
        result['sampleRelationships'] = [self.animal.get_relationship()]

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
    DictDevelStage.truncate()
    DictPhysioStage.truncate()
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

    # merging dictionaries: https://stackoverflow.com/a/26853961
    # HINT: have they sense in a per user statistic?
    report = {**report, **missing_terms()}

    return report


def missing_terms():
    """Get informations about dictionary terms without ontologies"""

    # a list with all dictionary classes
    dict_classes = [
        DictBreed, DictCountry, DictSpecie, DictUberon, DictDevelStage,
        DictPhysioStage
    ]

    # get a dictionary to report data
    report = {}

    for dict_class in dict_classes:
        # get a queryset with missing terms
        missing = dict_class.objects.filter(term=None)

        # ket a key for report dictionary
        key = "%s_without_ontology" % (
            dict_class._meta.verbose_name_plural.replace(" ", "_"))

        # track counts
        report[key] = missing.count()

    return report


# A method to discover is image database has data or not
def db_has_data():
    # Test only tables I read data to fill UID
    if (Animal.objects.exists() or Sample.objects.exists() or
            Name.objects.exists()):
        return True

    else:
        return False
