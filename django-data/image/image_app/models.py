from django.db import models
# from django.contrib.auth.models import User
import datetime
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


YEAR_CHOICES = []
for r in range(1980, (datetime.datetime.now().year+1)):
    YEAR_CHOICES.append((r,r))



class Dict_organization_roles(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    description = models.CharField(max_length=255)

    def __str__(self):
        return str(self.description)

    class Meta:
        # managed = False
        db_table = 'dict_organization_roles'
        verbose_name = 'Organization role'
        verbose_name_plural = 'Organization roles'


class DictBreeds(models.Model):
    # id = models.IntegerField(primary_key=True)  # AutoField?
    db_breed = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    species = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    language = models.CharField(max_length=255, blank=True, null=True)
    api_url = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return str(self.description)

    class Meta:
        # managed = False
        db_table = 'dict_breeds'
        verbose_name = 'Breed'
        verbose_name_plural = 'Breeds'



