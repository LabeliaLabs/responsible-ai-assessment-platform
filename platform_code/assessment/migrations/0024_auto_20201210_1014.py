# Generated by Django 3.0.5 on 2020-12-10 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0023_auto_20201209_1016'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evaluation',
            name='name',
            field=models.CharField(default='Evaluation', max_length=200),
        ),
    ]
