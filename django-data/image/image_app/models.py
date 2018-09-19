
import os
import datetime
from enum import Enum

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from .constants import OBO_URL
from .helpers import format_attribute


# helper classes
class DictMixin():
    """Base class for dictionary tables"""

    def __str__(self):
        return "{label} ({term})".format(
                label=self.label,
                term=self.term)

    def to_validation(self):
        biosample = dict(text=self.label)

        if self.term:
            biosample["ontologyTerms"] = "/".join([
                OBO_URL,
                self.term]
            )

        return biosample


class DictRole(DictMixin, models.Model):
    """A class to model roles defined as childs of
    http://www.ebi.ac.uk/efo/EFO_0002012"""

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

    # TODO: fk with Ontology table

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "role"
        unique_together = (("label", "term"),)


class DictCountry(DictMixin, models.Model):
    """A class to model contries defined by Gazetteer
    https://www.ebi.ac.uk/ols/ontologies/gaz"""

    # if not defined, this table will have an own primary key
    label = models.CharField(
            max_length=255,
            blank=False,
            help_text="Example: Germany")

    term = models.CharField(
            max_length=255,
            blank=False,
            null=True,
            help_text="Example: GAZ_00002646")

    # 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
    class CONFIDENCE(Enum):
        high = (0, 'High')
        good = (1, 'Good')
        medium = (2, 'Medium')
        low = (3, 'Low')
        curated = (4, 'Manually Curated')

        @classmethod
        def get_value(cls, member):
            return cls[member].value[0]

    # confidence field (enum)
    confidence = models.SmallIntegerField(
        choices=[x.value for x in CONFIDENCE],
        help_text='example: Manually Curated',
        null=True)

    # TODO: fk with Ontology table

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "country"
        verbose_name_plural = "countries"
        unique_together = (("label", "term"),)


class DictSpecie(DictMixin, models.Model):
    """A class to model species defined by NCBI organismal classification
    http://www.ebi.ac.uk/ols/ontologies/ncbitaxon"""

    # if not defined, this table will have an own primary key
    label = models.CharField(
        max_length=255,
        blank=False,
        help_text="Example: Sus scrofa")

    @property
    def taxon_id(self):
        if not self.term or self.term == '':
            return None

        return int(self.term.split("_")[-1])

    term = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Example: NCBITaxon_9823")

    # 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
    class CONFIDENCE(Enum):
        high = (0, 'High')
        good = (1, 'Good')
        medium = (2, 'Medium')
        low = (3, 'Low')
        curated = (4, 'Manually Curated')

        @classmethod
        def get_value(cls, member):
            return cls[member].value[0]

    # confidence field (enum)
    confidence = models.SmallIntegerField(
        choices=[x.value for x in CONFIDENCE],
        help_text='example: Manually Curated',
        null=True)

    # TODO: fk with Ontology table

    class Meta:
        # db_table will be <app_name>_<classname>
        verbose_name = "specie"
        unique_together = (("label", "term"),)

    @classmethod
    def get_by_synonim(cls, synonim, language):
        # return an object
        return cls.objects.get(
            speciesynonim__word=synonim,
            speciesynonim__language__label=language)


