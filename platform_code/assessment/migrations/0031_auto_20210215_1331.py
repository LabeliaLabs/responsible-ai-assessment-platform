# Generated by Django 3.0.5 on 2021-02-15 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0030_auto_20210212_1629'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evaluation',
            name='slug',
            field=models.SlugField(),
        ),
    ]
