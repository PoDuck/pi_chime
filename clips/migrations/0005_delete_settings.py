# Generated by Django 5.0.7 on 2024-07-21 16:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clips', '0004_rename_volume_settings_max_volume'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Settings',
        ),
    ]
