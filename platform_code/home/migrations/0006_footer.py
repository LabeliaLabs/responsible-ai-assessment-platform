# Generated by Django 3.2.7 on 2022-03-22 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0005_platformmanagement_labelling_threshold'),
    ]

    operations = [
        migrations.CreateModel(
            name='Footer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logo', models.ImageField(upload_to='logo')),
                ('link', models.URLField()),
                ('name', models.CharField(max_length=255)),
            ],
        ),
    ]
