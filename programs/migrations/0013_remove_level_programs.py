# Generated by Django 2.2.5 on 2020-10-05 19:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0012_level_programs'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='level',
            name='programs',
        ),
    ]