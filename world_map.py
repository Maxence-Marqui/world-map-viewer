from typing import Tuple, Dict, List

import pygame
from pygame.locals import *
from functools import lru_cache, wraps
from db_helpers import get_raster, get_multiple_rasters

from pygame_config import *
from area import Area
import numpy as np

from time import time
from math import floor

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


class WorldMap():
    def __init__(self, map_center: int) -> None:
        self.running: bool = True
        self.zoom_level: int = 4

        self.screen_size: Tuple[int, int] = SIZE
        self.areas: Dict[Tuple[int,int], Area] = {}
        self.displayed_map = np.ones(MAP_DIMENSIONS)

        self.map_center = self.get_raster_position(map_center)
        self.vertical_offset = 0
        self.horizontal_offset = 0
        self.color_set = set()
        self.displacement = 25 / self.zoom_level

        self.create_areas()
        self.start_pygame_loop()

        

    def start_pygame_loop(self):

        pygame.init()
        CLOCK = pygame.time.Clock()
        screen = pygame.display.set_mode(self.screen_size)
        keys_pressed = 0

        while self.running:

            screen.fill(LIGHT_GREY)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == KEYDOWN:
                    keys_pressed += 1
                if event.type == KEYUP:
                    keys_pressed -= 1

                
                if event.type == MOUSEBUTTONDOWN:
                    self.handle_click()
                
                if event.type == pygame.MOUSEWHEEL:
                    self.handle_mouse_wheel(event.y)

            if keys_pressed:
                    pressed = pygame.key.get_pressed()
                    self.handle_key_press(pressed)
    
            to_update = self.handle_screen_rendering(screen)
            CLOCK.tick(60)
            pygame.display.flip()
            #pygame.display.update(to_update) 

    def handle_click(self):
        pass

    def handle_mouse_wheel(self, direction):
        return
        if direction == 1:
            self.zoom_level += 1
        if direction == -1:
            self.zoom_level -= 1

    def handle_key_press(self, key):
        if key[K_ESCAPE]:
            self.running = False
        
        if key[K_PLUS] or key[K_KP_PLUS]:
            if self.zoom_level != 5:
                self.zoom_level += 1
                self.horizontal_offset = 0
                self.vertical_offset = 0
                self.displacement += 5
        
        if key[K_MINUS] or key[K_KP_MINUS]:
            if self.zoom_level != 1:
                self.zoom_level -= 1
                self.horizontal_offset = 0
                self.vertical_offset = 0
                self.displacement += 5
    
        if key[K_UP]:
            remaining = 100 - abs(self.vertical_offset) - self.displacement
            self.vertical_offset -= self.displacement
            if remaining < 0:
                self.vertical_offset = 100 + abs(remaining)
                self.map_center = (self.map_center[0] - 1, self.map_center[1])
            

        if key[K_DOWN]:
            remaining = 100 - abs(self.vertical_offset) - self.displacement
            self.vertical_offset += self.displacement
            if  remaining < 0:
                self.vertical_offset = -100 + abs(remaining)
                self.map_center = (self.map_center[0] + 1, self.map_center[1])
            
            
        if key[K_LEFT]:
            remaining = 150 - abs(self.vertical_offset) - self.displacement
            self.horizontal_offset -= self.displacement
            if  remaining < 0:
                self.horizontal_offset = 150 + remaining
                self.map_center = (self.map_center[0], self.map_center[1] - 1)
            
                
        if key[K_RIGHT]:
            remaining = 150 - abs(self.vertical_offset) - self.displacement
            self.horizontal_offset += self.displacement
            if self.horizontal_offset > 150:
                self.horizontal_offset = -150 + abs(remaining)
                self.map_center = (self.map_center[0], self.map_center[1] + 1)

        #print(self.zoom_level)
        
        self.create_areas()

    def create_areas(self):
        positions = self.get_new_area_near_center()
        rids_to_load = []
        for position in positions:
            if position in self.areas: continue
            rids_to_load.append(self.get_rid(position))
        
        if not len(rids_to_load): return
        print(f"Loading {len(rids_to_load)} areas...")
        areas = get_multiple_rasters(rids_to_load)
        print(f"Loading finished.")

        for area in areas:
            position = self.get_raster_position(area[0])
            self.areas[position] = Area(area[0], position, area[1])
    
    @lru_cache
    def get_raster_position(self, rid):
        rid -= 1
        horizontal_position = int(rid % 48)
        vertical_position = int(rid / 48)
        return (vertical_position, horizontal_position)

    @lru_cache
    def get_rid(self, position: Tuple[int,int]):
        return position[0] * 48 + position[1] + 1

    def handle_screen_rendering(self, screen):

        #area_to_check = self.get_areas_to_check()
        area_to_check = self.get_array_and_camera()
        #original_map = self.displayed_map.copy()
        #print("original map", original_map.shape)

        print("----")

        for area in area_to_check:
            indexes = area["indexes"]
            camera = area["camera"]
            sub_map = self.areas[area["position"]].get_displayed_nodes(self.zoom_level, indexes)

            print(area["position"], sub_map.shape)
            print("indexes", indexes)
            print("camera", camera)
            
            self.displayed_map[camera["starting_y"]:camera["ending_y"], camera["starting_x"]: camera["ending_x"]] = sub_map

        #map_differences = self.find_changed_indices(original_map, self.displayed_map)
        rectangles_to_update = []

        #for difference in map_differences:
        for y, row in enumerate(self.displayed_map):
            for x, column in enumerate(row):
                dimensions = (x * NODE_SIZE, y * NODE_SIZE, NODE_SIZE, NODE_SIZE)
                #dimensions = (difference[1] * NODE_SIZE, difference[0] * NODE_SIZE, NODE_SIZE, NODE_SIZE)
                #current_node = self.displayed_map[difference[0]][difference[1]]
                current_node = column
                if current_node == 0: color = BLUE
                else: color = interpolate(LIGHTEST_GREEN, DARKEST_GREEN, current_node / 2000)
                self.color_set.add(color)
                #color = WHITE
                pygame.draw.rect(screen, color, dimensions, 0)
                #rectangles_to_update.append()
        
        return #rectangles_to_update

    
    
    def find_changed_indices(self, original_array, modified_array):
    # Trouver les indices où les valeurs sont différentes
        changed_indices = np.argwhere(original_array != modified_array)
        return changed_indices

    def get_new_area_near_center(self):
        positions = []

        if self.zoom_level == 5: starting_point, ending_point =  -1, 2
        if self.zoom_level == 4: starting_point, ending_point =  -2, 2
        if self.zoom_level == 3: starting_point, ending_point =  -3, 3
        if self.zoom_level == 2: starting_point, ending_point =  -6, 6
        if self.zoom_level == 1: starting_point, ending_point =  -12, 12

        for i in range(starting_point,ending_point):
            for j in range(starting_point,ending_point):
                new_pos = (self.map_center[0] + i, self.map_center[1] + j)
                if not new_pos in self.areas: positions.append(new_pos)

        return positions
        
    def get_array_and_camera(self):

        vertical_offset = abs(self.vertical_offset)
        horizontal_offset = abs(self.horizontal_offset)

        areas = []
        
        print("----------------------------------")
        print((self.vertical_offset, self.horizontal_offset))

        chunks_infos = self.get_chunks_and_informations()

        #print(chunks_infos)
        
        chunks_count = chunks_infos["chunks_count"]
        height_range_start = chunks_infos["height_range_start"]
        width_range_start = chunks_infos["width_range_start"]
        base_camera_height = chunks_infos["base_camera_height"]
        base_camera_width = chunks_infos["base_camera_width"]
        y_index_to_display = chunks_infos["y_index_to_display"]
        x_index_to_display = chunks_infos["x_index_to_display"]

        remaining_height_camera = self.displayed_map.shape[0]
        remaining_height_map = y_index_to_display

        for vertical_modifier in range(height_range_start, height_range_start + chunks_count[0]):
            remaining_width_camera = self.displayed_map.shape[1]
            remaining_width_map = x_index_to_display

            for horizontal_modifier in range(width_range_start, width_range_start + chunks_count[1]):
                if vertical_modifier == height_range_start:
                    print("start_y")
                    camera_starting_height = 0
                    if self.vertical_offset < 0: camera_ending_height = vertical_offset
                    else: camera_ending_height = base_camera_height - vertical_offset

                    remaining_height_camera -= abs(camera_ending_height - camera_starting_height)

                    if self.vertical_offset < 0: starting_y = self.displayed_map.shape[0] - vertical_offset
                    else: starting_y = vertical_offset
                    ending_y = self.displayed_map.shape[0]
                
                elif vertical_modifier == (height_range_start + chunks_count[0] - 1):
                    print("end_y")
                    if self.vertical_offset < 0: camera_starting_height = vertical_offset
                    else: camera_starting_height = camera_starting_height #- vertical_offset
                    camera_ending_height = self.displayed_map.shape[0]

                    starting_y = 0
                    if self.vertical_offset == 0: ending_y = remaining_height_map
                    elif self.vertical_offset < 0 : ending_y = remaining_height_map - vertical_offset
                    else: ending_y = vertical_offset

                else:
                    print("middle_y")
                    starting_y = 0
                    ending_y = self.displayed_map.shape[0]

                if horizontal_modifier == width_range_start:
                    print("start_x")
                    camera_starting_width = 0
                    if self.horizontal_offset < 0: camera_ending_width = horizontal_offset
                    else: camera_ending_width = base_camera_width - horizontal_offset

                    remaining_width_camera -= abs(camera_ending_width - camera_starting_width)

                    if self.horizontal_offset < 0: starting_x = self.displayed_map.shape[1] - horizontal_offset
                    else: starting_x = horizontal_offset
                    ending_x = self.displayed_map.shape[1]

                    remaining_width_map -= abs(starting_x - ending_x)
                
                elif horizontal_modifier == (width_range_start + chunks_count[1] - 1):
                    print("end_x")
                    if self.horizontal_offset < 0: camera_starting_width = horizontal_offset 
                    else: camera_starting_width = self.displayed_map.shape[1] - remaining_width_camera

                    camera_ending_width = self.displayed_map.shape[1]

                    starting_x = 0
                    ending_x = remaining_width_map

                else:
                    print("middle_x")
                    camera_starting_width = camera_ending_width
                    camera_ending_width = camera_starting_width + base_camera_width
                    remaining_width_camera -= base_camera_width

                    starting_x = 0
                    ending_x = self.displayed_map.shape[1]
                    remaining_width_map -= self.displayed_map.shape[1]

                camera = {"starting_y":  int(camera_starting_height), 
                           "ending_y": int(camera_ending_height), 
                           "starting_x": int(camera_starting_width), 
                           "ending_x": int(camera_ending_width)}

                indexes = {"starting_y": int(starting_y) , 
                           "ending_y": int(ending_y) , 
                           "starting_x": int(starting_x), 
                           "ending_x": int(ending_x)}
                
                print((self.map_center[0] + vertical_modifier, self.map_center[1] + horizontal_modifier))
                print("camera: ",camera)
                print("indexes: ", indexes)
                
                area = {"position": (self.map_center[0] + vertical_modifier, self.map_center[1] + horizontal_modifier),
                        "indexes": indexes, 
                        "camera": camera}
                
                areas.append(area)
            
            remaining_height_camera = self.displayed_map.shape[0]
            remaining_height_map = y_index_to_display
            camera_starting_height = camera_ending_height
            camera_ending_height = camera_starting_height + base_camera_height
                
        
        return areas
    
    def get_chunks_and_informations(self):

        chunks_informations = {}

        if self.zoom_level == 5: zoom_modificator = 1
        if self.zoom_level == 4: zoom_modificator = 2
        if self.zoom_level == 3: zoom_modificator = 4
        if self.zoom_level == 2: zoom_modificator = 10
        if self.zoom_level == 1: zoom_modificator = 20

        chunks_informations["base_camera_height"] = self.displayed_map.shape[0] / zoom_modificator
        chunks_informations["base_camera_width"] = self.displayed_map.shape[1] / zoom_modificator

        chunks_informations["y_index_to_display"] = self.displayed_map.shape[0] * zoom_modificator
        chunks_informations["x_index_to_display"] = self.displayed_map.shape[1] * zoom_modificator

        chunks_y_count = zoom_modificator
        chunks_x_count = zoom_modificator

        if abs(self.vertical_offset): chunks_y_count += 1
        if abs(self.horizontal_offset): chunks_x_count += 1

        height_range_start = floor(chunks_y_count / 2) - chunks_y_count + 1
        width_range_start = floor(chunks_x_count / 2) - chunks_x_count + 1

        if self.vertical_offset < 0: height_range_start -= 1
        if self.horizontal_offset < 0: width_range_start -= 1

        chunks_informations["chunks_count"] = (chunks_y_count, chunks_x_count)

        chunks_informations["height_range_start"] = height_range_start
        chunks_informations["width_range_start"] = width_range_start

        return chunks_informations

@lru_cache
def interpolate(color_a, color_b, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(color_a, color_b))
