from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from common.constants import STATUSES, WAITING
from image_app.models import Submission as UIDSubmission


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


class Submission(models.Model):
    uid_submission = models.ForeignKey(
        UIDSubmission,
        on_delete=models.CASCADE,
        related_name='usi_submissions')

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
    name_limit = models.Q(app_label='image_app', model='animal') | \
        models.Q(app_label='image_app', model='sample')

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
