# Generated by Django 3.1.4 on 2021-04-22 17:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('messenger_users', '0027_auto_20210420_2213'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='last_seen',
        ),
    ]