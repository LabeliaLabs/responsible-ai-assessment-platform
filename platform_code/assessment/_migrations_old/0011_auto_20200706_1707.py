# Generated by Django 3.0.5 on 2020-07-06 17:07

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("assessment", "0010_auto_20200702_1354"),
    ]

    operations = [
        migrations.RemoveField(model_name="scoringsystem", name="coefficient",),
        migrations.AddField(
            model_name="scoringsystem",
            name="attributed_points_coefficient",
            field=models.FloatField(default=0.5),
        ),
        migrations.AlterField(
            model_name="evaluation",
            name="name",
            field=models.CharField(default="Evaluation 2020-07-06", max_length=200),
        ),
        migrations.AlterField(
            model_name="masterchoice",
            name="master_evaluation_element",
            field=models.ForeignKey(
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="master_choice_set",
                to="assessment.MasterEvaluationElement",
            ),
        ),
        migrations.AlterField(
            model_name="scoringsystem",
            name="organisation_type",
            field=models.CharField(
                blank=True, default="entreprise", max_length=1000, null=True
            ),
        ),
        migrations.CreateModel(
            name="EvaluationElementWeight",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=500)),
                (
                    "organisation_type",
                    models.CharField(
                        blank=True, default="entreprise", max_length=1000, null=True
                    ),
                ),
                (
                    "master_evaluation_element_weight_json",
                    django.contrib.postgres.fields.jsonb.JSONField(),
                ),
                (
                    "assessment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="assessment.Assessment",
                    ),
                ),
            ],
        ),
    ]
