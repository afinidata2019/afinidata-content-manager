# Generated by Django 2.2.13 on 2020-08-10 03:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_auto_20200810_0332'),
    ]

    operations = [
        migrations.AlterField(
            model_name='situacional',
            name='id',
            field=models.CharField(choices=[('casa', 'En casa'), ('libre', 'Al aire libre'), ('transporte', 'En transporte'), ('caluroso', 'Día caluroso'), ('frio', 'Día de frío'), ('vacaciones', 'Vacaciones'), ('noche', 'De noche'), ('dia', 'De día'), ('todo', 'En toda ocasión')], max_length=35, primary_key=True, serialize=False),
        ),
    ]