# Generated by Django 3.0.5 on 2020-11-04 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_merge_20201029_1014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='role',
            field=models.CharField(choices=[('read_only', 'read_only'), ('editor', 'editor'), ('admin', 'admin')], default='admin', max_length=200),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='sector',
            field=models.CharField(choices=[('Industriel - Grande entreprise', 'Industriel - Grande entreprise'), ('Industriel - ETI', 'Industriel - ETI'), ('Industriel - PME', 'Industriel - PME'), ('Prestataire B2B - Editeur de logiciels', 'Prestataire B2B - Editeur de logiciels'), ('Prestataire B2B - Cabinet de conseil', 'Prestataire B2B - Cabinet de conseil'), ('Organisme de recherche', 'Organisme de recherche'), ('autres', 'autres')], max_length=1000),
        ),
    ]