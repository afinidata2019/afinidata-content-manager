# Generated by Django 2.2.13 on 2020-12-22 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger_users', '0018_userchannel_bot_channel_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userchannel',
            name='user_channel_id',
            field=models.BigIntegerField(),
        ),
    ]