class DictBreed(models.Model):
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

    # 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
    class CONFIDENCE(Enum):
        high = (0, 'High')
        good = (1, 'Good')
        medium = (2, 'Medium')
        low = (3, 'Low')
        curated = (4, 'Manually Curated')

        @classmethod
        def get_value(cls, member):
            return cls[member].value[0]

    # confidence field (enum)
    confidence = models.SmallIntegerField(
        choices=[x.value for x in CONFIDENCE],
        help_text='example: Manually Curated',
        null=True)

    # using a constraint for country.
    country = models.ForeignKey('DictCountry')

    # using a constraint for specie
    specie = models.ForeignKey('DictSpecie')

    def __str__(self):
        # return mapped breed if defined
        if self.mapped_breed:
            return str(self.mapped_breed)

        else:
            return str(self.supplied_breed)

    def to_validation(self):
        result = {}

        result['suppliedBreed'] = self.supplied_breed

        # Add mapped breed and its term if I have them
        if self.mapped_breed and self.mapped_breed_term:
            result['mappedBreed'] = {
                    'text': self.mapped_breed,
                    'ontologyTerms': "/".join([
                        OBO_URL,
                        self.mapped_breed_term]
                    ),
            }

        result['country'] = self.country.to_validation()
        return result

    class Meta:
        verbose_name = 'Breed'

        # HINT: would mapped_breed ba a better choice to define a unique key
        # using breed and species? in that case, mapped breed need to have a
        # default value, ex the descricption (supplied_breed)
        unique_together = (("supplied_breed", "specie"),)


class DictSex(DictMixin, models.Model):
    """A class to model sex as defined in PATO"""

    label = models.CharField(
            max_length=255,
            blank=False,
            unique=True,
            help_text="Example: male")

    term = models.CharField(
            max_length=255,
            blank=False,
            null=True,
            help_text="Example: PATO_0000384")

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

    submission = models.ForeignKey(
            'Submission',
            db_index=True,
            related_name='name_set')

    # This need to be assigned after submission
    # HINT: this column should be UNIQUE?
    biosample_id = models.CharField(max_length=255, blank=True, null=True)

    # '+' instructs Django that we don’t need this reverse relationship
    owner = models.ForeignKey(
        User,
        related_name='+',
        on_delete=models.CASCADE)

    def __str__(self):
        # HINT: shuold I return biosampleid if defined?
        return "%s (Submission: %s)" % (self.name, self.submission_id)

    class Meta:
        unique_together = (("name", "submission"),)


class BioSampleMixin(object):
    """Common methods for animal and samples"""

    def __str__(self):
        return str(self.name)

    def get_biosample_id(self):
        """Get the biosample id or a temporary name"""

        return self.name.biosample_id or "animal_%s" % (
                self.id)

    def to_validation(self):
        """Common features to both Sample and Animal"""

        result = {}

        # get a biosample id or a default value
        result["biosampleId"] = self.get_biosample_id()

        result["project"] = "IMAGE"

        if self.description:
            result["description"] = self.description

        result["name"] = self.name.name

        submission = self.name.submission
        result["geneBankName"] = submission.gene_bank_name
        result["geneBankCountry"] = submission.gene_bank_country.label
        # https://docs.djangoproject.com/en/1.11/ref/models/instances/#django.db.models.Model.get_FOO_display
        result["dataSourceType"] = submission.get_datasource_type_display()
        result["dataSourceVersion"] = submission.datasource_version

        result["dataSourceId"] = self.alternative_id

        return result

    def get_attributes(self):
        """Common attribute definition"""

        attributes = {}

        attributes["project"] = format_attribute(
            value="IMAGE")

        attributes['dataSourceId'] = format_attribute(
            value=self.name.name)

        attributes['alternativeId'] = format_attribute(
            value=self.alternative_id)

        attributes['submissionTitle'] = format_attribute(
            value=self.name.submission.title)

        attributes['personLastName'] = format_attribute(
            value=self.owner.last_name)

        attributes['personEmail'] = format_attribute(
            value=self.owner.email)

        attributes['personAffiliation'] = format_attribute(
            value=self.owner.person.affiliation.name)

        attributes['personRole'] = format_attribute(
            value=self.owner.person.role.label,
            terms=self.owner.person.role.term)

        attributes['organizationName'] = format_attribute(
            value=self.name.submission.organization.name)

        attributes['organizationRole'] = format_attribute(
            value=self.name.submission.organization.role.label,
            terms=self.name.submission.organization.role.term)

        attributes['geneBankName'] = format_attribute(
            value=self.name.submission.gene_bank_name)

        attributes['geneBankCountry'] = format_attribute(
            value=self.name.submission.gene_bank_country.label,
            terms=self.name.submission.gene_bank_country.term)

        attributes['dataSourceType'] = format_attribute(
            value=self.name.submission.get_datasource_type_display())

        attributes['dataSourceVersion'] = format_attribute(
            value=self.name.submission.datasource_version)

        return attributes


