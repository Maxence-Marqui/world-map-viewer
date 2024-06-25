"""import rasterio
from matplotlib import pyplot
src = rasterio.open("maps/00_01.tif")

dataset = src.read()[0]

print(dataset.shape)

dataset[dataset <= 0] = 5000

pyplot.imshow(dataset, cmap='pink')
pyplot.show()"""


from functools import lru_cache
from math import floor
from typing import Tuple

@lru_cache(maxsize=None)
def get_raster_db_locations(position: Tuple[int, int]):

    table, relative_position = get_table_and_relative_position(position)
    rid = get_rid(relative_position)

    print("table", table,"position_db", relative_position, "rid", rid)

    return (table, rid)

@lru_cache(maxsize=None)
def get_table_and_relative_position(position: Tuple[int, int]):

    position_y = position[0]

    if position_y <= 33:
        table_y = 0
        relative_y = position_y
    else:
        position_y -= 33
        table_y = 1 + floor(position_y / 48)
        relative_y = position_y - ((table_y - 1) * 48)
        #if relative_y - 16

    table_x = floor(position[1] / 48)
    relative_x = position[1] - (table_x * 48)

    return (table_y, table_x), (relative_y, relative_x)

@lru_cache(maxsize=None)
def get_rid(position: Tuple[int, int]):
    return position[0] * 48 + position[1] + 1

# Fonction inverse
def get_initial_position(table: Tuple[int, int], rid: int) -> Tuple[int, int]:

    relative_position = get_position_from_rid(rid)
    initial_position = get_initial_from_table_and_relative_position(table, relative_position)
    
    return initial_position

@lru_cache(maxsize=None)
def get_position_from_rid(rid: int) -> Tuple[int, int]:
    relative_y = (rid - 1) // 48
    relative_x = (rid - 1) % 48
    return relative_y, relative_x

@lru_cache(maxsize=None)
def get_initial_from_table_and_relative_position(table: Tuple[int, int], relative_position: Tuple[int, int]) -> Tuple[int, int]:

    table_y, table_x = table
    relative_y, relative_x = relative_position

    if table_y == 0:
        initial_y = relative_y
    else:            
        initial_y = relative_y + table[0] * 48 - 16

    initial_x = table_x * 48 + relative_x

    return initial_y + 1, initial_x 

for position in [(79, 45), (79, 46), (79, 47), (80, 45), (80, 46), (80, 47), (81, 45), (81, 46), (81, 47)]:
    print("---------------")
    table, rid = get_raster_db_locations(position)
    initial_position = get_initial_position(table, rid)

    print("position", position, "initial_position", initial_position)
