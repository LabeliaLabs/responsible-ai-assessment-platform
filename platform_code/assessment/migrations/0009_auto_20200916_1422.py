# Generated by Django 3.0.5 on 2020-09-16 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0008_auto_20200916_1343'),
    ]

    operations = [
        migrations.AddField(
            model_name='choice',
            name='fetch',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='evaluationelement',
            name='fetch',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='section',
            name='fetch',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='section',
            name='user_notes',
            field=models.TextField(blank=True, max_length=20000, null=True),
        ),
    ]