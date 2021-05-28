# Generated by Django 3.1.4 on 2021-04-26 15:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0017_intent'),
    ]

    operations = [
        migrations.CreateModel(
            name='Missing',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filter_params', models.TextField()),
                ('seen', models.TextField()),
                ('seen_count', models.IntegerField(default=0, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]