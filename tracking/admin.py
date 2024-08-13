from django.contrib import admin
from .models import Track


class TrackAdmin(admin.ModelAdmin):
    fields = ('location', 'created', 'updated')
    list_display = ('location', 'created', 'updated')
    readonly_fields = ('created', 'updated')


admin.site.register(Track, TrackAdmin)
