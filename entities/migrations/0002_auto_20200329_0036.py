# Generated by Django 2.2.10 on 2020-03-29 00:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('entities', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='entity',
            options={'permissions': (('view_all_entities', 'View all entities types for instances.'),)},
        ),
    ]
