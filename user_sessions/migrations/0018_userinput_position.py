# Generated by Django 2.2.13 on 2020-11-11 21:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_sessions', '0017_auto_20201111_1959'),
    ]

    operations = [
        migrations.AddField(
            model_name='userinput',
            name='position',
            field=models.IntegerField(default=0),
        ),
    ]