class Animal(BioSampleMixin, models.Model):
    # an animal name has a entry in name table
    name = models.OneToOneField(
            'Name',
            on_delete=models.PROTECT)

    # alternative id will store the internal id in data source
    alternative_id = models.CharField(max_length=255, blank=True, null=True)

    description = models.CharField(max_length=255, blank=True, null=True)

    # HINT: link to a term list table?
    material = models.CharField(
            max_length=255,
            default="Organism",
            editable=False,
            null=True)

    breed = models.ForeignKey('DictBreed', db_index=True)

    # species is in DictBreed table

    # using a constraint for sex
    sex = models.ForeignKey(
            'DictSex',
            blank=True,
            null=True,
            default=-1)

    # check that father and mother are defined using Foreign Keys
    # HINT: mother and father are not mandatory in all datasource
    father = models.ForeignKey(
            'Name',
            on_delete=models.PROTECT,
            null=True,
            related_name='father_set')

    mother = models.ForeignKey(
            'Name',
            on_delete=models.PROTECT,
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

    owner = models.ForeignKey(
        User,
        related_name='animals',
        on_delete=models.CASCADE)

    def get_biosample_id(self):
        """Get the biosample id or a temporary name"""

        return self.name.biosample_id or "animal_%s" % (
                self.id)

    def to_validation(self):
        """Get a json representation of animal"""

        result = super().to_validation()

        result["material"] = {
                "text": "organism",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "OBI_0100026"]
                ),
        }

        result["species"] = self.breed.specie.to_validation()

        result["breed"] = self.breed.to_validation()

        result["sex"] = self.sex.to_validation()

        # TODO: were are father and mother? Should unknown return no fields?

        return result

    def get_attributes(self):
        """Return attributes like biosample needs"""

        attributes = super().get_attributes()

        attributes["material"] = format_attribute(
            value="organism", terms="OBI_0100026")

        attributes['species'] = format_attribute(
            value=self.breed.specie.label,
            terms=self.breed.specie.term)

        attributes['suppliedBreed'] = format_attribute(
            value=self.breed.supplied_breed)

        attributes['efabisBreedCountry'] = format_attribute(
            value=self.breed.country.label,
            terms=self.breed.country.term)

        attributes['sex'] = format_attribute(
            value=self.sex.label,
            terms=self.sex.term)

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
            result['releaseDate'] = None
        else:
            now = datetime.datetime.now()
            result['releaseDate'] = str(now.date())

        result['taxonId'] = self.breed.specie.taxon_id

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
    name = models.ForeignKey(
            'Name',
            on_delete=models.PROTECT)

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
            on_delete=models.PROTECT)

    protocol = models.CharField(max_length=255, blank=True, null=True)

    collection_date = models.DateField(blank=True, null=True)
    collection_place_latitude = models.FloatField(blank=True, null=True)
    collection_place_longitude = models.FloatField(blank=True, null=True)
    collection_place = models.CharField(max_length=255, blank=True, null=True)

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

    def to_validation(self):
        """Get a biosample representation of animal"""

        result = super().to_validation()

        result["material"] = {
                "text": "specimen from organism",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "OBI_0001479"]
                ),
        }

        result["derivedFrom"] = self.animal.get_biosample_id()

        if self.collection_date:
            result["collectionDate"] = {
                "text": str(self.collection_date),
                "unit": "YYYY-MM-DD"
            }

        if self.collection_place:
            result["collectionPlace"] = self.collection_place

        # TODO: move the following two fields to Dictionary Table
        if self.organism_part and self.organism_part_term:
            result["organismPart"] = {
                "text": self.organism_part,
                "ontologyTerms": "/".join([
                    OBO_URL,
                    self.organism_part_term]
                ),
            }

        if self.developmental_stage and self.developmental_stage_term:
            result["developmentStage"] = {
                "text": self.developmental_stage,
                "ontologyTerms": "/".join([
                    OBO_URL,
                    self.developmental_stage_term]
                ),
            }

        if self.animal_age_at_collection:
            result["animalAgeAtCollection"] = {
                "text": self.animal_age_at_collection,
                "unit": "years"
            }

        if self.availability:
            result["availability"] = self.availability

        return result

    def get_attributes(self):
        """Return attributes like biosample needs"""

        attributes = super().get_attributes()

        attributes["material"] = format_attribute(
            value="specimen from organism", terms="OBI_0001479")

        attributes['species'] = format_attribute(
            value=self.animal.breed.specie.label,
            terms=self.animal.breed.specie.term)

        # HINT: this won't to be a biosample id in the first submission.
        # How to fix it? can be removed from mandatory attributes
        attributes['derivedFrom'] = format_attribute(
            value=self.animal.name.name)

        attributes['collectionDate'] = format_attribute(
            value=str(self.collection_date), units="YYYY-MM-DD")

        attributes['collectionPlace'] = format_attribute(
            value=self.collection_place)

        # TODO: this will point to a correct term dictionary table
        attributes['organismPart'] = format_attribute(
            value=self.organism_part,
            terms=self.organism_part_term)

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
            result['releaseDate'] = None
        else:
            now = datetime.datetime.now()
            result['releaseDate'] = str(now.date())

        result['taxonId'] = self.animal.breed.specie.taxon_id

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


