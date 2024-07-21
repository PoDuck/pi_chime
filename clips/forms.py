from django import forms
from .models import Clip


class RangeInput(forms.TextInput):
    template_name = "clips/widgets/range.html"


class ClipUploadForm(forms.ModelForm):
    class Meta:
        model = Clip
        fields = ["title", "game", "thumbnail", "file", "max_volume", "start_time", "end_time"]
        widgets = {'max_volume': RangeInput(
            attrs={
                'type': 'range',
                'oninput': 'this.nextElementSibling.value = this.value',
                'class': 'form-range w-25'
            }
        )}
