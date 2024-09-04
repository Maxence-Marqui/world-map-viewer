"""import rasterio
from matplotlib import pyplot
import numpy as np


#fig, axes = pyplot.subplots(2, 2)
fig, axes = pyplot.subplots(2)

#src_0_0 = rasterio.open("maps/00_11.tif")
src_0_1 = rasterio.open("maps/00_00.tif")
#src_1_0 = rasterio.open("maps/01_11.tif")
src_1_1 = rasterio.open("maps/01_00.tif")

#dataset_1 = src_0_0.read()[0]
dataset_2 = src_0_1.read()[0]
#dataset_3 = src_1_0.read()[0]
dataset_4 = src_1_1.read()[0]


#dataset_1[dataset_1 <= 0] = 5000
dataset_2[dataset_2 <= 0] = 5000
#dataset_3[dataset_3 <= 0] = 5000
dataset_4[dataset_4 <= 0] = 5000

#axes[0,0].imshow(dataset_1, cmap='pink')
axes[0].imshow(dataset_2, cmap='pink')
#axes[0].imshow(dataset_3, cmap='pink')
axes[1].imshow(dataset_4, cmap='pink')

pyplot.subplots_adjust(hspace=0, wspace=0)
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

    if position_y < 34:
        table_y = 0
        relative_y = position_y
    else:
        position_y -= 34
        table_y = 1 + floor(position_y / 48)
        relative_y = position_y - ((table_y - 1) * 48)

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
        initial_y = relative_y + table[0] * 48 - 14

    initial_x = table_x * 48 + relative_x

    return initial_y, initial_x 

for position in [(32, 41), (33, 41), (34, 19), (34, 20), (34, 21), 
                 (34, 22), (34, 23), (34, 37), (34, 38), (34, 39), (34, 40), (34, 41), 
                 (35, 19), (35, 20), (35, 21), (35, 22), (35, 23), (35, 37), (35, 38), 
                 (35, 39), (35, 40), (35, 41), (36, 19), (36, 20), (36, 21), (36, 22), 
                 (36, 23), (36, 37), (36, 38), (36, 39)]:
    print("---------------")
    table, rid = get_raster_db_locations(position)
    initial_position = get_initial_position(table, rid)

    print("initial position", position, "new position", initial_position)