class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    initials = models.CharField(max_length=255, blank=True, null=True)

    # HINT: with a OneToOneField relation, there will be only one user for
    # each organization
    affiliation = models.ForeignKey(
        'Organization',
        null=True,
        on_delete=models.CASCADE,
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
    address = models.CharField(
        max_length=255, blank=True, null=True,
        help_text='One line, comma separated')

    country = models.ForeignKey('DictCountry')

    URI = models.URLField(
        max_length=500, blank=True, null=True,
        help_text='Web site')

    role = models.ForeignKey(
            'DictRole',
            on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class Publication(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    pubmed_id = models.CharField(max_length=255,
                                 help_text='Valid PubMed ID, numeric only')

    # This column is in submission sheet of template file
    doi = models.CharField(max_length=255,
                           help_text='Valid Digital Object Identifier')

    def __str__(self):
        return str(str(self.id) + ", " + str(self.pubmed_id))


# HINT: do I need this table?
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


class Submission(models.Model):
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

    gene_bank_country = models.ForeignKey('DictCountry')

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
        on_delete=models.CASCADE,
        help_text="Who owns the data")

    # custom fields for datasource
    upload_dir = 'data_source/'
    uploaded_file = models.FileField(upload_to=upload_dir)

    # when submission is created
    created_at = models.DateTimeField(auto_now_add=True)

    # 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
    class STATUSES(Enum):
        waiting = (0, 'Waiting')
        loaded = (1, 'Loaded')
        submitted = (2, 'Submitted')
        error = (3, 'Error')
        need_revision = (4, 'Need Revision')

        @classmethod
        def get_value(cls, member):
            return cls[member].value[0]

    # a column to track submission status
    status = models.SmallIntegerField(
            choices=[x.value for x in STATUSES],
            help_text='example: Waiting',
            null=True,
            blank=True,
            default=0)

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

    def get_absolute_url(self):
        return reverse("submissions:detail", kwargs={"pk": self.pk})


def uid_report():
    """Performs a statistic on UID database to find issues"""

    # TODO: act for a user
    report = {}

    # get n_of_animals
    report['n_of_animals'] = Animal.objects.count()

    # get n_of_samples
    report['n_of_samples'] = Sample.objects.count()

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
