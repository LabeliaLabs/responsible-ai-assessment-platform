# Generated by Django 3.0.5 on 2021-04-05 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0003_archivednotes'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluationscore',
            name='exposition_dic',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='masterevaluationelement',
            name='risk_domain',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='masterevaluationelement',
            name='risk_domain_en',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='masterevaluationelement',
            name='risk_domain_fr',
            field=models.TextField(blank=True, null=True),
        ),
    ]
