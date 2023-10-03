# README for developers

> Reminder: No deploy friday!

Quick access:
1. [Linux](#1-linux)
1. [Docker](#2-docker)
1. [Django](#3-django)
1. [Postgresql](#4-postgresql)
1. [Monthly routines](#5-monthly--yearly-routines)
1. [Tips](#6-tips)

## 1. Linux

> Warning: Treat with caution ssh keys and if you find some viruses on your machine, please let other members of the team know and update your keys once the issue is solved.

### [new server only] Config

On a new server, change unix user password: `whoami` & `sudo passwd`

### SSH

> Note: OVH requires rsa keys in order to add it to the server with the web interface (to regain access to the server in case of reinstallation).
>
> We use port 22222 instead of 22

[OVH ssh keys admin](https://www.ovh.com/manager/dedicated/#/billing/autorenew/ssh)

[quick server config](https://docs.ovh.com/fr/vps/conseils-securisation-vps/)

#### Generate key

> Note: add your public key (`.pub`) to OVH or on a server and keep your private key for yourself!

Generate a dedicated ssh key (RSA 4096 bit key with email as a comment):

```sh
# OVH needs a rsa key if you want to add it from web interface
ssh-keygen -t rsa -b 4096 -C "<<EMAIL_CHANGE_ME>>" -f ~/.ssh/<KEY_NAME_CHANGE_ME>
# if possible use ed25519
ssh-keygen -o -a 100 -t ed25519 -f ~/.ssh/id_ed25519 -C "<<EMAIL_CHANGE_ME>>" -f ~/.ssh/<KEY_NAME_CHANGE_ME>
```

Use the OVH web interface for first login, then you will be authorized to append this ssh key to `.ssh/authorized_keys` or with `ssh-copy-id`. When it's done you can connect to the server you created.

#### Connection

```sh
ssh -i ~/.ssh/<PRIVATE_KEY> <UNIX_USER>@<IP> -p <PORT>
# For example, to connect to the assessment preprod server
ssh -i ~/.ssh/preprod ubuntu@51.68.125.118 -p 22222
```

You can also use this config to avoid some mistakes. When it is ready, you can simply use `ssh preprod` or `ssh prod`! For that edit your `.ssh/config` file as follow:

```sh
Host preprod
        HostName 51.68.125.118
        User ubuntu
        IdentityFile ~/.ssh/<KEY>
        Port 22222

Host prod
        HostName 146.59.147.178
        User ubuntu
        IdentityFile ~/.ssh/<KEY>
        Port 22222
```

#### SCP

- Copy a **local file to a remote host**: `scp {{path/to/local_file}} {{remote_host}}:{{path/to/remote_file}}`

- Copy a file **from a remote host to a local directory**: `scp {{remote_host}}:{{path/to/remote_file}} {{path/to/local_directory}}`

```sh
scp -i ~/.ssh/<CLE> -P <PORT> <UNIX_USER>@<IP>:/home/ubuntu/platform_db_prod.dump ./
# For example
scp -i ~.ssh/preprod -P 22222 ubuntu@51.68.125.118:/home/ubuntu/platform_db_prod.dump ./
# with .ssh/config ready
scp ubuntu@prod:/home/ubuntu/platform_db_prod.dump ./
```

> Please have a look at the /dump/dump_db_prod.sh script: a zip file containing several dumps can be generated and fetched!

### [monthly] Server Update

Use the `update.sh` script (with `./update.sh`), but be careful with programs! For instance, it is better to stop docker (down) before installing docker upgrades.

This script basically does this:

```sh
sudo apt update && \
        sudo apt upgrade && \
        sudo apt autoremove --purge && \
        sudo apt autoclean
```

### [monthly] Docker Update

Check the server updates to be performed:

```sh
apt list --upgradable
```

If there is no Docker update, use `update.sh` (see [Server Update](#monthly-server-update))

If there is Docker updates:

```sh
# Create a dump
make prod_backup

# Save locally your db - file name to be adapted
scp ubuntu@prod:/home/ubuntu/platform_db_prod.dump ./

# Stop Docker
make prod_down

# Update servers
./update.sh

# Restart Docker
make prod_buildupd

# Check if everything is ok. If not, you can restore the DB
docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_restore -d platform_db_prod --clean < platform_db_prod_<DATE>.dump
```

### Install Docker & docker-compose

1. [docker](https://docs.docker.com/engine/install/ubuntu/)
2. Don't forget to `sudo usermod -aG docker $USER`
3. [docker-compose](https://docs.docker.com/compose/install/)

### SSL Certificate installation and renewal

> Note: Use the wildcard domain to catch all sub-domains `*.labelia.org`

#### New instructions for certificate renewal

1. Local preparation: Generate a CSR and a private key with an openssl command provided by the web provider (e.g. Gandi), typically:
  `openssl req -nodes -new -newkey rsa:2048 -sha256 -keyout 'labeliadotorg.key' -out 'labeliadotorg.csr' -subj '/CN=*.labelia.org' -utf8`
1. Generate the certificate via the web provider interface
1. Local preparation: Append the provider intermediary certificate (`cat GandiStandardSSLCA2.pem >> labelia.org.crt` or simply by copy-pasting it within the file)
1. On the server: replace the certificate file `labelia.org.crt` and the private key `labeliadotorg.key` that was used to generate the certificate. They should be located in the `/ssl` folder (in the home folder of the user Ubuntu)
1. Pay attention to the filenames indicated, as they might be referenced in the nginx configuration
1. Stop and relaunch the application so that the new files can be taken into account:
   1. First: `make <env>_down`
   1. Then: `make <env>_buildupd`

#### Details on the above commands

- `-newkey rsa:2048` - Generates a CSR request and a private key using RSA with 2048 bits
- `-sha256` - Use the SHA-2, SHA256 hash algorithm
- `-keyout myserver.key`: Save the private key in the file myserver.key in the folder where the command was executed.
- `-out server.csr`: Save the CSR in the file server.csr in the folder where the command was executed.

When creating a new CSR the openssl command execution might lead to requesting the following inputs:

- `Country name`: Provide the two letter code of your country.
- `State or Province Name`: Write out the name of your state or province; do not use an abbreviation.
- `Locality Name`: Provide the name of your city or town.
- `Organization Name`: Provide the name of your organization, such as the name of your business. This field is optional for Standard certificates standard_certificates, but for Pro and Business certificates, the organization name is mandatory.
- `Organization Unit Name`: Provide the name of your organization unit within your company, such as the IT department.
- `Common Name`: Provide the domain name you are wanting to secure. For more details see the previous section on this page.
- `Email Address`: Provide your email address. The email address is **not mandatory**, but is recommended.
- `A challenge password`: This is a rarely used and optional feature. We recommend you leave this blank.
- `An optional company name`: We also recommend leaving this option blank.

### UFW: Uncomplicated FireWall

> Warning: please make sure you keep an ssh access to the server *before* applying rules!

```sh
# Status/On/Off
sudo ufw status
sudo ufw status verbose
sudo ufw enable
sudo ufw disable

# Connections status
sudo ufw app list
sudo ufw status numbered

# Allow required connections
sudo ufw allow http
sudo ufw allow https
sudo ufw allow 22222
sudo ufw allow 587
sudo ufw allow out 587

# Custom
sudo ufw delete <ID>
sudo ufw deny out <PORT>

# Logs
tail -f /var/log/ufw.log
```

As of now, available applications:

- 80 (Nginx HTTP)
- 443 (Nginx HTTPS)
- 22222 (ssh)
- 587 (email)

Displayed like this:

```sh
sudo ufw status numbered
Status: active

     To                         Action      From
     --                         ------      ----
[ 1] 22222                      ALLOW IN    Anywhere
[ 2] 80/tcp                     ALLOW IN    Anywhere
[ 3] 443/tcp                    ALLOW IN    Anywhere
[ 4] 587                        ALLOW IN    Anywhere
[ 5] 587                        ALLOW OUT   Anywhere                   (out)
[ 6] 22222 (v6)                 ALLOW IN    Anywhere (v6)
[ 7] 80/tcp (v6)                ALLOW IN    Anywhere (v6)
[ 8] 443/tcp (v6)               ALLOW IN    Anywhere (v6)
[ 9] 587 (v6)                   ALLOW IN    Anywhere (v6)
[10] 587 (v6)                   ALLOW OUT   Anywhere (v6)              (out)

```

### Install Antivirus

```sh
# install
sudo apt install clamav

# update signatures
sudo freshclam

# help
clamscan --help

# scan download folder
clamscan -r -i /home/ubuntu/Downloads

# scan all and remove infected files
clamscan -r --remove /
```

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

On Gandi.net interface (just [here](https://admin.gandi.net/domain/3547e9fe-5ee6-11ea-ba20-00163e8fd4b8/substra.ai/records)), set `A` and `AAAA` records to the servers IP (`ipv4` & `ipv6`).

### Use the makefile

Help yourself and use the `Makefile` at the root of the repo! You might need to first install `build-essential` on linux or `make` (with chocolatey package manager for [example](https://chocolatey.org/packages/make) on Windows).

You'll then be able to use `make buildupd` instead of typing `docker-compose up --build -d` and so on!

Available commands:

```sh
# Dev
- up: start
- upd: start in detached mode
- buildup: build image
- buildupd: build in detached mode
- migr: generate migrations & apply it
- migr-show: show migrations
- migr-fake: force migrations
- static: collect statics
- admin: create admin user
- down: stop
- downv: stop & remove volume (including db)
- tests: run tests
- trans-prep: prepare translations (local only)
- translate: make translations (local only)
- backup: create a platform_db_<DATE>.dump from the whole database

# Prod-like-local
- prodlike_up: start
- prodlike_upd: start in detached mode
- prodlike_buildup: build image
- prodlike_buildupd: build in detached mode
- prodlike_migr: generate migrations & apply it
- prodlike_migr-show: show migrations
- prodlike_migr-fake: force migrations
- prodlike_static: collect statics
- prodlike_admin: create admin user
- prodlike_down: stop
- prodlike_downv: stop & remove volume (including db)
- prodlike_tests: run tests

# Preprod
- preprod_up: start
- preprod_upd: start in detached mode
- preprod_buildup: build image
- preprod_buildupd: build in detached mode
- preprod_migr: generate migrations & apply it
- preprod_migr-show: show migrations
- preprod_migr-fake: force migrations
- preprod_static: collect statics
- preprod_admin: create admin user
- preprod_down: stip
- preprod_downv: stop & remove volume (including db)
- preprod_tests: run tests
- preprod_backup: create a platform_db_preprod_<DATE>.dump from the whole database

# Prod
- prod_up: start
- prod_upd: start in detached mode
- prod_buildup: build image
- prod_buildupd: build in detached mode
- prod_migr: generate migrations & apply it
- prod_migr-show: show migrations
- prod_migr-fake: force migrations
- prod_static: collect statics
- prod_admin: create admin user
- prod_down: stip
- prod_downv: stop & remove volume (including db)
- prod_tests: run tests
- prod_backup: create a platform_db_prod_<DATE>.dump from the whole database
```

### Logs

```sh
# live logs
journalctl -f

tail -f /var/log/nginx/access.log;            # container
tail -f /var/log/nginx/error.log;             # container
tail -f /var/log/ufw.log                      # server
tail -f /var/log/letsencrypt/letsencrypt.log  # obsolete

tail -f /var/log/fail2ban.log                 # server
tail -f /var/log/auth.log                     # server
tail -f /var/log/syslog                       # server
```

### Deploy a new release aka deploy on Prod

[optional] Before deploying, if you want to save locally the db, you can run the following commands:

```sh
# Create a dump
make prod_backup

# Save locally your db - file name to be adapted
scp ubuntu@prod:/home/ubuntu/platform_db_prod.dump ./
```

The deploy script (`./deploy.sh`) is ready to handle this but as an overview of the required steps, here is what is happening during a code release:

- [optional] Apply server updates (especially docker updates!): `./update.sh`
- Backup: `docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_dump -Fc platform_db_prod > platform_db_prod.dump` (`make prod_backup`)
- Stop docker: `docker-compose -f docker-compose.prod.yml down` (`make prod_down`)
- Pull the code with the "*deploy*" user (**read-only**): `git fetch && git pull --rebase`
- Re-build the code: `docker-compose -f docker-compose.prod.yml up --build -d` (`make prod_buildupd`)
- Apply migrations (`make prod_migr`):
  - `docker-compose -f docker-compose.prod.yml exec web python manage.py makemigrations`
  - `docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput`
- Update statics (`make prod_static`): `docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear`

If needed, use backup:

- Postgresql `pg_restore`

```sh
docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_restore -d platform_db_prod --clean < platform_db_prod.dump
```

- migrate

```sh
docker-compose -f docker-compose.prod.yml exec python manage.py showmigrations # make prod_migr-show
docker-compose -f docker-compose.prod.yml exec python manage.py makemigrations # make prod_migr
docker-compose -f docker-compose.prod.yml exec python manage.py migrate        # make prod_migr
# In case of failing migrations, you can try
docker-compose -f docker-compose.prod.yml exec python manage.py migrate --fake # make prod_migr-fake
docker-compose -f docker-compose.prod.yml exec python manage.py showmigrations # make prod_migr-show
```

### Deploy on local

You may be required as a dev to deploy locally but also to perform some tests.

```sh
# Switch to the branch you need
git fetch && git pull --rebase
git checkout <branch>

# Build your docker image
make buildup

# Create a super user to login to the platform: you will be requested an email and a password
make admin

# You have now access on your local machine to the platform: http://0.0.0.0:8080/

# Apply translations
make trans-prep
make translate

# You can stop and start again if needed
make down
make up

# For Dev: run tests
make tests

# Delete your build
make downv
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

### Django settings

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
to implement it), you need to use `gettext_lazy` or `i18n` or even `ngettext` to manage plural.

For example, in Python files, use the syntax: `_("English message to translate in French")` with the **underscore** for `gettext_lazy`.

In the html files, at the beginning of the file, add `{% load i18n %}` and for the text you want to translate, use the tags `{% trans "English message to translate in French" %}` for short messages
and `{% blocktrans trimmed %} text {% endblocktrans %}` for long messages which cannot be written in one line, as this tag handles line breaks.

Then you can do the command:

```sh
django-admin makemessages -l fr
>>> processing locale fr
```

or use `make trans-prep`.

This will gather all the text between the tags in the file `django.po`.
Then, the text to translate should appear after **msgid** `msgid "You must be connected to access this content"`. You must write the translation in the **msgtrs** following `msgstr "Vous devez vous connecter pour accéder à ce contenu"`. Be careful to the 'fuzzy' translations which are inaccurate (Tips: use `Ctrl + f "fuzzy"`). Make all your translations and then do the command:

```sh
django-admin compilemessages
```

Or use `make translate`.

Do not forget to add and commit both of the files `django.po` and `django.mo`.

If you want to do translation in javascript files, you can use gettext, or other django functions.
Then, use the command:

```sh
django-admin makemessages -d djangojs -l fr
>>> processing locale fr
```

Check the translations to apply in the file djangojs.po
You need to compile the messages with the same command that for python files.

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
# or
make tests
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

docker-compose exec web python manage.py makemigrations # make migr
docker-compose exec web python manage.py showmigrations # make migr-show
docker-compose exec web python manage.py migrate        # make migr
# In case of errors, you can try
docker-compose exec web python manage.py migrate --fake # make migr-fake
# You can also try to apply migrations one by one
docker-compose exec web python manage.py migrate home 0002 --fake
docker-compose exec web python manage.py migrate assessment 0002 --fake
docker-compose exec web python manage.py migrate home 0003
docker-compose exec web python manage.py migrate assessment 0003
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
docker cp $(docker ps | grep web | awk '{print $1}'):/home/app/web/prod.log ./
```

And you can then save it on your local machine, from your local machine:

```sh
scp ubuntu@prod:/home/ubuntu/prod.log ./
```

### Django check

You can use the builtin `check` command to get an overview of issues on the plateform:

```sh
docker-compose exec web python manage.py check --deploy
docker-compose exec web python manage.py check --deploy --fail-level WARNING
```

### Django admin

```sh
django-admin check                       # Checks the entire django project for potential problems
django-admin changepassword <username>   # Allows changing a user’s password. It prompts you to enter a new password twice for the given user.
django-admin clearsessions               # Can be run as a cron job or directly to clean out expired sessions.
django-admin collectstatic               # Helps to collect all the static files in the one mentioned directory
django-admin createsuperuser             # Creates a superuser account (a user who has all permissions).
django-admin compilemessages             # Compiles .po files to .mo files for use with builtin gettext support
django-admin createcachetable            # Creates the tables needed to use the SQL cache backend.
django-admin dbshell                     # Runs the command-line client for specified database, or the default database if none is provided.
django-admin diffsettings                # Displays differences between the current settings.py and Django's default settings.
django-admin dumpdata                    # Output the contents of the database as a fixture of the given format (using each model's default manager unless --all is specified).
django-admin flush                       # Removes ALL DATA from the database, including data added during migrations. Does not achieve a "fresh install" state.
django-admin inspectdb                   # Introspects the database tables in the given database and outputs a Django model module.
django-admin loaddata                    # Installs the named fixture(s) in the database.
django-admin makemessages                # Runs over the entire source tree of the current directory and pulls out all strings marked for translation. It creates (or updates) a message file in the conf/locale (in the django tree) or locale (for projects and applications) directory. You must run this command with one of either the --locale, --exclude, or --all options.
django-admin help                        # display usage information and a list of the commands provided by each application
django-admin makemigrations              # create new migrations to the database based on the changes detected in the models
django-admin migrate                     # synchronize the database state with your current state project models and migrations
django-admin remove_stale_contenttypes   # Deletes stale content types (from deleted models) in your database.y.
django-admin runserver <port>            # start the development webserver at 127.0.0.1 with the port <port> default 8000
django-admin sendtestemail               # Sends a test email to the email addresses specified as arguments.
django-admin shell                       # Runs a Python interactive interpreter. Tries to use IPython or bpython, if one of them is available. Any standard input is executed as code.
django-admin showmigrations              # Shows all available migrations for the current project.
django-admin sqlflush                    # Returns a list of the SQL statements required to return all tables in the database to the state they were in just after they were installed.
django-admin sqlmigrate                  # Prints the SQL statements for the named migration.
django-admin sqlsequencereset            # Prints the SQL statements for resetting sequences for the given app name(s).
django-admin squashmigrations            # Squashes an existing set of migrations (from first until specified) into a single new one.
django-admin startapp <Appname>          # create a new django application with the specified name
django-admin startproject <ProjectName>  # create a new project directory structure
django-admin testserver                  # Runs a development server with data from the given fixture(s).
django-admin version                     # display the current django version
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
# or
make prod_backup

# dev
docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_dump -Fc platform_db > platform_db.dump
# or
make backup
```

### Restaure full db

```sh
docker exec -i -u postgres <CONTAINER_ID> pg_restore -d <DB> < <INPUT_FILE>

# prod ex.
docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_restore -d platform_db_prod --clean < platform_db_prod.dump

# dev ex.
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
assessment_elementchangelog
assessment_evaluation
assessment_evaluationelement
assessment_evaluationelementweight
assessment_evaluationscore
assessment_externallink
assessment_labelling
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
home_footer
home_membership
home_organisation
home_pendinginvitation
home_platformmanagement
home_releasenot
home_user
home_user_groups
home_user_user_permissions
home_userresources
home_userresources_resources
```

## 5. Monthly & Yearly routines

Once a month:

- Check [antivirus](#install-antivirus). In doubt, scan the whole system with `clamscan -r -i /`, but it will be long...
- Check [server updates](#monthly-server-update), including [Docker updates](#monthly-docker-update)

Once a year:

- [Renew SSL certificate](#new-instructions-for-certificate-renewal)

For these types of interventions, the typical sequence of actions is the following:

1. Backup: `./dump/dump_<env db>.sh` (or `make <env>_backup`)
1. Down: `make <env>_down`
1. Perform specific action (e.g. server updates, certificate renewal, new release, etc.)
1. Build & up : `make <env>_buildupd`

And in case of changes in the application code, add the below commands (or use the deployment script which packages all required commands in that case, see [here](#deploy-a-new-release-aka-deploy-on-prod))

1. Migrations : `make <env>_migr` (or see the 2 associated commands)
1. Static : `make <env>_static`

And in case of recreation of the database:

1. Superuser : `make <env>_admin`

## 6. Tips

### Utils

- `htop`: process manager
- `ps aux | grep <name>`: search for an active process
- `history`: shell history
- `ncdu`: disk usage explorer
- `tldr`: install it on your local machine ([repo](https://github.com/tldr-pages/tldr))

### SEO

Use Lighthouse report! Don't pay for hacky stuff!

### Debug & logs

```sh
# Container status (all)
docker ps -a

# Network overview, useful for checking ports
sudo netstat -tlpn
sudo lsof -P -i -n

# GET on port 8000 & 443
curl http://0.0.0.0:8000
curl 0.0.0.0:8000
curl --insecure -I -k localhost:443

# From your local machine
nmap -F preprod.assessment.labelia.org   # Fast
nmap -A preprod.assessment.labelia.org   # longer
nmap -sV preprod.assessment.labelia.org  # version

# Nginx
# Follow logs from container
docker logs -f nginx
docker logs -f web

# nginx logs path (inside the nginx container)
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### [not required] Nginx

> Nginx is dockerized, so the following is not required, but it is still a good source of knowledge. Configuration files are located in the `nginx` folder.

```sh
# Ubuntu install
sudo apt install nginx

# [only once] Dereference default conf from enabled websites
sudo unlink /etc/nginx/sites-enabled/default

# Edit your config with the one located in data/nginx/nginx.conf
sudo vi /etc/nginx/sites-available/preprod.assessment.labelia.org
# [temp] use this path for statics: "/home/ubuntu/pf-assessment-dsrc/platform_code/assessment/static/;"

# Link it to the enabled websites
sudo ln -s /etc/nginx/sites-available/preprod.assessment.labelia.org /etc/nginx/sites-enabled

# Test config & reload nginx: will provide feedbacks in case of errors
sudo nginx -t && sudo nginx -s reload
sudo nginx -T
```

### [not required] Port forward

> This is required anymore, but it's a good piece of knowledge

Enable `sysctl net.ipv4.forward` by editing `/etc/sysctl.conf` & `/etc/ufw/sysctl.conf` and running `sysctl -p`.

Ufw: `/etc/ufw/before.rules`:

```sh
*nat
:PREROUTING ACCEPT [0:0]
-A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8000
COMMIT
```

And reload `ufw`

```sh
sudo ufw disable && sudo ufw enable
sudo service ufw restart
sudo ufw reload
sudo systemctl restart ufw
```
