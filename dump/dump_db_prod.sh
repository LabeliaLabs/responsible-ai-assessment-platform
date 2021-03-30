docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_dump -Fc platform_db_prod > platform_db_prod_$(date -u +"%Y-%m-%d-%H-%M").dump && \
	zip -r dumps_prod_$(date -u +"%Y-%m-%d-%H-%M").zip ./*.dump && \
	echo Done
