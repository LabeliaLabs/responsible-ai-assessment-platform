docker exec -i -u postgres $(docker ps | grep postgres | awk '{print $1}') pg_dump -Fc platform_db > platform_db_$(date -u +"%Y-%m-%d-%H-%M").dump && \
	zip -r dumps_$(date -u +"%Y-%m-%d-%H-%M").zip ./*.dump && \
	echo Done
