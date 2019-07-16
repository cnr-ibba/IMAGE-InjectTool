from django.db import models
from django.contrib.auth.models import User

from common.constants import STATUSES, NAME_STATUSES, WAITING, LOADED
from image_app.models import Submission as UIDSubmission, Name


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

    usi_submission_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        unique=True,
        help_text='USI submission id')

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    # a column to track submission status
    # HINT: should I limit by biosample status?
    status = models.SmallIntegerField(
        choices=[x.value for x in STATUSES],
        help_text='example: Waiting',
        default=WAITING)

    def __str__(self):
        return "%s (%s): %s" % (
            self.usi_submission_id,
            self.uid_submission,
            self.get_status_display())


class SubmissionData(models.Model):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='submission_data')

    name = models.ForeignKey(
        Name,
        on_delete=models.CASCADE)

    # a column to track submission status
    # HINT: should I limit by biosample status? should I move from UID name?
    status = models.SmallIntegerField(
        choices=[x.value for x in STATUSES if x.name in NAME_STATUSES],
        help_text='example: Submitted',
        default=LOADED)

    def __str__(self):
        return "%s: %s" % (
            self.submission.usi_submission_id,
            self.name.name)

    class Meta:
        verbose_name = "submission data"
        verbose_name_plural = "submission data"
