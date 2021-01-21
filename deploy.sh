#!/usr/bin/bash
docker-compose -f docker-compose.prod.yml down && \
	git fetch && \
	git pull --rebase && \
	docker-compose -f docker-compose.prod.yml up --build -d && \
	docker-compose -f docker-compose.prod.yml exec web python manage.py makemigrations && \
	docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput && \
	docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear

