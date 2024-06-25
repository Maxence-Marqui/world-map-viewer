from typing import Tuple, Dict, List

import pygame
from pygame.locals import *
from functools import lru_cache

from helpers import *

from pygame_config import *
from area import Area
from chunk_dispacher import ChunkDispacher

import numpy as np
from skimage.measure import regionprops, label, find_contours
import threading



class WorldMap():
    def __init__(self, map_center: tuple[int, int]) -> None:
        self.running: bool = True
        self.zoom_level: int = 5

        self.screen_size: Tuple[int, int] = SIZE
        self.areas: Dict[Tuple[int,int], Area] = {}
        self.displayed_map = np.ones(MAP_DIMENSIONS)

        self.map_center = map_center
        self.vertical_offset = 100
        self.horizontal_offset = 0
        self.color_set = set()
        self.displacement = 5
        self.topographic_intervals = generate_intervals(1, 2000, TOPOGRAPHIC_THRESHOLDS[self.zoom_level])

        self.map_mode = REGULAR_MAP
        self.render_type = FULL_RERENDER
        self.draw_golden_center = False
        self.silent_mode = False
        
        self.create_areas()
        

    def start(self):

        pygame.init()
        CLOCK = pygame.time.Clock()
        screen = pygame.display.set_mode(self.screen_size)
        keys_pressed = 0

        while self.running:

            CLOCK.tick(60)
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

            if self.map_mode == REGULAR_MAP: to_update = self.render_regular_map(screen)
            if self.map_mode == TOPOGRAPHIC_MAP: to_update = self.render_topographical_map(screen)

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
                self.topographic_intervals = generate_intervals(1, 5000, TOPOGRAPHIC_THRESHOLDS[self.zoom_level])
        
        if key[K_MINUS] or key[K_KP_MINUS]:
            if self.zoom_level != 1:
                self.zoom_level -= 1
                self.horizontal_offset = 0
                self.vertical_offset = 0
                self.topographic_intervals = generate_intervals(1, 5000, TOPOGRAPHIC_THRESHOLDS[self.zoom_level])
    
        if key[K_UP]: self.handle_movements("up")
        if key[K_DOWN]: self.handle_movements("down")
        if key[K_LEFT]: self.handle_movements("left")
        if key[K_RIGHT]: self.handle_movements("right")

        if key[K_TAB]: self.switch_render_mode()
        if key[K_g]: self.draw_golden_center = not self.draw_golden_center
        if key[K_s]: self.silent_mode = not self.silent_mode
        if key[K_m]: self.switch_map_mode()

        
        self.create_areas()

    def switch_render_mode(self):
        if self.render_type == FULL_RERENDER: self.render_type = PARTIAL_RERENDER
        elif self.render_type == PARTIAL_RERENDER: self.render_type = HYBRID_RERENDER
        elif self.render_type == HYBRID_RERENDER: self.render_type = FULL_RERENDER
    
    def switch_map_mode(self):
        if self.map_mode == REGULAR_MAP: self.map_mode = TOPOGRAPHIC_MAP
        elif self.map_mode == TOPOGRAPHIC_MAP: self.map_mode = REGULAR_MAP

    def create_areas(self):
        positions = self.get_new_area_near_center()
        rids_to_load: Dict[Tuple[int, int], List[int]] = {}

        for position in positions:       
            if position in self.areas: continue

            table, rid = get_raster_db_locations(position)
            self.areas[position] = Area(rid, position)
            if rid > 0:
                if table in rids_to_load: rids_to_load[table].append(rid)
                else: rids_to_load[table] = [rid]
        
        if not len(rids_to_load): return
        
        for table in rids_to_load:
            for rids in chunk_array(rids_to_load[table], 10):
                thread = threading.Thread(target=get_multiple_rasters, args=[self.areas, table, rids])
                thread.start()

    def render_regular_map(self, screen):

        if self.draw_golden_center: nodes_positions = None
        if self.render_type != FULL_RERENDER: original_map = self.displayed_map.copy()

        area_to_check = self.get_array_and_camera()

        self.displayed_map.fill(None)

        for area in area_to_check:
            indexes = area["indexes"]
            camera = area["camera"]

            sub_map = self.areas[area["position"]].get_displayed_nodes(self.zoom_level, indexes)  
            if self.draw_golden_center and area["position"] == self.map_center: nodes_positions = camera

            sub_map = self.areas[area["position"]].get_displayed_nodes(self.zoom_level, indexes)                
            self.displayed_map[camera["starting_y"]:camera["ending_y"], camera["starting_x"]: camera["ending_x"]] = sub_map

        if self.render_type == FULL_RERENDER:

            for y, row in enumerate(self.displayed_map):
                for x, column in enumerate(row):
                    dimensions = (x * NODE_SIZE, y * NODE_SIZE, NODE_SIZE, NODE_SIZE)
                    current_node = column
                    color = get_node_color(current_node)

                    if self.draw_golden_center:
                        if (nodes_positions["starting_y"] <= y <= nodes_positions["ending_y"]) and (
                            nodes_positions["starting_x"] <= x <= nodes_positions["ending_x"]): 
                            color = GOLD
                    try:
                        pygame.draw.rect(screen, color, dimensions, 0)
                    except Exception as e:
                        pass
                        """print(e)
                        print(column, color)"""

        
        if self.render_type == PARTIAL_RERENDER:
            
            map_differences = find_changed_indices(original_map, self.displayed_map)
            rectangles_to_update = []

            for difference in map_differences:
                dimensions = (difference[1] * NODE_SIZE, difference[0] * NODE_SIZE, NODE_SIZE, NODE_SIZE)
                current_node = self.displayed_map[difference[0]][difference[1]]

                color = get_node_color(current_node)

                if self.draw_golden_center:
                    if (nodes_positions["starting_y"] <= y <= nodes_positions["ending_y"]) and (
                        nodes_positions["starting_x"] <= x <= nodes_positions["ending_x"]): 
                        color = GOLD

                self.color_set.add(color)
                
                rectangles_to_update.append(pygame.draw.rect(screen, color, dimensions, 0))
        
            return rectangles_to_update

        if self.render_type == HYBRID_RERENDER:

            map_differences = find_changed_indices(original_map, self.displayed_map)

            for difference in map_differences:
                dimensions = (difference[1] * NODE_SIZE, difference[0] * NODE_SIZE, NODE_SIZE, NODE_SIZE)
                current_node = self.displayed_map[difference[0]][difference[1]]
                color = get_node_color(current_node)

                if self.draw_golden_center:
                    if (nodes_positions["starting_y"] <= y <= nodes_positions["ending_y"]) and (
                        nodes_positions["starting_x"] <= x <= nodes_positions["ending_x"]): 
                        color = GOLD

                self.color_set.add(color)
                pygame.draw.rect(screen, color, dimensions, 0)
    
    def render_topographical_map(self, screen):

        if self.draw_golden_center: nodes_positions = None
        if self.render_type != FULL_RERENDER: original_map = self.displayed_map.copy()

        area_to_check = self.get_array_and_camera()

        for area in area_to_check:
            indexes = area["indexes"]
            camera = area["camera"]
            
            sub_map = self.areas[area["position"]].get_displayed_nodes(self.zoom_level, indexes)  
            self.displayed_map[camera["starting_y"]:camera["ending_y"], camera["starting_x"]: camera["ending_x"]] = sub_map

            if self.draw_golden_center and area["position"] == self.map_center: nodes_positions = camera


        if self.render_type == FULL_RERENDER:
            
            updated_map = (self.displayed_map == 0)

            for y, row in enumerate(updated_map):
                for x, column in enumerate(row):
                    if not column: continue

                    dimensions = (x * NODE_SIZE, y * NODE_SIZE, NODE_SIZE, NODE_SIZE)
                    pygame.draw.rect(screen, BLUE, dimensions, 0)

            for min, max ,color in self.topographic_intervals:
                updated_map = (min <= self.displayed_map) & (self.displayed_map <= max)
                labelled_map = label(updated_map, connectivity=2)

                regions = regionprops(labelled_map)

                for region in regions:
                    for node in region.coords:
                        #if node == None: color = LIGHT_GREY
                        dimensions = (node[1] * NODE_SIZE, node[0] * NODE_SIZE, NODE_SIZE, NODE_SIZE)
                        pygame.draw.rect(screen, color, dimensions, 0)
                    
                    #if abs(region.bbox[0] - region.bbox[2]) < 2 or abs(region.bbox[1] - region.bbox[3]) < 2: continue
                    #dimensions = (int(region.centroid[1]) * NODE_SIZE, int(region.centroid[0]) * NODE_SIZE, NODE_SIZE, NODE_SIZE)
                    #pygame.draw.rect(screen, RED, dimensions, 0)

                    if abs(region.bbox[0] - region.bbox[2]) < 8 or abs(region.bbox[1] - region.bbox[3]) < 8: continue
                    for contour in find_contours(region.image, fully_connected="low"):
                        contour[:, 0] += region.bbox[0]
                        contour[:, 1] += region.bbox[1]
                        perimeter = []
                        for node in contour:
                            perimeter.append((node[1] * NODE_SIZE, node[0] * NODE_SIZE))
                        pygame.draw.lines(screen, BLACK, False ,perimeter)

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

            map_differences = find_changed_indices(original_map, self.displayed_map)
            rectangles_to_update = []

            for difference in map_differences:
                dimensions = (difference[1] * NODE_SIZE, difference[0] * NODE_SIZE, NODE_SIZE, NODE_SIZE)
                current_node = self.displayed_map[difference[0]][difference[1]]

                if current_node == 0: color = BLUE
                elif current_node == None: color = LIGHT_GREY
                else: color = interpolate(LIGHTEST_GREEN, DARKEST_GREEN, current_node / 2000)

                if self.draw_golden_center:
                    if (nodes_positions["starting_y"] <= y <= nodes_positions["ending_y"]) and (nodes_positions["starting_x"] <= x <= nodes_positions["ending_x"]): 
                        color = GOLD

                self.color_set.add(color)
                
                rectangles_to_update.append(pygame.draw.rect(screen, color, dimensions, 0))
        
            return rectangles_to_update

        if self.render_type == HYBRID_RERENDER:

            original_map = self.displayed_map.copy()
            map_differences = find_changed_indices(original_map, self.displayed_map)

            for difference in map_differences:
                dimensions = (difference[1] * NODE_SIZE, difference[0] * NODE_SIZE, NODE_SIZE, NODE_SIZE)
                current_node = self.displayed_map[difference[0]][difference[1]]

                if current_node == 0: color = BLUE
                elif current_node == None: color = LIGHT_GREY
                else: color = interpolate(LIGHTEST_GREEN, DARKEST_GREEN, current_node / 2000)

                if self.draw_golden_center:
                    if (nodes_positions["starting_y"] <= y <= nodes_positions["ending_y"]) and (nodes_positions["starting_x"] <= x <= nodes_positions["ending_x"]): 
                        color = GOLD

                pygame.draw.rect(screen, color, dimensions, 0)


    def get_new_area_near_center(self):

        positions = []

        if self.zoom_level == 5: starting_point, ending_point =  -1, 2
        if self.zoom_level == 4: starting_point, ending_point =  -2, 3
        if self.zoom_level == 3: starting_point, ending_point =  -3, 4
        if self.zoom_level == 2: starting_point, ending_point =  -6, 7
        if self.zoom_level == 1: starting_point, ending_point =  -11, 12

        for vertical_modifier in range(starting_point,ending_point):
            for horizontal_modifier in range(starting_point,ending_point):

                y_position = self.map_center[0] + vertical_modifier
                x_position = self.map_center[1] + horizontal_modifier

                if y_position < 0 or y_position > MAX_VERTICAL_CHUNK:  continue

                if x_position < 0: x_position = MAX_HORIZONTAL_CHUNK - abs(horizontal_modifier)
                elif x_position > MAX_HORIZONTAL_CHUNK: x_position = 0 + abs(horizontal_modifier)
                
                new_pos = (y_position, x_position)
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

                y_position = self.map_center[0] + vertical_modifier
                x_position = self.map_center[1] + horizontal_modifier

                if y_position < 0 or y_position > MAX_VERTICAL_CHUNK: continue

                if x_position < 0: x_position = MAX_HORIZONTAL_CHUNK - abs(horizontal_modifier)
                if x_position > MAX_HORIZONTAL_CHUNK: x_position = 0 + abs(horizontal_modifier)
            
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
                
                area = {"position": (y_position, x_position),
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
            if self.map_center[0] == 0: return

            diff_until_change = abs(vertical_threshold - abs(self.vertical_offset))
            above_threshold = self.displacement - diff_until_change
            if above_threshold >= 0 and self.vertical_offset < 0:
                self.vertical_offset = vertical_threshold + above_threshold
                self.map_center = (self.map_center[0] - 1, self.map_center[1])
            else:
                self.vertical_offset -= self.displacement

        if direction == "down":
            if self.map_center[0] == 350: return

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
                if self.map_center[1] == 0: self.map_center = (self.map_center[0], MAX_HORIZONTAL_CHUNK)
                else:self.map_center = (self.map_center[0], self.map_center[1] - 1)
            else:
                self.horizontal_offset -= self.displacement

        if direction == "right":
            diff_until_change = abs(horizontal_threshold - abs(self.horizontal_offset))
            above_threshold = self.displacement - diff_until_change
            if above_threshold >= 0 and self.horizontal_offset > 0:
                self.horizontal_offset = -(horizontal_threshold - above_threshold)
                if self.map_center[1] == 580: self.map_center = (self.map_center[0], 0)
                else: self.map_center = (self.map_center[0], self.map_center[1] + 1)
            else:
                self.horizontal_offset += self.displacement        



