# Generated by Django 2.2.5 on 2020-10-05 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0013_remove_level_programs'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='levels',
            field=models.ManyToManyField(to='programs.Level'),
        ),
    ]