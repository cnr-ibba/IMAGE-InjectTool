
from django import forms
from image_app.models import DataSource


class DataSourceForm(forms.ModelForm):
    class Meta:
        model = DataSource
        fields = ('name', 'version', 'uploaded_file')
