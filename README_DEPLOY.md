# Deploy

> No deploy friday & use `tmux`!
> At some point, you will want to cleanup your dockers images `docker rmi -f $(docker images -q)`.
> /!\ This will **remove** your images!

## Updates

Run this command but check packages to be updated before accepting!!

```sh
sudo apt update && \
        sudo apt upgrade && \
        sudo apt autoremove --purge && \
        sudo apt autoclean
```

## Git

TODO: readonly token

## Environment variables

If you want to use the *test* configuration, please use:

- `docker-compose.yaml`
- [env_dev_template](./env_dev_template)

If you want to use the *production* configuration, please use:

- `docker-compose.prod.yaml`  
- [env_prod_template](./env_prod_template)

Then, please follow the recommendations inside the relevant template:

- Rename the file as advised in the first line of the template file, for example with `cp env_dev_template .env.dev`
- Update values flagged as `<CHANGE_ME>`

## Nginx

```sh
# Ubuntu install
sudo apt install nginx
```

### Server config

```sh
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

### Debug

```sh
# Container status
docker ps -a

# Network overview, useful for checking ports
sudo netstat -tlpn
sudo lsof -P -i -n

# Nginx
# Follow logs from container
docker logs -f nginx
docker logs -f web

# GET on port 8000 & 443
curl http://0.0.0.0:8000
curl 0.0.0.0:8000
curl --insecure -I -k localhost:443

# From your local machine
nmap -F preprod.assessment.substra.ai # Fast
nmap -A preprod.assessment.substra.ai # longer
nmap -sV preprod.assessment.substra.ai # version

# nginx logs path
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## Certbot

TODO: cronjob renew but faut pas que ça dérape...

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

## ssh config

TODO:

- change port 22
- unix user  
- export conf here (no password, timeout, etc.)
- definir une politique sec (que faire si on découvre un virus sur sa machine locale qui a des clés ssh pour des serveurs => PREVENIR les autres ayant accès à la machine)

## UFW: Uncomplicated FireWall

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

### [WIP] Port forward

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

## Fail2ban: IP ban for script kiddies

Ubuntu package: <https://packages.ubuntu.com/search?keywords=fail2ban>

```sh
# Install
curl -LO http://fr.archive.ubuntu.com/ubuntu/pool/universe/f/fail2ban/fail2ban_0.11.1-1_all.deb
sudo dpkg -i fail2ban_0.11.1-1_all.deb

# Check service status 
sudo service fail2ban status

# Logs
tail -f /var/log/fail2ban.log
```

## Docker

### Dev

You can load different settings when starting django with this:

```sh
python manage.py runserver 0.0.0.0:8000 --settings=dev_platform.settings
```

You can follow logged elements live with:

```sh
docker-compose exec web watch cat dev.log
```

#### Translation

Note that all the content should be written in english. Currently, the languages accepted are
French and English. The site is deployed in French. To realize the translation (refer to the
 [django documentation](https://docs.djangoproject.com/en/3.1/topics/i18n/translation/)
to implement it ), you need to use `gettext_lazy` or `i18n` or even `ngettext` to manage plural.

For example, in Python files, use the syntax: `_("English message to translate in French")` with the **underscore** for `gettext_lazy`.

In the html files, at the beginning of the file, add `{% load i18n %}` and for the text you want to translate, 
use the tags `{% trans "English message to translate in French" %}` for short messages
and `{% blocktrans trimmed %} text {% endblocktrans %}` for long messages which cannot be written in one line, as this tag handles line breaks. 

Then you can do the command:

```sh
django-admin makemessages -l fr
>>> processing locale fr
```

This will gather all the text between the tags in the file `django.po`. 
Then, the text to translate should appear after **msgid** `msgid "You must be connected to access this content"`. 
You must write the translation in the **msgtrs** following `msgstr "Vous devez vous connecter pour accéder à ce contenu"`. 
Be careful to the 'fuzzy' translations which are inaccurate (Tips: use `Ctrl + f "fuzzy"`). 
Make all your translations and then do the command:

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
You can add your own tests in these folders or create a new one. The only requirement is to make your python
file starting with "test". 
For more details, refer to the [django documentation](https://docs.djangoproject.com/fr/3.0/topics/testing/overview/).

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

### Prod

Use, **with caution**, the `deploy.sh` script

```sh
# Power up Docker & build image, in detached mode
docker-compose -f docker-compose.prod.yml up --build -d

# Create migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py makemigrations

# Apply migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput

# Collectstatic
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear

# [only once] Createsuperuser (please do not create too many admin users)
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Turn off Docker
docker-compose -f docker-compose.prod.yml down
# or /!\ Removes volumes, including db!
docker-compose -f docker-compose.prod.yml down -v # --volumes 
```

## Logs

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

## Django logs

A logger is created in the settings (dev and prod), called *monitoring*. It creates logs
in the file `prod.log` in the `platform_code` folder.
You can retrieve this logger in python files (in the views for example) with the following code:

```python
logger = logging.getLogger('monitoring')
```

You can then writes new logs in this file with the code `logger.info("text")` for example.
Refer to the [django documentation](https://docs.djangoproject.com/fr/3.1/topics/logging/) for more information.

In order to categorize the logs and to use it in the admin dashboard, a tag is set at the beginning of the log text in 
the project:

```python
logger.info(f"[organisation_deletion] The organisation {organisation} has been created")
```

You are free to use the tag you want, but some are used for a certain purpose:

- 'error' for all generic errors (400, 403, 404, 500)
- '*action*_error' for errors caught in the code (as excepts)


## Platform admin account

contact: nathanael.cretin@substra.org
