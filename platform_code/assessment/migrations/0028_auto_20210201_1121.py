# Generated by Django 3.0.5 on 2021-02-01 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0027_auto_20210121_1249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evaluation',
            name='slug',
            field=models.SlugField(unique=True),
        ),
    ]
