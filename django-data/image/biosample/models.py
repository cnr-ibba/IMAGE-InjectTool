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
        return self.name
