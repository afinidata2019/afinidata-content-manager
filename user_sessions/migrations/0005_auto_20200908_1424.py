# Generated by Django 2.2.13 on 2020-09-08 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_sessions', '0004_auto_20200908_1416'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reply',
            name='label',
            field=models.CharField(max_length=50),
        ),
    ]