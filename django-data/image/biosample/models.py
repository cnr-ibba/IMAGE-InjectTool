from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Account(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='biosample_account')
    name = models.SlugField()
    team = models.CharField(max_length=255)

    def __str__(self):
        return "%s (%s)" % (self.name, self.team)


# TODO: is really necessary?
class Managed(models.Model):
    team_name = models.CharField(max_length=255, unique=True)

    @classmethod
    def get_teams(cls):
        teams = cls.objects.all()

        return [team.team_name for team in teams]

    def __str__(self):
        return self.team_name

    class Meta:
        verbose_name = "managed team"
        verbose_name_plural = "managed teams"
