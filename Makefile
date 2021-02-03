#######
# DEV #
#######

up:
	docker-compose up

buildup:
	docker-compose up --build

buildupd:
	docker-compose up --build -d

migr:
	docker-compose exec web python manage.py makemigrations
	docker-compose exec web python manage.py migrate --noinput

static:
	docker-compose exec web python manage.py collectstatic --no-input --clear

admin:
	docker-compose exec web python manage.py createsuperuser

down:
	docker-compose down
	
downv:
	docker-compose down -v

tests:
	docker-compose exec web python manage.py test --verbosity 2

dump:
	docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_dump -Fc platform_db > platform_db.dump && echo "Dumped"

restore:
	docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_restore -d platform_db --clean < platform_db.dump && echo "Restored"

############
# PRODLIKE #
############

prodlike_up:
	docker-compose -f docker-compose.prod-like-local.yml up

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

prodlike_downv:
	docker-compose -f docker-compose.prod-like-local.yml down -v

prodlike_tests:
	docker-compose -f docker-compose.prod-like-local.yaml exec web python manage.py test --verbosity 2

prodlike_dump:
	docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_dump -Fc platform_db_prod > platform_db_prod.dump && echo "Dumped"

prodlike_restore:
	docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_restore -d platform_db_prod --clean < platform_db_prod.dump && echo "Restored"

########
# PROD #
########

prod_up:
	docker-compose -f docker-compose.prod.yml up

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

prod_downv:
	docker-compose -f docker-compose.prod.yml down -v

prod_tests:
	docker-compose -f docker-compose.prod.yaml exec web python manage.py test --verbosity 2

prod_dump:
	docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_dump -Fc platform_db_prod > platform_db_prod.dump && echo "Dumped"

prod_restore:
	docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_restore -d platform_db_prod --clean < platform_db_prod.dump && echo "Restored"
