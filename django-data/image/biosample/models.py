from django.db import models
from django.contrib.auth.models import User


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
