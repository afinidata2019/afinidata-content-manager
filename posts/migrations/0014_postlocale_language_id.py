# Generated by Django 2.2.13 on 2020-09-07 05:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0013_interaction_instance_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='postlocale',
            name='language_id',
            field=models.IntegerField(null=True),
        ),
    ]
