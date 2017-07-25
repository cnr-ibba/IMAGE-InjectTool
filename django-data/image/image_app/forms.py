from django import forms
from image_app.models import Backup


class BackupForm(forms.ModelForm):
    class Meta:
        model = Backup
        fields = ('description', 'backup',)