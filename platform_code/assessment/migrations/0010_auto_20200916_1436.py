# Generated by Django 3.0.5 on 2020-09-16 14:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0009_auto_20200916_1422'),
    ]

    operations = [
        migrations.AlterField(
            model_name='masterchoice',
            name='master_evaluation_element',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='assessment.MasterEvaluationElement'),
        ),
    ]
