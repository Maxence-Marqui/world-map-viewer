import tempfile
import rasterio
from db_helpers import get_raster
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
    def __init__(self, rid: int, raster_position: Tuple[int, int]) -> None:
        self.rid: int = rid
        self.position = raster_position
        self.raster: np.ndarray = []
        self.load_area()

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
    
    def get_displayed_nodes(self, zoom_level: int, indexes: dict):

        sub_raster = self.get_subset_of_nodes(indexes["starting_y"], indexes["ending_y"], indexes["starting_x"], indexes["ending_x"])
        sub_raster = self.get_zoomed_raster(sub_raster,zoom_level)
        
        return sub_raster
    
    def get_subset_of_nodes(self, starting_y, ending_y, starting_x, ending_x):
        subset = self.raster[starting_y:ending_y, starting_x:ending_x]
        return subset
    
    def get_zoomed_raster(self, raster, zoom_level):
        if zoom_level == 0:
            return raster
        
        if zoom_level == 1:
            return raster[::2]
        
        if zoom_level == 2:
            return raster[::4]
        
        if zoom_level == 3:
            return raster[::12]
        
        if zoom_level == 4:
            return raster[::60]


@lru_cache
def interpolate(color_a, color_b, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(color_a, color_b))