# Generated by Django 2.2.10 on 2020-03-21 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('languages', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='available',
            field=models.BooleanField(default=True),
        ),
    ]
