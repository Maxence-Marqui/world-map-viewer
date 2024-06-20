import psycopg2
from typing import Generator, Tuple, List, Dict
from time import time
from functools import lru_cache, wraps
from pygame_config import *
from math import floor
import numpy as np
from area import Area


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print('func:%r args:[%r, %r] took: %2.4f sec' % \
          (f.__name__, args, kw, te-ts))
        return result
    return wrap

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


def get_multiple_rasters(map_dict: Dict[Tuple[int,int], Area],  table: Tuple[int, int], rids: List[int]):
    table_name = format_table_name(table[0], table[1])
    print(f"Loading {len(rids)} areas from table {table_name}...")

    rids = tuple(rids)
    request = f"""SELECT rid, ST_AsGDALRaster(rast, 'GTiff') FROM "{table_name}" WHERE rid IN %s"""

    try:
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute(request, (rids,))
        areas = cursor.fetchall()
    except Exception as e:
        print(e)
        areas = []
    finally:
        cursor.close()
        connection.close()
    
    for area in areas:
        position = get_raster_position(area[0], table)
        map_dict[position].add_real_raster(area[1])
    
    #print(f"Finished loading {len(rids)} areas...")

@lru_cache(maxsize=None)
def get_table_and_relative_position(position):
    table_y = floor(position[0] / 48)
    table_x = floor(position[1] / 48)
        
    relative_y = position[0] - (table_y * 48)
    relative_x = position[1] - (table_x * 48)
    return (table_y, table_x), (relative_y, relative_x)

@lru_cache(maxsize=None)
def get_raster_locations(position):
    table, relative_position = get_table_and_relative_position(position)
    rid = get_rid(relative_position)

    return (table, rid)


@lru_cache(maxsize=None)
def get_raster_position(rid, table: Tuple[int, int]):
    rid -= 1
    horizontal_position = int(rid % 48) + table[1] * 48
    vertical_position = int(rid / 48) + table[0] * 48
    return (vertical_position, horizontal_position)

@lru_cache(maxsize=None)
def get_rid(position: Tuple[int,int]):
    return position[0] * 48 + position[1] + 1

@lru_cache(maxsize=None)
def interpolate(color_a, color_b, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(color_a, color_b))

@lru_cache(maxsize=None)
def round_to_nearest_x(x, base_value):
    return x * round(base_value / x)

def format_table_name(y, x):
    y = f"{y:02}"
    x = f"{x:02}"
    return f"{y}_{x}"

def generate_intervals(start, end, step):
    intervals = []
    for i in range(start, end + step, step):
        intervals.append((i, i + step - 1 ,interpolate(LIGHTEST_GREEN, DARKEST_GREEN, (i + step - 1) / end)))

    return intervals

@lru_cache(maxsize=None)
def find_changed_indices(original_array, modified_array):
    # Trouver les indices où les valeurs sont différentes
        changed_indices = np.argwhere(original_array != modified_array)
        return changed_indices

def chunk_array(array, chunk_size: int = 5) -> Generator[List, None, None]:
    """Divise un array en sous-groupes de taille maximale chunk_size."""
    for i in range(0, len(array), chunk_size):
        yield array[i:i + chunk_size]

@lru_cache(maxsize=None)
def get_node_color(node_value):
    if node_value == 0: return BLUE
    elif np.isnan(node_value) or node_value < 0 or node_value > 5000: return LIGHT_GREY
    else: return interpolate(LIGHTEST_GREEN, DARKEST_GREEN, node_value / 2000)