import psycopg2

def connect_to_db():
    """Open a connexion to the database using the .env informations
    """
    connexion = psycopg2.connect(
        host="localhost",
        database="WorldMapProject",
        user="postgres",
        password="mypassword",
        port=8001)

    return connexion

def get_raster(rid):

    request = """SELECT ST_AsGDALRaster(rast, 'GTiff') FROM a_world_map WHERE rid = {}""".format(rid)

    try:
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute(request)
        area = cursor.fetchone()[0]
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        connection.close()
    
    if not area:
        return False
    return area


def get_multiple_rasters(table, rids):
    rids = tuple(rids)
    request = f"""SELECT rid, ST_AsGDALRaster(rast, 'GTiff') FROM "{table}" WHERE rid IN %s"""

    try:
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute(request, (rids,))
        areas = cursor.fetchall()
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        connection.close()
    
    if not areas:
        return False
    return areas
