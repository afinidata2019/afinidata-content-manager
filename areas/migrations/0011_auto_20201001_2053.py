# Generated by Django 2.2.5 on 2020-10-01 20:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('areas', '0010_delete_topic'),
    ]

    operations = [
        migrations.RenameField(
            model_name='area',
            old_name='topic',
            new_name='top',
        ),
    ]
