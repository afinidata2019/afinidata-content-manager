# Generated by Django 2.2.10 on 2020-02-24 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instances', '0003_instance_milestones'),
    ]

    operations = [
        migrations.AlterField(
            model_name='response',
            name='created_at',
            field=models.DateTimeField(),
        ),
    ]
