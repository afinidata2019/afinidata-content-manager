#!/usr/bin/env bash

echo "Loading .env in bash"
set -a; source .env; set +a

PORT=${D_CONTENT_MANAGER_SERVICE_PORT:=8202}
PORT=${MY_PORT:=$PORT}
echo "DEPLOYMENT_TYPE=$DEPLOYMENT_TYPE"
# if [ "$DEPLOYMENT_TYPE" == 'dev' ]
# then
    pipenv run python ./manage.py makemigrations
    pipenv run python ./manage.py migrate
    pipenv run python ./manage.py runserver 0.0.0.0:"$PORT"
# else
#     pipenv run gunicorn -b 0.0.0.0:"$PORT" -w 4 content_manager.wsgi
# fi

