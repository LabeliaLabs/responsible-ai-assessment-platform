#######
# DEV #
#######
dev_buildup:
	docker-compose up --build

dev_buildupd:
	docker-compose up --build -d

dev_migr:
	docker-compose exec web python manage.py makemigrations
	docker-compose exec web python manage.py migrate --noinput

dev_static:
	docker-compose exec web python manage.py collectstatic --no-input --clear

dev_admin:
	docker-compose exec web python manage.py createsuperuser

dev_down:
	docker-compose down

dev_test:
	docker-compose exec web python manage.py test --verbosity 2

############
# PRODLIKE #
############
prodlike_buildup:
	docker-compose -f docker-compose.prod-like-local.yml up --build

prodlike_buildupd:
	docker-compose -f docker-compose.prod-like-local.yml up --build -d

prodlike_migr:
	docker-compose -f docker-compose.prod-like-local.yml exec web python manage.py makemigrations
	docker-compose -f docker-compose.prod-like-local.yml exec web python manage.py migrate --noinput

prodlike_static:
	docker-compose -f docker-compose.prod-like-local.yml exec web python manage.py collectstatic --no-input --clear

prodlike_admin:
	docker-compose -f docker-compose.prod-like-local.yml exec web python manage.py createsuperuser

prodlike_down:
	docker-compose -f docker-compose.prod-like-local.yml down

prodlike_test:
	docker-compose -f docker-compose.prod-like-local.yaml exec web python manage.py test --verbosity 2

########
# PROD #
########
prod_buildup:
	docker-compose -f docker-compose.prod.yml up --build

prod_buildupd:
	docker-compose -f docker-compose.prod.yml up --build -d

prod_migr:
	docker-compose -f docker-compose.prod.yml exec web python manage.py makemigrations
	docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput

prod_static:
	docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear

prod_admin:
	docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

prod_down:
	docker-compose -f docker-compose.prod.yml down

prod_test:
	docker-compose -f docker-compose.prod.yaml exec web python manage.py test --verbosity 2
