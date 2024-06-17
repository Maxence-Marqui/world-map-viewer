from typing import Tuple, Dict, List

import pygame
from pygame.locals import *
from functools import lru_cache, wraps

from db_helpers import get_multiple_rasters

from pygame_config import *
from area import Area
from chunk_dispacher import ChunkDispacher

import numpy as np
from time import time
from math import floor
import concurrent.futures


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
    def __init__(self, map_center: tuple[int, int]) -> None:
        self.running: bool = True
        self.zoom_level: int = 5

        self.screen_size: Tuple[int, int] = SIZE
        self.areas: Dict[Tuple[int,int], Area] = {}
        self.displayed_map = np.ones(MAP_DIMENSIONS)

        self.map_center = map_center
        self.vertical_offset = 0
        self.horizontal_offset = 0
        self.color_set = set()
        self.displacement = 5

        self.render_type = FULL_RERENDER
        self.draw_golden_center = False
        self.silent_mode = False

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

            if self.render_type == HYBRID_RERENDER: pygame.display.update()
            if self.render_type == FULL_RERENDER: pygame.display.flip()
            if self.render_type == PARTIAL_RERENDER: pygame.display.update(to_update) 
        
    def handle_click(self):
        pass

    def handle_mouse_wheel(self, direction):
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
        
        if key[K_MINUS] or key[K_KP_MINUS]:
            if self.zoom_level != 1:
                self.zoom_level -= 1
                self.horizontal_offset = 0
                self.vertical_offset = 0
    
        if key[K_UP]: self.handle_movements("up")
        if key[K_DOWN]: self.handle_movements("down")
        if key[K_LEFT]: self.handle_movements("left")
        if key[K_RIGHT]: self.handle_movements("right")

        if key[K_TAB]: self.switch_render_mode()
        if key[K_g]: self.draw_golden_center = not self.draw_golden_center
        if key[K_s]: self.silent_mode = not self.silent_mode

        self.create_areas()
    
    def switch_render_mode(self):
        if self.render_type == FULL_RERENDER: self.render_type = PARTIAL_RERENDER
        elif self.render_type == PARTIAL_RERENDER: self.render_type = HYBRID_RERENDER
        elif self.render_type == HYBRID_RERENDER: self.render_type = FULL_RERENDER

    def create_areas(self):
        positions = self.get_new_area_near_center()
        rids_to_load = {}

        for position in positions:
            if position in self.areas: continue
            table, rid = self.get_raster_locations(position)
            if rid > 0:
                if table in rids_to_load: rids_to_load[table].append(rid)
                else: rids_to_load[table] = [rid]
        
        if not len(rids_to_load): return
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for table in rids_to_load:
                executor.map(self.load_areas, [table], [rids_to_load[table]])

    def load_areas(self, table, rids):
        table_name = format_table_name(table[0], table[1])
        print(f"Loading {len(rids)} areas from table {table_name}...")
        areas = get_multiple_rasters(table_name, rids)
        for area in areas:
            position = self.get_raster_position(area[0], table)
            self.areas[position] = Area(area[0], position, area[1])
            
        print(f"Finished loading {len(rids)} areas...")
        return

    
    @lru_cache(maxsize=None)
    def get_raster_position(self, rid, table: Tuple[int, int]):
        rid -= 1
        horizontal_position = int(rid % 48) + table[1] * 48
        vertical_position = int(rid / 48) + table[0] * 48
        return (vertical_position, horizontal_position)

    @lru_cache(maxsize=None)
    def get_rid(self, position: Tuple[int,int]):
        return position[0] * 48 + position[1] + 1

    def handle_screen_rendering(self, screen):

        if self.draw_golden_center: 
            nodes_positions = None

        if self.render_type == FULL_RERENDER:
            area_to_check = self.get_array_and_camera()
            for area in area_to_check:
                indexes = area["indexes"]
                camera = area["camera"]

                if self.draw_golden_center:
                    if area["position"] == self.map_center: 
                        nodes_positions = camera

                if not area["position"] in self.areas: continue

                sub_map = self.areas[area["position"]].get_displayed_nodes(self.zoom_level, indexes)                
                self.displayed_map[camera["starting_y"]:camera["ending_y"], camera["starting_x"]: camera["ending_x"]] = sub_map

            
            for y, row in enumerate(self.displayed_map):
                for x, column in enumerate(row):
                    dimensions = (x * NODE_SIZE, y * NODE_SIZE, NODE_SIZE, NODE_SIZE)
                    current_node = column
                    if current_node == 0: color = BLUE
                    else: color = interpolate(LIGHTEST_GREEN, DARKEST_GREEN, current_node / 2000)

                    if self.draw_golden_center:
                        if (nodes_positions["starting_y"] <= y <= nodes_positions["ending_y"]) and (nodes_positions["starting_x"] <= x <= nodes_positions["ending_x"]): 
                            color = GOLD

                    self.color_set.add(color)
                    pygame.draw.rect(screen, color, dimensions, 0)
        
            return
        
        if self.render_type == PARTIAL_RERENDER:
            area_to_check = self.get_array_and_camera()
            original_map = self.displayed_map.copy()
            for area in area_to_check:
                indexes = area["indexes"]
                camera = area["camera"]
                sub_map = self.areas[area["position"]].get_displayed_nodes(self.zoom_level, indexes)
                self.displayed_map[camera["starting_y"]:camera["ending_y"], camera["starting_x"]: camera["ending_x"]] = sub_map

                if self.draw_golden_center:
                    if area["position"] == self.map_center: nodes_positions = camera

            map_differences = self.find_changed_indices(original_map, self.displayed_map)
            rectangles_to_update = []

            for difference in map_differences:
                dimensions = (difference[1] * NODE_SIZE, difference[0] * NODE_SIZE, NODE_SIZE, NODE_SIZE)
                current_node = self.displayed_map[difference[0]][difference[1]]

                if current_node == 0: color = BLUE
                else: color = interpolate(LIGHTEST_GREEN, DARKEST_GREEN, current_node / 2000)

                if self.draw_golden_center:
                    if (nodes_positions["starting_y"] <= y <= nodes_positions["ending_y"]) and (nodes_positions["starting_x"] <= x <= nodes_positions["ending_x"]): 
                        color = GOLD

                self.color_set.add(color)
                
                rectangles_to_update.append(pygame.draw.rect(screen, color, dimensions, 0))
        
            return rectangles_to_update

        if self.render_type == HYBRID_RERENDER:
            area_to_check = self.get_array_and_camera()
            original_map = self.displayed_map.copy()
            for area in area_to_check:
                indexes = area["indexes"]
                camera = area["camera"]
                sub_map = self.areas[area["position"]].get_displayed_nodes(self.zoom_level, indexes)
                self.displayed_map[camera["starting_y"]:camera["ending_y"], camera["starting_x"]: camera["ending_x"]] = sub_map

                if self.draw_golden_center:
                    if area["position"] == self.map_center: nodes_positions = camera

            map_differences = self.find_changed_indices(original_map, self.displayed_map)
            for difference in map_differences:
                dimensions = (difference[1] * NODE_SIZE, difference[0] * NODE_SIZE, NODE_SIZE, NODE_SIZE)
                current_node = self.displayed_map[difference[0]][difference[1]]

                if current_node == 0: color = BLUE
                else: color = interpolate(LIGHTEST_GREEN, DARKEST_GREEN, current_node / 2000)

                if self.draw_golden_center:
                    if (nodes_positions["starting_y"] <= y <= nodes_positions["ending_y"]) and (nodes_positions["starting_x"] <= x <= nodes_positions["ending_x"]): 
                        color = GOLD

                self.color_set.add(color)
                
                pygame.draw.rect(screen, color, dimensions, 0)

            return
            

    def find_changed_indices(self, original_array, modified_array):
    # Trouver les indices où les valeurs sont différentes
        changed_indices = np.argwhere(original_array != modified_array)
        return changed_indices

    def get_new_area_near_center(self):
        positions = []

        if self.zoom_level == 5: starting_point, ending_point =  -1, 2
        if self.zoom_level == 4: starting_point, ending_point =  -2, 3
        if self.zoom_level == 3: starting_point, ending_point =  -3, 4
        if self.zoom_level == 2: starting_point, ending_point =  -6, 7
        if self.zoom_level == 1: starting_point, ending_point =  -11, 12

        for i in range(starting_point,ending_point):
            for j in range(starting_point,ending_point):
                new_pos = (self.map_center[0] + i, self.map_center[1] + j)
                if not new_pos in self.areas: positions.append(new_pos)

        return positions
        
    def get_array_and_camera(self):

        areas = []
        chunks_infos = self.get_chunks_and_informations(self.zoom_level, self.vertical_offset, self.horizontal_offset)
        
        chunks_count = chunks_infos["chunks_count"]
        height_range_start = chunks_infos["height_range_start"]
        width_range_start = chunks_infos["width_range_start"]
        base_camera_height = chunks_infos["base_camera_height"]
        base_camera_width = chunks_infos["base_camera_width"]

        chunk_dispatcher = ChunkDispacher(base_camera_height, base_camera_width, self.horizontal_offset, self.vertical_offset)

        for vertical_modifier in range(height_range_start, height_range_start + chunks_count[0]):
            if vertical_modifier == height_range_start:
                camera_starting_height, camera_ending_height, starting_y, ending_y = chunk_dispatcher.get_start_y()
                
            elif vertical_modifier == (height_range_start + chunks_count[0] - 1):
                camera_starting_height, camera_ending_height, starting_y, ending_y = chunk_dispatcher.get_ending_y()

            else:
                camera_starting_height, camera_ending_height, starting_y, ending_y = chunk_dispatcher.get_middle_y()

            for horizontal_modifier in range(width_range_start, width_range_start + chunks_count[1]):
            
                if horizontal_modifier == width_range_start:
                    camera_starting_width, camera_ending_width, starting_x, ending_x = chunk_dispatcher.get_start_x()
                
                elif horizontal_modifier == (width_range_start + chunks_count[1] - 1):
                   camera_starting_width, camera_ending_width, starting_x, ending_x = chunk_dispatcher.get_ending_x()

                else:
                    camera_starting_width, camera_ending_width, starting_x, ending_x = chunk_dispatcher.get_middle_x()
                    

                camera = {"starting_y":  int(camera_starting_height), 
                           "ending_y": int(camera_ending_height), 
                           "starting_x": int(camera_starting_width), 
                           "ending_x": int(camera_ending_width)}

                indexes = {"starting_y": int(starting_y) , 
                           "ending_y": int(ending_y) , 
                           "starting_x": int(starting_x), 
                           "ending_x": int(ending_x)}
                
                area = {"position": (self.map_center[0] + vertical_modifier, self.map_center[1] + horizontal_modifier),
                        "indexes": indexes, 
                        "camera": camera}
                
                areas.append(area)    
        
        return areas
    
    @lru_cache(maxsize=None)
    def get_chunks_and_informations(self, zoom_level, vertical_offset, horizontal_offset):
        chunks_informations = {}

        chunks_informations["base_camera_height"] = MAP_DIMENSIONS[0] / ZOOM_LVL_MODIFICATOR[zoom_level]
        chunks_informations["base_camera_width"] =  MAP_DIMENSIONS[1] / ZOOM_LVL_MODIFICATOR[zoom_level]

        chunks_y_count = ZOOM_LVL_MODIFICATOR[zoom_level]
        chunks_x_count = ZOOM_LVL_MODIFICATOR[zoom_level]

        if abs(vertical_offset): chunks_y_count += 1
        if abs(horizontal_offset): chunks_x_count += 1

        height_range_start = STARTING_INDEXES[zoom_level][0]
        width_range_start = STARTING_INDEXES[zoom_level][1]

        if vertical_offset < 0: height_range_start -= 1
        if horizontal_offset < 0: width_range_start -= 1

        chunks_informations["chunks_count"] = (chunks_y_count, chunks_x_count)

        chunks_informations["height_range_start"] = height_range_start
        chunks_informations["width_range_start"] = width_range_start

        return chunks_informations

    def handle_movements(self, direction):
        
        vertical_threshold = MAP_DIMENSIONS[0] / 2 / ZOOM_LVL_MODIFICATOR[self.zoom_level]
        horizontal_threshold = MAP_DIMENSIONS[1] / 2 / ZOOM_LVL_MODIFICATOR[self.zoom_level]

        if direction == "up":
            diff_until_change = abs(vertical_threshold - abs(self.vertical_offset))
            above_threshold = self.displacement - diff_until_change
            if above_threshold >= 0 and self.vertical_offset < 0:
                self.vertical_offset = vertical_threshold + above_threshold
                self.map_center = (self.map_center[0] - 1, self.map_center[1])
            else:
                self.vertical_offset -= self.displacement

        if direction == "down":
            diff_until_change = abs(vertical_threshold - abs(self.vertical_offset))
            above_threshold = self.displacement - diff_until_change
            if above_threshold >= 0 and self.vertical_offset > 0:
                self.vertical_offset = -(vertical_threshold - above_threshold)
                self.map_center = (self.map_center[0] + 1, self.map_center[1])
            else:
                self.vertical_offset += self.displacement

        if direction == "left":
            diff_until_change = abs(horizontal_threshold - abs(self.horizontal_offset))
            above_threshold = self.displacement - diff_until_change
            if above_threshold >= 0 and self.horizontal_offset < 0:
                self.horizontal_offset = horizontal_threshold + above_threshold
                self.map_center = (self.map_center[0], self.map_center[1] - 1)
            else:
                self.horizontal_offset -= self.displacement

        if direction == "right":
            diff_until_change = abs(horizontal_threshold - abs(self.horizontal_offset))
            above_threshold = self.displacement - diff_until_change
            if above_threshold >= 0 and self.horizontal_offset > 0:
                self.horizontal_offset = -(horizontal_threshold - above_threshold)
                self.map_center = (self.map_center[0], self.map_center[1] + 1)
            else:
                self.horizontal_offset += self.displacement        


    def get_table_and_relative_position(self, position):
        table_y = floor(position[0] / 48)
        table_x = floor(position[1] / 48)
        
        relative_y = position[0] - (table_y * 48)
        relative_x = position[1] - (table_x * 48)
        return (table_y, table_x), (relative_y, relative_x)
    
    def get_raster_locations(self, position):
        table, relative_position = self.get_table_and_relative_position(position)
        rid = self.get_rid(relative_position)

        return (table, rid)



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
