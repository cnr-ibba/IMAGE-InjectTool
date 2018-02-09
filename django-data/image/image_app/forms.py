
from django import forms
from django.contrib.auth.models import User

from image_app.models import DataSource, Person


class DataSourceForm(forms.ModelForm):
    class Meta:
        model = DataSource
        fields = ('name', 'version', 'uploaded_file')


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ('initials', 'affiliation', 'role')
