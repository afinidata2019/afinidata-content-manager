# Generated by Django 2.2.10 on 2020-03-25 15:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instances', '0010_remove_instance_user_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='instance',
            name='areas',
        ),
        migrations.DeleteModel(
            name='InstanceSection',
        ),
    ]
