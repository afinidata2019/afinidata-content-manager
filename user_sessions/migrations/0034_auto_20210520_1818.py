# Generated by Django 3.1.4 on 2021-05-20 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_sessions', '0033_reply_attribute'),
    ]

    operations = [
        migrations.AlterField(
            model_name='botsessions',
            name='session_type',
            field=models.CharField(choices=[('welcome', 'Welcome'), ('default', 'Default'), ('exchange', 'Exchange')], max_length=20),
        ),
    ]