#!/bin/bash

. ./.env

MAPS_DIR="maps"

docker compose up -d

while ! pg_isready  -q --host=localhost --port=$IMAGE_PORT -U postgres; do
  echo "$(date) - waiting for database to start"
  sleep 2
done

if [ -d "$MAPS_DIR" ]; then
    for file in "$MAPS_DIR"/*; do
        if [ -f "$file" ]; then

        sql_filename=$(basename "$file" .tif).sql
        raster2pgsql -C -I -P -t 300x200 -Y 200 "$file" > ./sql_archives/$sql_filename
        psql postgresql://$POSTGRES_USER:$POSTGRES_DB_PASSWORD@localhost:$IMAGE_PORT/$POSTGRES_DB_NAME -q -f ./sql_archives/$sql_filename
        fi
    done
else
    echo "Folder $MAPS_DIR does not exists."
fi

python3 -m venv world_map_project
source ./world_map_project/bin/activate
pip install -r requirements.txt
