#!/bin/bash

CONTAINER="" # docker ps | grep postgres | awk '{print $1}'
DB="platform_db_prod" # or platform_db
TABLES=(
    assessment_assessment
    assessment_choice
    assessment_evaluation
    assessment_evaluationelement
    assessment_evaluationelementweight
    assessment_evaluationscore
    assessment_externallink
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
    home_membership
    home_organisation
    home_pendinginvitation
    home_platformmanagement
    home_user
    home_user_groups
    home_user_user_permissions
    home_userresources
    home_userresources_resources
)

for table in ${TABLES[@]}
do
    echo "Dump table" $table
    docker exec -u postgres ${CONTAINER} psql -d ${DB} -c "COPY $table TO STDOUT WITH CSV HEADER " > db_$table.csv

done
echo "Tables exported"

zip -r zipped.zip ./db_*
echo "Tables exported to zipped.zip"

echo "Cleanup"
rm ./db_*

echo "Done"
