#######
# DEV #
#######

up:
	docker compose up

upd:
	docker compose up -d

buildup:
	docker compose up --build

buildupd:
	docker compose up --build -d

migr:
	docker compose exec web python manage.py makemigrations
	docker compose exec web python manage.py migrate --noinput

migr-show:
	docker compose exec web python manage.py showmigrations

migr-fake:
	docker compose exec web python manage.py migrate --fake

static:
	docker compose exec web python manage.py collectstatic --no-input --clear

admin:
	docker compose exec web python manage.py createsuperuser

down:
	docker compose down

downv:
	docker compose down -v

tests:
	docker compose exec web python manage.py test --verbosity 2

trans-prep:
	django-admin makemessages -l fr

translate:
	django-admin compilemessages

backup:
	./dump/dump_db.sh

exec:
	docker compose exec web ./manage.py $(filter-out $@,$(MAKECMDGOALS))

restart:
	docker compose stop web && docker compose up -d web

############
# PRODLIKE #
############

prodlike_up:
	docker compose -f docker-compose.prod-like-local.yml up

prodlike_upd:
	docker compose -f docker-compose.prod-like-local.yml up -d

prodlike_buildup:
	docker compose -f docker-compose.prod-like-local.yml up --build

prodlike_buildupd:
	docker compose -f docker-compose.prod-like-local.yml up --build -d

prodlike_migr:
	docker compose -f docker-compose.prod-like-local.yml exec web python manage.py makemigrations
	docker compose -f docker-compose.prod-like-local.yml exec web python manage.py migrate --noinput

prodlike_migr-show:
	docker compose -f docker-compose.prod-like-local.yml exec web python manage.py showmigrations

prodlike_migr-fake:
	docker compose -f docker-compose.prod-like-local.yml exec web python manage.py migrate --fake

prodlike_static:
	docker compose -f docker-compose.prod-like-local.yml exec web python manage.py collectstatic --no-input --clear

prodlike_admin:
	docker compose -f docker-compose.prod-like-local.yml exec web python manage.py createsuperuser

prodlike_down:
	docker compose -f docker-compose.prod-like-local.yml down

prodlike_downv:
	docker compose -f docker-compose.prod-like-local.yml down -v

prodlike_tests:
	docker compose -f docker-compose.prod-like-local.yaml exec web python manage.py test --verbosity 2

###########
# PREPROD #
###########

preprod_up:
	docker compose -f docker-compose.preprod.yml up

preprod_upd:
	docker compose -f docker-compose.preprod.yml up -d

preprod_buildup:
	docker compose -f docker-compose.preprod.yml up --build

preprod_buildupd:
	docker compose -f docker-compose.preprod.yml up --build -d

preprod_migr:
	docker compose -f docker-compose.preprod.yml exec web python manage.py makemigrations
	docker compose -f docker-compose.preprod.yml exec web python manage.py migrate --noinput

preprod_migr-show:
	docker compose -f docker-compose.preprod.yml exec web python manage.py showmigrations

preprod_migr-fake:
	docker compose -f docker-compose.preprod.yml exec web python manage.py migrate --fake

preprod_static:
	docker compose -f docker-compose.preprod.yml exec web python manage.py collectstatic --no-input --clear

preprod_admin:
	docker compose -f docker-compose.preprod.yml exec web python manage.py createsuperuser

preprod_down:
	docker compose -f docker-compose.preprod.yml down

preprod_downv:
	docker compose -f docker-compose.preprod.yml down -v

preprod_tests:
	docker compose -f docker-compose.preprod.yaml exec web python manage.py test --verbosity 2

preprod_backup:
	./dump/dump_db_preprod.sh

########
# PROD #
########

prod_up:
	docker compose -f docker-compose.prod.yml up

prod_upd:
	docker compose -f docker-compose.prod.yml up -d

prod_buildup:
	docker compose -f docker-compose.prod.yml up --build

prod_buildupd:
	docker compose -f docker-compose.prod.yml up --build -d

prod_migr:
	docker compose -f docker-compose.prod.yml exec web python manage.py makemigrations
	docker compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput

prod_migr-show:
	docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations

prod_migr-fake:
	docker compose -f docker-compose.prod.yml exec web python manage.py migrate --fake

prod_static:
	docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear

prod_admin:
	docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

prod_down:
	docker compose -f docker-compose.prod.yml down

prod_downv:
	docker compose -f docker-compose.prod.yml down -v

prod_tests:
	docker compose -f docker-compose.prod.yaml exec web python manage.py test --verbosity 2

prod_backup:
	./dump/dump_db_prod.sh
