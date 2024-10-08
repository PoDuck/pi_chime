# Generated by Django 5.0.7 on 2024-07-21 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Clip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('game', models.CharField(max_length=100)),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='thumbnails/')),
                ('file', models.FileField(upload_to='clips/')),
                ('order', models.IntegerField(default=100000)),
                ('last_played', models.BooleanField(default=False)),
            ],
        ),
    ]
