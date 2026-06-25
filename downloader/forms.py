from django import forms

AUDIO_FORMATS = [
    ('mp3', 'MP3'),
    ('m4a', 'M4A'),
    ('aac', 'AAC'),
    ('flac', 'FLAC'),
    ('wav', 'WAV'),
    ('ogg', 'OGG Vorbis'),
    ('opus', 'Opus'),
]

VIDEO_FORMATS = [
    ('mp4', 'MP4'),
    ('webm', 'WebM'),
    ('mkv', 'MKV'),
    ('avi', 'AVI'),
    ('mov', 'MOV'),
]

FORMAT_TYPE_CHOICES = [
    ('audio', 'Audio only'),
    ('video', 'Video'),
]


class DownloadForm(forms.Form):
    url = forms.URLField(
        label='YouTube URL',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.youtube.com/watch?v=...',
        }),
    )
    format_type = forms.ChoiceField(
        choices=FORMAT_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='audio',
    )
    audio_format = forms.ChoiceField(
        choices=AUDIO_FORMATS,
        initial='mp3',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    video_format = forms.ChoiceField(
        choices=VIDEO_FORMATS,
        initial='mp4',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    start_time = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0:00 or 90',
        }),
        help_text='Leave blank to start from the beginning.',
    )
    end_time = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '3:45 or 225',
        }),
        help_text='Leave blank to go to the end.',
    )
