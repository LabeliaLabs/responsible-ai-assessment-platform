# Dev Setup

> Reminder: No deploy friday!

- [Dev Setup](#dev-setup)
  - [1. Docker](#2-docker)
    - [Environments & environment variables](#environments--environment-variables)
    - [Run in detached mode and follow docker logs](#run-in-detached-mode-and-follow-docker-logs)
  - [2. Django](#3-django)
    - [Python Recommended tools](#python-recommended-tools)
    - [Django settings](#django-settings)
    - [Start a django shell in the django container](#start-a-django-shell-in-the-django-container)
    - [Translation](#translation)
    - [Tests](#tests)
    - [Reset migrations](#reset-migrations)
    - [Django logs](#django-logs)
    - [Django check](#django-check)
    - [Django admin](#django-admin)
  - [3. Postgresql](#4-postgresql)
    - [Start a postgresql shell](#start-a-postgresql-shell)
    - [Debugger (pdb, ipdb)](#debugger-pdb-ipdb)
    - [Get the postgresql container id](#get-the-postgresql-container-id)
    - [Dump full db](#dump-full-db)
    - [Restaure full db](#restaure-full-db)
    - [Dump tables](#dump-tables)
    - [List tables](#list-tables)
  - [4. Monthly routines](#5-monthly-routines)
  - [5. Tips](#6-tips)
    - [Utils](#utils)
    - [SEO](#seo)
    - [Debug & logs](#debug--logs)

## 1. Docker

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

## 2. Django

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
to implement it ), you need to use `gettext_lazy` or `i18n` or even `ngettext` to manage plural.

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

## 3. Postgresql

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

## 4. Monthly routines

Once a month:

- Check [antivirus](#install-antivirus). In doubt, scan the whole system with `clamscan -r -i /`, but it will be long...
- Check [server updates](#monthly-server-update), including [Docker updates](#monthly-docker-update)

## 5. Tips

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
