# Generated by Django 3.0.5 on 2020-08-07 10:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import django_countries.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('assessment', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('email', models.EmailField(error_messages={'unique': 'A user with that username already exists.'}, max_length=255, unique=True, verbose_name='email')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
            ],
            options={
                'abstract': False,
            },
            managers=[
                ('object', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='UserResources',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('resources', models.ManyToManyField(blank=True, to='assessment.ExternalLink')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Organisation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('size', models.CharField(choices=[('0-9', '0-9'), ('10-49', '10-49'), ('50-99', '50-99'), ('100-499', '100-499'), ('500-4999', '500-4999'), ('>5000', '>5000')], max_length=200)),
                ('country', django_countries.fields.CountryField(max_length=2)),
                ('sector', models.CharField(choices=[('Agriculture', 'Agriculture'), ('Agroalimentaire', 'Industrie Agroalimentaire'), ('Armée / sécurité', 'Armée / sécurité'), ('Art / Design', 'Art / Design'), ('Audiovisuel / Spectacle', 'Audiovisuel / Spectacle'), ('Automobile', 'Automobile'), ('Banque / Assurance', 'Banque / Assurance'), ('Bois / Papier / Carton / Imprimerie', 'Bois / Papier / Carton / Imprimerie'), ('BTP / Architecture / Matériaux de construction', 'BTP / Architecture / Matériaux de construction'), ('Chimie / Parachimie', 'Chimie / Parachimie'), ('Commerce / Négoce / Distribution', 'Commerce / Négoce / Distribution'), ('Marketing / Communication / Multimédia', 'Communication / Marketing / Multimédia'), ('Construction aéronautique, ferroviaire et navale', 'Construction aéronautique, ferroviaire et navale'), ("Culture / Artisanat d'art", "Culture / Artisanat d'art"), ('Droit / Justice', 'Droit / Justice'), ('Électronique / Électricité', 'Électronique / Électricité'), ('Energie', 'Energie'), ('Enseignement', 'Enseignement'), ('Environnement', 'Environnement'), ('Fonction publique', 'Fonction publique'), ('Gestion / Conseil / Audit', 'Gestion / Conseil / Audit'), ('Hôtellerie / Restauration', 'Hôtellerie / Restauration'), ('Industrie pharmaceutique', 'Industrie pharmaceutique'), ('Informatique / Télécoms', 'Informatique / Télécoms'), ('Edition / Journalisme', 'Journalisme / Edition'), ('Machines et équipements / Mécanique', 'Machines et équipements / Mécanique'), ('Métallurgie / Travail du métal', 'Métallurgie / Travail du métal'), ('Plastique / Caoutchouc', 'Plastique / Caoutchouc'), ('Recherche', 'Recherche'), ('Santé', 'Santé'), ('Social', 'Social'), ('Sport / Loisirs / Tourisme', 'Sport / Loisirs / Tourisme'), ('Textile / Habillement / Chaussure', 'Textile / Habillement / Chaussure'), ('Traduction / Interprétariat', 'Traduction / Interprétariat'), ('Transports / Logistique', 'Transports / Logistique'), ('Autre', 'Autre')], max_length=1000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', 'admin'), ('simple_user', 'simple_user')], default='admin', max_length=200)),
                ('organisation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='home.Organisation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]