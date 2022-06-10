from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_userresources'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='language_preference',
            field=models.CharField(choices=[('en', 'English'), ('fr', 'French')], default='fr', max_length=15)
        ),
    ]
