# Generated by Django 3.0.5 on 2021-01-19 09:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0011_auto_20210116_1404'),
    ]

    operations = [
        migrations.RenameField(
            model_name='platformmanagement',
            old_name='delivery',
            new_name='activate_multi_languages',
        ),
        migrations.RenameField(
            model_name='platformmanagement',
            old_name='languages_activation',
            new_name='platform_update',
        ),
    ]
