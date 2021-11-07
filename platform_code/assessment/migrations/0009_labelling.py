# Generated by Django 3.2.7 on 2021-09-03 15:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0009_auto_20210906_0852'),
    ]

    operations = [
        migrations.CreateModel(
            name='Labelling',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('progress', 'progress'), ('justification', 'justification'), ('labelled', 'labelled'), ('refused', 'refused')], default='progress', max_length=200)),
                ('counter', models.IntegerField(default=1)),
                ('start_date', models.DateTimeField(auto_now_add=True)),
                ('last_update', models.DateTimeField(blank=True, null=True)),
                ('justification_request_date', models.DateTimeField(blank=True, null=True)),
                ('evaluation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='assessment.evaluation')),
            ],
        ),
        migrations.AddField(
            model_name='evaluation',
            name='is_deleteable',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='evaluation',
            name='is_editable',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='assessment',
            name='previous_assessment',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to='assessment.assessment'),
        ),
    ]