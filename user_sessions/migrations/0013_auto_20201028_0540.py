# Generated by Django 2.2.13 on 2020-10-28 05:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_sessions', '0012_auto_20201028_0534'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='interaction',
            name='instance_id_id',
        ),
        migrations.RemoveField(
            model_name='interaction',
            name='user_id_id',
        ),
    ]
