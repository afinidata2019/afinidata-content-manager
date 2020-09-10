# Generated by Django 2.2.5 on 2020-02-19 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('block_id', models.CharField(default='', max_length=255)),
                ('language', models.CharField(max_length=2)),
                ('full_locale', models.CharField(max_length=5)),
                ('content', models.TextField()),
                ('extra_items', models.TextField(default='')),
            ],
        ),
    ]