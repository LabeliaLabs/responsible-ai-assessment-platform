# Generated by Django 3.0.5 on 2020-09-04 08:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0006_externallink_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='scoringsystem',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='evaluation',
            name='name',
            field=models.CharField(default='Evaluation 04/09/2020', max_length=200),
        ),
    ]