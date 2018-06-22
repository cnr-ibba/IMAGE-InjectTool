
from django import forms

from image_app.models import DataSource, DictCountry


class DataSourceForm(forms.ModelForm):
    name = forms.CharField(label="Gene bank Name")
    country = forms.ModelChoiceField(
        label="Gene bank country",
        queryset=DictCountry.objects.all())

    # the request is now available, add it to the instance data
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(DataSourceForm, self).__init__(*args, **kwargs)

    class Meta:
        model = DataSource
        fields = ('name', 'country', 'type', 'version', 'uploaded_file')
