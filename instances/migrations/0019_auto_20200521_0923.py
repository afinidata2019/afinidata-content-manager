# Generated by Django 2.2.10 on 2020-05-21 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instances', '0018_auto_20200505_1638'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instance',
            name='name',
            field=models.TextField(),
        ),
    ]
