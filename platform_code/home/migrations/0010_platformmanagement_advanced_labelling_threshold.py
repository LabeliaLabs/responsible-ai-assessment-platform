from django.db import migrations, models


def update_thresholds(apps, schema_editor):
    PlatformManagement = apps.get_model("home", "PlatformManagement")
    for platform_management in PlatformManagement.objects.all():
        if platform_management.labelling_threshold == 45:
            platform_management.labelling_threshold = 50
        if platform_management.advanced_labelling_threshold is None:
            platform_management.advanced_labelling_threshold = 60
        platform_management.save(update_fields=["labelling_threshold", "advanced_labelling_threshold"])


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0009_auto_20231006_0814"),
    ]

    operations = [
        migrations.AddField(
            model_name="platformmanagement",
            name="advanced_labelling_threshold",
            field=models.FloatField(default=60),
        ),
        migrations.AlterField(
            model_name="platformmanagement",
            name="labelling_threshold",
            field=models.FloatField(default=50),
        ),
        migrations.RunPython(update_thresholds, migrations.RunPython.noop),
    ]
