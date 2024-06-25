#!/bin/bash

MAPS_DIR="maps"


if [ -d "$MAPS_DIR" ]; then
    for file in "$MAPS_DIR"/*; do
        if [ -f "$file" ]; then
        raster2pgsql -C -I -P -t -Y max_rows_per_copy=50 300x200 "$file" > test_raster.sql
        psql postgresql://postgres:mypassword@localhost:8001/WorldMapProject -f test_raster.sql
        fi
    done
else
    echo "Le dossier $MAPS_DIR n'existe pas."
fi
