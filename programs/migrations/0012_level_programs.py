# Generated by Django 2.2.5 on 2020-10-05 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0011_remove_level_program'),
    ]

    operations = [
        migrations.AddField(
            model_name='level',
            name='programs',
            field=models.ManyToManyField(to='programs.Program'),
        ),
    ]
