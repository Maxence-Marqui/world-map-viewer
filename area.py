import tempfile
import rasterio

from pygame_config import *
from typing import Tuple
import numpy as np


class Area:

    empty_raster = np.ndarray(shape=MAP_DIMENSIONS, dtype=None)
    empty_raster.fill(None)

    def __init__(self, rid: int, position: Tuple[int, int]) -> None:
        self.rid: int = rid
        self.position = position
        self.raster = self.empty_raster

    def convert_binary_to_np(self, raster_binary):

        with tempfile.NamedTemporaryFile() as tmpfile:
            tmpfile.write(raster_binary)
            with rasterio.open(tmpfile.name) as dataset:
                return dataset.read()[0]
    
    def add_real_raster(self, raster_binary):
        self.raster = self.convert_binary_to_np(raster_binary)

    
    def get_displayed_nodes(self, zoom_level: int, indexes: dict):

        starting_y = indexes["starting_y"] 
        ending_y = indexes["ending_y"]

        starting_x = indexes["starting_x"] 
        ending_x = indexes["ending_x"]

        sub_raster = self.get_zoomed_raster(self.raster, zoom_level)
        sub_raster = self.get_subset_of_nodes(sub_raster, starting_y, ending_y, starting_x, ending_x)
        return sub_raster
    
    def get_subset_of_nodes(self, raster, starting_y, ending_y, starting_x, ending_x):
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
