# Generated by Django 2.2.10 on 2020-03-18 21:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0002_auto_20200311_1221'),
    ]

    operations = [
        migrations.CreateModel(
            name='Interaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserInteraction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('Interaction', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='bots.Interaction')),
                ('bot', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='bots.Bot')),
            ],
        ),
    ]