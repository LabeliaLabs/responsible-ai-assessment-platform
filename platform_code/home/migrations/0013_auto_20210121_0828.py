# Generated by Django 3.0.5 on 2021-01-21 08:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0012_auto_20210119_0945'),
    ]

    operations = [
        migrations.AlterField(
            model_name='platformmanagement',
            name='delivery_text',
            field=models.TextField(default='Bonjour', max_length=1000),
        ),
        migrations.AlterField(
            model_name='platformmanagement',
            name='delivery_text_en',
            field=models.TextField(default='Bonjour', max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='platformmanagement',
            name='delivery_text_fr',
            field=models.TextField(default='Bonjour', max_length=1000, null=True),
        ),
    ]
