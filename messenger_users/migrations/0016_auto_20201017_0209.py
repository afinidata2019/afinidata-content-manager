# Generated by Django 2.2.13 on 2020-10-17 02:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger_users', '0015_auto_20201017_0159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdata',
            name='data_key',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
