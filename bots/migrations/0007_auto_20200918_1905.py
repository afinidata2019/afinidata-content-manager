# Generated by Django 2.2.5 on 2020-09-18 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0006_auto_20200328_2112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userinteraction',
            name='created_at',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='userinteraction',
            name='updated_at',
            field=models.DateTimeField(),
        ),
    ]
