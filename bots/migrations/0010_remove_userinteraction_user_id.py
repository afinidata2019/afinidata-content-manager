# Generated by Django 2.2.5 on 2020-09-18 21:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0009_userinteraction_person'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userinteraction',
            name='user_id',
        ),
    ]
