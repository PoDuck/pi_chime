from django.contrib import admin
from .models import Track


class TrackAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at')
admin.site.register(Track)
