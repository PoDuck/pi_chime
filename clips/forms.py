from django import forms
from .models import Clip


class ClipUploadForm(forms.ModelForm):
    class Meta:
        model = Clip
        fields = ["title", "game", "thumbnail", "file"]