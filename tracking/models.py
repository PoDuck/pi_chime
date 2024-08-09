from django.db import models


class Track(models.Model):
    location = models.CharField(max_length=255, default="front_door")
    created = models.DateTimeField(auto_now_add=True)
