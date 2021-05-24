# Generated by Django 3.1.4 on 2021-05-24 18:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attributes', '0005_attribute_attribute_view'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attribute',
            name='type',
            field=models.CharField(choices=[('numeric', 'Numeric'), ('string', 'String'), ('date', 'Date'), ('boolean', 'Boolean'), ('category', 'Category')], default='string', max_length=20),
        ),
    ]
