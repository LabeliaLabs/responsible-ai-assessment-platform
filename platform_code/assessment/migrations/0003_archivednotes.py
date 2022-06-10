from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0002_auto_20210323_1322'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluationelement',
            name='user_notes_archived',
            field=models.BooleanField(default=False),
        ),
    ]

