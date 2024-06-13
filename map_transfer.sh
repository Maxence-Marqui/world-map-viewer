#!/bin/bash

#On créer la table + remplissage avec le premier raster

MAPS_DIR="maps"

#raster2pgsql -C -I -P -t 300x200 a_world_map.tif  > test_raster.sql
#psql -h localhost -p 8001 -U postgres -d WorldMapProject -f test_raster.sql

if [ -d "$MAPS_DIR" ]; then
    for file in "$MAPS_DIR"/*; do
        if [ -f "$file" ]; then
        raster2pgsql -C -I -P -t 300x200 "$file" > test_raster.sql
        psql -h localhost -p 8001 -U postgres -d WorldMapProject -f test_raster.sql
        #ogr2ogr -f "PostgreSQL" PG:"host=localhost:8000 user=postgres password=mypassword dbname=postgres" "$file" -nln world_map
        fi
    done
else
    echo "Le dossier $MAPS_DIR n'existe pas."
fi