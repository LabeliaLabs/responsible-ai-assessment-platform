# Deploy

> No deploy friday & use `tmux`!

## Updates

Run this command but check packages to be updated before accepting!!

```sh
sudo apt update && sudo apt upgrade && sudo apt autoremove
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

- Rename the file as avised in the first line of the template file, for example with `cp env_dev_template .env.dev`
- Update values flagged as `<CHANGE_ME>`

## Nginx

```sh
# Ubuntu install
sudo apt install nginx
```

### Server config

```sh
# [only once] Dereference default conf from enabled webstites
sudo unlink /etc/nginx/sites-enabled/default

# Edit your config with the one located in data/nginx/nginx.conf
sudo vi /etc/nginx/sites-available/preprod.assessment.substra.ai
# [temp] use this path for statics: "/home/ubuntu/pf-assessment-dsrc/platform_code/assessment/static/;"

# Link it to the enabled websites
sudo ln -s /etc/nginx/sites-available/preprod.assessment.substra.ai /etc/nginx/sites-enabled

# Test config: will provide feedbacks in case of errors
sudo nginx -t

# Reload nginx: required if the configuration is updated
sudo nginx -s reload
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
# nginx logs path
cat /var/log/nginx/access.log
```

## Certbot

TODO:

- fix cert volumes for docker
- cronjob

```sh
# Ubuntu install
sudo snap install --classic certbot

# First config
sudo certbot --nginx

# Test renew
sudo certbot renew --dry-run

# Renew
sudo certbot renew
```

## ssh config

TODO:

- export conf here (no password, timeout, etc.)
- definir une politique sec (que faire si on découvre un virus sur sa machine locale qui a des clés ssh pour des serveurs => PREVENIR les autres ayant accès à la machine)

## UFW: Uncomplicated FireWall

```sh
# Status/On/Off
sudo ufw status
sudo ufw enable
sudo ufw disable

# Connections status
sudo ufw app list
sudo ufw status numbered

# Allow web connections, only
sudo ufw allow http
sudo ufw allow https

# Custom
sudo ufw delete <ID>
sudo ufw deny out <PORT>
```

As of now, available applications:

- Nginx Full
- Nginx HTTP
- Nginx HTTPS
- OpenSSH

TODO: add port 587 for email

## Fail2ban: IP ban for script kiddies

TODO:

- re-add (disabled during dev/test)
- config documentation

## Docker

### Dev

You can load different settings when starting django with this:

```sh
python manage.py runserver 0.0.0.0:8000 --settings=dev_platform.settings
```

### Prod

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
# or
docker-compose -f docker-compose.prod.yml down -v # --volumes /!\ Removes volumes, including db!
```

## Plateform admin account

contact: nathanael.cretin@substra.org
