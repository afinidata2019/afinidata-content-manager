# Generated by Django 2.1.7 on 2019-03-26 00:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('milestones', '__first__'),
        ('entities', '0001_initial'),
        ('areas', '0001_initial'),
        ('bots', '0001_initial'),
        ('attributes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='attributes.Attribute')),
            ],
        ),
        migrations.CreateModel(
            name='Instance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('bot_user_id', models.IntegerField(default=1, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='InstanceSection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value_to_init', models.IntegerField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='areas.Area')),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='instances.Instance')),
            ],
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='instances.Instance')),
                ('milestone', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='milestones.Milestone')),
            ],
        ),
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField(default=0, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='areas.Area')),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='instances.Instance')),
            ],
        ),
        migrations.CreateModel(
            name='ScoreTracking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField(default=0, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='areas.Area')),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='instances.Instance')),
            ],
        ),
        migrations.AddField(
            model_name='instance',
            name='areas',
            field=models.ManyToManyField(through='instances.InstanceSection', to='areas.Area'),
        ),
        migrations.AddField(
            model_name='instance',
            name='attributes',
            field=models.ManyToManyField(through='instances.AttributeValue', to='attributes.Attribute'),
        ),
        migrations.AddField(
            model_name='instance',
            name='bot',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bots.Bot'),
        ),
        migrations.AddField(
            model_name='instance',
            name='entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='entities.Entity'),
        ),
        migrations.AddField(
            model_name='attributevalue',
            name='instance',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='instances.Instance'),
        ),
    ]