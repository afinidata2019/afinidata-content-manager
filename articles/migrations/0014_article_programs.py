# Generated by Django 2.2.5 on 2020-10-02 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0010_program_languages'),
        ('articles', '0013_delete_topic'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='programs',
            field=models.ManyToManyField(to='programs.Program'),
        ),
    ]