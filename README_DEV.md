# Dev Setup

> Reminder: No deploy friday!

- [Dev Setup](#dev-setup)
  - [1. Linux](#1-linux)
    - [Config](#config)
    - [[monthly] Server Update](#monthly-server-update)
    - [SSH](#ssh)
      - [Generate key](#generate-key)
      - [Connection](#connection)
      - [SCP](#scp)
    - [Install Docker & docker-compose](#install-docker--docker-compose)
    - [Install Nginx & configure](#install-nginx--configure)
    - [Install Certbot](#install-certbot)
    - [UFW: Uncomplicated FireWall](#ufw-uncomplicated-firewall)
    - [Port forward](#port-forward)
    - [Install Antivirus](#install-antivirus)
    - [Install Fail2ban](#install-fail2ban)
    - [Configure DNS](#configure-dns)
    - [Use the makefile](#use-the-makefile)
    - [Logs](#logs)
    - [Deploy a new release aka deploy on Prod](#deploy-a-new-release-aka-deploy-on-prod)
  - [2. Docker](#2-docker)
    - [Environments & environment variables](#environments--environment-variables)
    - [Run in detached mode and follow docker logs](#run-in-detached-mode-and-follow-docker-logs)
  - [3. Django](#3-django)
    - [Python Recommended tools](#python-recommended-tools)
    - [Djnago settings](#djnago-settings)
    - [Start a django shell in the django container](#start-a-django-shell-in-the-django-container)
    - [Translation](#translation)
    - [Tests](#tests)
    - [Reset migrations](#reset-migrations)
    - [Django logs](#django-logs)
    - [Django check](#django-check)
  - [4. Postgresql](#4-postgresql)
    - [Start a postgresql shell](#start-a-postgresql-shell)
    - [Debugger (pdb, ipdb)](#debugger-pdb-ipdb)
    - [Get the postgresql container id](#get-the-postgresql-container-id)
    - [Dump full db](#dump-full-db)
    - [Restaure full db](#restaure-full-db)
    - [Dump tables](#dump-tables)
    - [List tables](#list-tables)
  - [5. Tips](#5-tips)
    - [Copy the zip file from the server to your local machine](#copy-the-zip-file-from-the-server-to-your-local-machine)
    - [Utils](#utils)
    - [SEO](#seo)
    - [Debug & logs](#debug--logs)

## 1. Linux

> Warning: Treat with caution ssh keys and if you find some viruses on your machine, please let other members of the team know and update your keys once the issue is solved.

### Config

On a new server, change unix user password: `whoami` & `sudo passwd`

### [monthly] Server Update

Use the `update.sh` script (with `./update.sh`), but be careful with programs! For instance, it is better to stop docker (down) before installing docker upgrades.

This script basilly does this:

```sh
sudo apt update && \
        sudo apt upgrade && \
        sudo apt autoremove --purge && \
        sudo apt autoclean
```

### SSH

> Note: OVH requires rsa keys in order to add it to the server with the web interface (to regain access to the server in case of reinstallation).

[OVH ssh keys admin](https://www.ovh.com/manager/dedicated/#/billing/autorenew/ssh)

[quick server config](https://docs.ovh.com/fr/vps/conseils-securisation-vps/)

#### Generate key

> Note: add your public key (`.pub`) to OVH or on a server and keep your private key for yourself!

Generate a dedicated ssh key (RSA 4096 bit key with email as a comment):

```sh
# OVH needs a rsa key if you want to add it from web interface
ssh-keygen -t rsa -b 4096 -C "<<EMAIL_CHANGE_ME>>" -f ~/.ssh/<KEY>
# if ppossible use ed25519
ssh-keygen -o -a 100 -t ed25519 -f ~/.ssh/id_ed25519 -C "<<EMAIL_CHANGE_ME>>" -f ~/.ssh/<KEY>
```

Use the OVH web interface for first login, then you will be authorized to append this ssh key to `.ssh/authorized_keys` or with `ssh-copy-id`. When it's done you can connect to preprod server.

#### Connection

```sh
ssh -i ~/.ssh/<PRIVATE_KEY> <UNIX_USER>@<IP>
# For example, to connect preprod
ssh -i ~/.ssh/preprod ubuntu@51.68.125.118
```

You use this config to avoid some mistakes. When it is ready, you can simply use `ssh preprod` or `ssh prod`!

```sh
Host preprod 
        HostName 51.68.125.118
        User ubuntu
        IdentityFile ~/.ssh/<KEY>

Host prod
        HostName 146.59.147.178
        User ubuntu
        IdentityFile ~/.ssh/<KEY>
```

#### SCP

- Copy a **local file to a remote host**: `scp {{path/to/local_file}} {{remote_host}}:{{path/to/remote_file}}`

- Copy a file **from a remote host to a local directory**: `scp {{remote_host}}:{{path/to/remote_file}} {{path/to/local_directory}}`

```sh
scp -i ~/.ssh/<CLE> <UNIX_USER>@<IP>:/home/ubuntu/platform_db_prod.dump .
# For example
scp -i .ssh/preprod ubuntu@51.68.125.118:/home/ubuntu/platform_db_prod.dump .
# with .ssh/config ready
scp ubuntu@prod:/home/ubuntu/platform_db_prod.dump .
```

> Please have a look at the /dump/dump_db_prod.sh script: a zip file containing several dumps can be generated and fetched!

### Install Docker & docker-compose

- [docker](https://docs.docker.com/engine/install/ubuntu/)
- Don't forget to `sudo usermod -aG docker $USER`
- [docker-compose](https://docs.docker.com/compose/install/)

### Install Nginx & configure

```sh
# Ubuntu install
sudo apt install nginx

# [only once] Dereference default conf from enabled websites
sudo unlink /etc/nginx/sites-enabled/default

# Edit your config with the one located in data/nginx/nginx.conf
sudo vi /etc/nginx/sites-available/preprod.assessment.substra.ai
# [temp] use this path for statics: "/home/ubuntu/pf-assessment-dsrc/platform_code/assessment/static/;"

# Link it to the enabled websites
sudo ln -s /etc/nginx/sites-available/preprod.assessment.substra.ai /etc/nginx/sites-enabled

# Test config & reload nginx: will provide feedbacks in case of errors
sudo nginx -t && sudo nginx -s reload
sudo nginx -T
```

### Install Certbot

```sh
# Ubuntu snap install, as advised on certbot website
# https://certbot.eff.org/lets-encrypt/ubuntufocal-nginx
sudo snap install --classic certbot

# First config
sudo certbot --nginx

# Test renew
sudo certbot renew --dry-run
sudo certbot renew --dry-run --verbose
# Renew
sudo certbot renew
```

### UFW: Uncomplicated FireWall

```sh
# Status/On/Off
sudo ufw status
sudo ufw status verbose
sudo ufw enable
sudo ufw disable

# Connections status
sudo ufw app list
sudo ufw status numbered

# Allow web connections, only
sudo ufw allow http
sudo ufw allow https
sudo ufw allow 'Nginx Full'

# Custom
sudo ufw delete <ID>
sudo ufw deny out <PORT>

# Logs
tail -f /var/log/ufw.log
```

As of now, available applications:

- Nginx Full
- Nginx HTTP
- Nginx HTTPS
- OpenSSH
- 22
- 587 (email)

### Port forward

Enable `sysctl net.ipv4.forward` by editing `/etc/sysctl.conf` & `/etc/ufw/sysctl.conf` and running `sysctl -p`.

Ufw: `/etc/ufw/before.rules`:

```sh
*nat
:PREROUTING ACCEPT [0:0]
-A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8000
COMMIT
```

And reload ufw

```sh
sudo ufw disable && sudo ufw enable
sudo service ufw restart
sudo ufw reload
sudo systemctl restart ufw
```

### Install Antivirus

clamav: `sudo apt install clamav`

### Install Fail2ban

Ubuntu package: <https://packages.ubuntu.com/search?keywords=fail2ban>

```sh
# Install
# Please use the latest version
curl -LO http://fr.archive.ubuntu.com/ubuntu/pool/universe/f/fail2ban/fail2ban_0.11.1-1_all.deb

sudo dpkg -i fail2ban_0.11.1-1_all.deb

# Check service status 
sudo service fail2ban status

# Logs
tail -f /var/log/fail2ban.log
```

### Configure DNS

On Gandi.net interface (just [here](https://admin.gandi.net/domain/3547e9fe-5ee6-11ea-ba20-00163e8fd4b8/substra.ai/records)), set A and AAAA records to the servers IP (ipv4 & ipv6).

### Use the makefile

Help yourself and use the `Makefile` at the root of the repo! You might need to first install `build-essential` on linux or `make` (with chocolatey package manager for [example](https://chocolatey.org/packages/make) on Windows).

You'll then be able to use `make buildupd` instead of typing `docker-compose up --build -d` and so on!

Available commands:

```sh
# Dev
- up
- upd
- buildup
- buildupd
- migr
- migr-show
- migr-fake
- static
- admin
- down
- downv
- tests
- trans-prep
- translate
- backup

# Prod-like-local
- prodlike_up
- prodlike_buildup
- prodlike_buildupd
- prodlike_migr
- prodlike_static
- prodlike_admin
- prodlike_down
- prodlike_downv
- prodlike_tests

# Prod
- prod_up
- prod_buildup
- prod_buildupd
- prod_migr
- prod_static
- prod_admin
- prod_down
- prod_downv
- prod_tests
```

### Logs

```sh
# live logs
journalctl -f

tail -f /var/log/nginx/access.log;
tail -f /var/log/nginx/error.log;
tail -f /var/log/ufw.log
tail -f /var/log/letsencrypt/letsencrypt.log

tail -f /var/log/fail2ban.log
tail -f /var/log/auth.log
tail -f /var/log/syslog
```

### Deploy a new release aka deploy on Prod

The deploy script (`./deploy.sh`) is ready to handle this but as an overview of the required steps, here is what is happening during a code release:

- [optional] Apply server updates (especially docker updates!): `./update.sh`
- Backup: `docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_dump -Fc platform_db_prod > platform_db_prod.dump`
- Stop docker: `docker-compose -f docker-compose.prod.yml down`
- Pull the code with the "*deploy*" user (**read-only**): `git fetch && git pull --rebase`
- Re-build the code: `docker-compose -f docker-compose.prod.yml up --build -d`
- Apply migrations:
  - `docker-compose -f docker-compose.prod.yml exec web python manage.py makemigrations`
  - `docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput`
- Update statics: `docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear`

If needed, use backup:

- Postgresql `pg_restore`

```sh
docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_restore -d platform_db_prod --clean < platform_db_prod.dump
```

- migrate

```sh
docker-compose exec python manage.py showmigrations
docker-compose exec python manage.py makemigrations
docker-compose exec python manage.py migrate
# In case of failing migrations, you can try
docker-compose exec python manage.py migrate --fake
docker-compose exec python manage.py showmigrations
```

## 2. Docker

> At some point, you will want to cleanup your dockers images `docker rmi -f $(docker images -q)`.
> /!\ This will **remove** your images!

### Environments & environment variables

If you want to use the *test* configuration (`debug=True`), please use:

- `docker-compose.yaml`
- [env_dev_template](./env_dev_template)

If you want to use the *production* configuration (`debug=False`), please use:

- `docker-compose.prod.yaml`  
- [env_prod_template](./env_prod_template)

Then, please follow the recommendations inside the relevant template:

- Rename the file as advised in the first line of the template file, for example with `cp env_dev_template .env.dev`
- Update values flagged as `<CHANGE_ME>`

### Run in detached mode and follow docker logs

```sh
# show containers
docker ps

# django app logs
docker logs -f $(docker ps | grep web | awk '{print $1}')
# or
docker-compose -f docker-compose.prod.yml logs --tail=0 --follow

# Show django logs in the "web" container
docker-compose exec web watch cat dev.log

# Open a shell in the "web" container
docker-compose exec web sh
```

## 3. Django

### Python Recommended tools

- [flake8](flake8.pycqa.org/)
- [black](https://github.com/psf/black)
- [safety](https://pyup.io/safety/)

### Djnago settings

You can load different settings when starting django with this:

```sh
python manage.py runserver 0.0.0.0:8000 --settings=dev_platform.settings
```

### Start a django shell in the django container

```sh
docker-compose exec web django-admin shell
```

### Translation

Note that all the content should be written in english. Currently, the languages accepted are
French and English. The site is deployed in French. To realize the translation (refer to the
 [django documentation](https://docs.djangoproject.com/en/3.1/topics/i18n/translation/)
to implement it ), you need to use `gettext_lazy` or `i18n` or even `ngettext` to manage plural.

For example, in Python files, use the syntax: `_("English message to translate in French")` with the **underscore** for `gettext_lazy`.

In the html files, at the beginning of the file, add `{% load i18n %}` and for the text you want to translate, use the tags `{% trans "English message to translate in French" %}` for short messages
and `{% blocktrans trimmed %} text {% endblocktrans %}` for long messages which cannot be written in one line, as this tag handles line breaks.

Then you can do the command:

```sh
django-admin makemessages -l fr
>>> processing locale fr
```

This will gather all the text between the tags in the file `django.po`.
Then, the text to translate should appear after **msgid** `msgid "You must be connected to access this content"`. You must write the translation in the **msgtrs** following `msgstr "Vous devez vous connecter pour accéder à ce contenu"`. Be careful to the 'fuzzy' translations which are inaccurate (Tips: use `Ctrl + f "fuzzy"`). Make all your translations and then do the command:

```sh
django-admin compilemessages
```

Do not forget to add and commit both of the files `django.po` and `django.mo`.

Note that you should use `trimmed` inside `{% blocktrans %}`, to avoid line breaks in the translations:

```sh
{% blocktrans trimmed %}
 text very long
 on several lines
{% endblocktrans %}
```

Without, you will have `\n` in the translation file at the beginning of the `msgid`:

```sh
msgid ""
"\n"
" text very long\n"
 "on several lines"
```

So you need to add it also to the translation (only the first one at the beginning):

```sh
msgstr "\n"
"texte très long"
"sur plusieurs lignes"
```

### Tests

The tests are implemented on each application, assessment and home, in a folder named "tests".
You can add your own tests in these folders or create a new one. The only requirement is to make your python file starting with "test". For more details, refer to the [django documentation](https://docs.djangoproject.com/fr/3.0/topics/testing/overview/).

To run the tests, use the following command:

```sh
docker-compose exec web python manage.py test --verbosity 2
```

If all your tests are passed, you should see something like this:

```sh
Ran 92 tests in 11.590s

OK
Destroying test database for alias 'default' ('test_platform_db')...
```

If one or more of the tests failed, you should have a message like this:

```sh
======================================================================
FAIL: test_order_id_letter (assessment.tests.tests_imports.TestOrderIdTestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/code/assessment/tests/tests_imports.py", line 283, in test_order_id_letter
    self.assertFalse(test_order_id_letter("a,"))
AssertionError: True is not false

----------------------------------------------------------------------
Ran 92 tests in 12.213s

FAILED (failures=1)
Destroying test database for alias 'default' ('test_platform_db')...
```

### Reset migrations

At some point you might want to reset migrations, proceed with caution:

```sh
docker-compose exec web python manage.py showmigrations

# Delete migration files
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

docker-compose exec web python manage.py makemigrations

docker-compose exec web python manage.py showmigrations

docker-compose exec web python manage.py migrate

# In case of errors, you can try
docker-compose exec web python manage.py migrate --fake
```

You can also apply migrations one by one:

```sh
docker-compose exec web python manage.py migrate <APP> <MIGR_NB>
# for example
docker-compose exec web python manage.py migrate home 0002 --fake
docker-compose exec web python manage.py migrate assessment 0002 --fake
```

### Django logs

A logger is created in the settings (dev and prod), called *monitoring*. It creates logs
in the file `prod.log` in the `platform_code` folder.
You can retrieve this logger in python files (in the views for example) with the following code:

```python
logger = logging.getLogger('monitoring')
```

You can then writes new logs in this file with the code `logger.info("text")` for example.
Refer to the [django documentation](https://docs.djangoproject.com/fr/3.1/topics/logging/) for more information.

In order to categorize the logs and to use it in the admin dashboard, a tag is set at the beginning of the log text in the project:

```python
logger.info(f"[organisation_deletion] The organisation {organisation} has been created")
```

You are free to use the tag you want, but some are used for a certain purpose:

- 'error' for all generic errors (400, 403, 404, 500)
- '*action*_error' for errors caught in the code (as excepts)

You can grab django logs inside its container like this:

```sh
# It will be saved where you run the command
docker cp $(docker ps | grep web | awk '{print $1}'):/home/app/web/prod.log .
```

And you can then save it on your local machine, from your local machine:

```sh
scp ubuntu@prod:/home/ubuntu/prod.log .
```

### Django check

You can use the builtin `check` command to get an overview of issues on the plateform:

```sh
docker-compose exec web python manage.py check --deploy
docker-compose exec web python manage.py check --deploy --fail-level WARNING
```

## 4. Postgresql

### Start a postgresql shell

```sh
# check values from .env file
# dev
docker-compose exec db psql -U postgres -W --dbname platform_db
# prod
docker-compose exec db psql -U postgres -W --dbname platform_db_prod
```

### Debugger (pdb, ipdb)

The dev docker-compose is configured to allow you to use debugger breakpoints:

```sh
# grab the django container_id
docker ps | grep web
# attach it
docker attach <container_id>
# you can now use pdb or ipdb directly in the code
import pdb; pdb.set_trace()
```

### Get the postgresql container id

```sh
docker ps | grep postgres | awk '{print $1}'
```

### Dump full db

```sh
docker exec -i -u postgres <CONTAINER_ID> pg_dump -Fc <DB> > <DB>.dump

# prod
docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_dump -Fc platform_db_prod > platform_db_prod.dump

# dev
docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_dump -Fc platform_db > platform_db.dump
```

### Restaure full db

```sh
docker exec -i -u postgres <CONTAINER_ID> pg_restore -d <DB> < <INPUT_FILE>

# prod
docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_restore -d platform_db_prod --clean < platform_db_prod.dump

# dev
docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_restore -d platform_db --clean < platform_db.dump
```

### Dump tables

> /!\ Before running the `dump_tables.sh` script, please update the `<DB>`  and `<TABLE>` values.

```sh
# Login to postgresql container
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -W

# List db
\l

# Connect to platform_db
\c platform_db

# List relations / tables
\dt

# Example script to export one table to csv
DB="platform_db_prod" # or platform_db
TABLE="home_user"

docker exec -u postgres $(docker ps | grep postgres | awk '{print $1}') psql -d ${DB} -c "COPY ${TABLE} TO STDOUT WITH CSV HEADER " > db_${TABLE}.csv
```

### List tables

```sh
assessment_assessment
assessment_choice
assessment_evaluation
assessment_evaluationelement
assessment_evaluationelementweight
assessment_evaluationscore
assessment_externallink
assessment_masterchoice
assessment_masterevaluationelement
assessment_masterevaluationelement_external_links
assessment_mastersection
assessment_scoringsystem
assessment_section
assessment_upgrade
auth_group
auth_group_permissions
auth_permission
django_admin_log
django_content_type
django_migrations
django_session
home_membership
home_organisation
home_pendinginvitation
home_user
home_user_groups
home_user_user_permissions
home_userresources
home_userresources_resources
```

## 5. Tips

### Copy the zip file from the server to your local machine

> Note: you will first need to add your ssh key to the server

```sh
scp <USER>@<IP>:/home/ubuntu/pf-assessment-dsrc/dump_tables/zipped.zip ./
# also works with dump files
```

### Utils

- `htop`: process manager
- `ps aux | grep <name>`: search for an active process
- `history`: shell history

### SEO

Use Lighthouse report! Don't pay!

### Debug & logs

```sh
# Container status
docker ps -a

# Network overview, useful for checking ports
sudo netstat -tlpn
sudo lsof -P -i -n

# GET on port 8000 & 443
curl http://0.0.0.0:8000
curl 0.0.0.0:8000
curl --insecure -I -k localhost:443

# From your local machine
nmap -F preprod.assessment.substra.ai # Fast
nmap -A preprod.assessment.substra.ai # longer
nmap -sV preprod.assessment.substra.ai # version

# Nginx
# Follow logs from container
docker logs -f nginx
docker logs -f web

# nginx logs path
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```
