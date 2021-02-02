# Generated by Django 2.2.13 on 2021-02-02 21:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_sessions', '0021_botsessions'),
    ]

    operations = [
        migrations.CreateModel(
            name='AvailableService',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=500)),
                ('url', models.CharField(max_length=200)),
                ('request_type', models.CharField(choices=[('post', 'POST'), ('get', 'GET')], default='post', max_length=5)),
                ('suggested_params', models.CharField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='service',
            name='available_service',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.PROTECT, to='user_sessions.AvailableService'),
            preserve_default=False,
        ),
    ]