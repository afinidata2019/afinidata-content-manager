# Generated by Django 2.2.13 on 2020-09-07 05:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0007_merge_20200906_2353'),
    ]

    operations = [
        migrations.AddField(
            model_name='articletranslate',
            name='language_id',
            field=models.IntegerField(null=True),
        ),
    ]