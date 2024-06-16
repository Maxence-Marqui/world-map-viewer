import tempfile
import rasterio
from db_helpers import get_raster, get_multiple_rasters

from pygame_config import *
from typing import List, Tuple
from functools import lru_cache, wraps
import numpy as np

from time import time

def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print('func:%r args:[%r, %r] took: %2.8f sec' % \
          (f.__name__, args, kw, te-ts))
        return result
    return wrap


class Area:
    def __init__(self, rid: int, raster_position: Tuple[int, int], raster_binary) -> None:
        self.rid: int = rid
        self.position = raster_position
        self.raster: np.ndarray = self.convert_binary_to_np(raster_binary)
        print(f"Loaded Raster {self.rid}: {self.position}")

    def load_area(self) -> bool:
        if self.raster: return
        
        area = get_raster(self.rid)
        if not area:
            print(f"Error loading Raster {self.rid}: {self.position}")
        
        with tempfile.NamedTemporaryFile() as tmpfile:
            tmpfile.write(area)
            with rasterio.open(tmpfile.name) as dataset:
                self.raster = dataset.read()[0]

        print(f"Loaded Raster {self.rid}: {self.position}")
        return True
   
    def convert_binary_to_np(self, raster_binary):

        with tempfile.NamedTemporaryFile() as tmpfile:
            tmpfile.write(raster_binary)
            with rasterio.open(tmpfile.name) as dataset:
                return dataset.read()[0]

    
    def get_displayed_nodes(self, zoom_level: int, indexes: dict):

        starting_y = indexes["starting_y"] 
        ending_y = indexes["ending_y"]

        starting_x = indexes["starting_x"] 
        ending_x = indexes["ending_x"]

        sub_raster = self.get_zoomed_raster(self.raster, zoom_level)
        sub_raster = self.get_subset_of_nodes(sub_raster, starting_y, ending_y, starting_x, ending_x)
        return sub_raster
    
    def get_subset_of_nodes(self, raster,starting_y, ending_y, starting_x, ending_x):
        subset = raster[starting_y:ending_y, starting_x:ending_x]
        return subset
    
    def get_zoomed_raster(self, raster, zoom_level):
        if zoom_level == 5:
            return raster
        
        if zoom_level == 4:
            return raster[::2,::2]
        
        if zoom_level == 3:
            return raster[::4,::4]
        
        if zoom_level == 2:
            return raster[::10,::10]
        
        if zoom_level == 1:
            return raster[::20,::20]
