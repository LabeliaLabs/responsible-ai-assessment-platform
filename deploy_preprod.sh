#!/usr/bin/bash

docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_dump -Fc platform_db_prod > dump/platform_db_preprod_$(date -u +"%Y-%m-%d-%H-%M").dump && \

docker-compose -f docker-compose.preprod.yml down && \
	git fetch && \
	git pull --rebase && \
	docker-compose -f docker-compose.preprod.yml up --build -d && \
	docker-compose -f docker-compose.preprod.yml exec web python manage.py makemigrations && \
	docker-compose -f docker-compose.preprod.yml exec web python manage.py migrate --noinput && \
	docker-compose -f docker-compose.preprod.yml exec web python manage.py collectstatic --no-input --clear
