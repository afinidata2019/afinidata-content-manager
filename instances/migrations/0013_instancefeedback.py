# Generated by Django 2.2.10 on 2020-04-04 19:36

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('areas', '0007_auto_20200403_2324'),
        ('instances', '0012_auto_20200401_2318'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstanceFeedback',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post_id', models.IntegerField()),
                ('value', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('created_at', models.DateTimeField()),
                ('area', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='areas.Area')),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='instances.Instance')),
            ],
        ),
    ]
