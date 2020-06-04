from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField

from common.constants import STATUSES, WAITING, READY
from uid.models import Submission as UIDSubmission


# Create your models here.
class Account(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='biosample_account')
    name = models.SlugField()
    team = models.ForeignKey(
        'ManagedTeam',
        on_delete=models.CASCADE,
        help_text="Your AAP Team")

    def __str__(self):
        full_name = " ".join([self.user.first_name, self.user.last_name])
        return "%s (%s)" % (self.name, full_name)


class ManagedTeam(models.Model):
    name = models.CharField(max_length=255, unique=True)

    @classmethod
    def get_teams(cls):
        teams = cls.objects.all()

        return [team.name for team in teams]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "managed team"
        verbose_name_plural = "managed teams"


class BaseSubmission(models.Model):
    usi_submission_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        unique=True,
        help_text='USI submission name')

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    # a field to track errors in UID loading. Should be blank if no errors
    # are found
    message = models.TextField(
        null=True,
        blank=True)

    # a column to track submission status
    # HINT: should I limit by biosample status?
    status = models.SmallIntegerField(
        choices=[x.value for x in STATUSES],
        help_text='example: Waiting',
        default=WAITING)

    samples_count = models.PositiveIntegerField(default=0)

    samples_status = JSONField(default=dict)

    class Meta:
        # Abstract base classes are useful when you want to put some common
        # information into a number of other models
        abstract = True


class Submission(BaseSubmission):
    uid_submission = models.ForeignKey(
        UIDSubmission,
        on_delete=models.CASCADE,
        related_name='usi_submissions')

    def __str__(self):
        return "%s <%s> (%s): %s" % (
            self.id,
            self.usi_submission_name,
            self.uid_submission,
            self.get_status_display())


class SubmissionData(models.Model):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='submission_data')

    # limit choices for contenttypes
    # https://axiacore.com/blog/how-use-genericforeignkey-django-531/
    name_limit = models.Q(app_label='uid', model='animal') | \
        models.Q(app_label='uid', model='sample')

    # Below the mandatory fields for generic relation
    # https://simpleisbetterthancomplex.com/tutorial/2016/10/13/how-to-use-generic-relations.html
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=name_limit)

    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return "%s <%s>: %s" % (
            self.submission.id,
            self.submission.usi_submission_name,
            self.content_object.name)

    class Meta:
        verbose_name = "submission data"
        verbose_name_plural = "submission data"


class OrphanSubmission(BaseSubmission):

    def __str__(self):
        return "%s <%s>: %s" % (
            self.id,
            self.usi_submission_name,
            self.get_status_display())


class OrphanSample(models.Model):
    submission = models.ForeignKey(
        OrphanSubmission,
        on_delete=models.PROTECT,
        null=True,
        default=None,
        blank=True,
        related_name='submission_data')

    # This will be assigned after submission
    biosample_id = models.CharField(
        max_length=255,
        unique=True)

    found_at = models.DateTimeField(auto_now_add=True)

    ignore = models.BooleanField(
        default=False,
        help_text='Should I ignore this record or not?')

    name = models.CharField(
        max_length=255)

    team = models.ForeignKey(
        'ManagedTeam',
        on_delete=models.CASCADE,
        help_text="Your AAP Team")

    # a column to track sample status
    status = models.SmallIntegerField(
        choices=[x.value for x in STATUSES],
        help_text='example: Waiting',
        default=READY)

    removed = models.BooleanField(
        default=False,
        help_text='Is this sample still available?')

    removed_at = models.DateTimeField(
        null=True,
        blank=True)

    def __str__(self):
        return "%s (%s)" % (self.biosample_id, self.found_at)
