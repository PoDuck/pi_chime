from django.db import models


class Clip(models.Model):
    title = models.CharField(max_length=100)
    game = models.CharField(max_length=100)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    file = models.FileField(upload_to='clips/')
    order = models.IntegerField(blank=False, default=100_000)
    last_played = models.BooleanField(default=False)
    # Per clip settings.  Volume is in percentage and is multiplied with main settings volume percentage.
    # Start and end times override main settings start and end times.
    max_volume = models.IntegerField(blank=False, null=False, default=100)
    start_time = models.FloatField(blank=False, null=False, default=0.0)
    end_time = models.FloatField(blank=False, null=False, default=0.0)

    def __str__(self):
        return self.title

    @property
    def thumbnail_url(self):
        if self.thumbnail and hasattr(self.thumbnail, 'url'):
            return self.thumbnail.url

    @property
    def file_url(self):
        if self.file and hasattr(self.file, 'url'):
            return self.file.url


class Settings(models.Model):
    volume = models.IntegerField(default=100)
    start_time = models.FloatField(default=0.0)
    end_time = models.FloatField(default=0.0)
