from typing import Tuple, Dict, List

import pygame
from pygame.locals import *
from functools import lru_cache, wraps

from pygame_config import *
from area import Area
import numpy as np

from time import time

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
        self.zoom_level: int = 0

        self.screen_size: Tuple[int, int] = SIZE
        self.areas: Dict[Tuple[int,int], Area] = {}
        self.displayed_map = np.random.rand(200, 300)

        self.map_center = self.get_raster_position(map_center)
        self.vertical_offset = 0
        self.horizontal_offset = 0
        self.color_set = set()

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
        if direction == 1:
            self.zoom_level += 1
        if direction == -1:
            self.zoom_level -= 1

    def handle_key_press(self, key):
        if key[K_ESCAPE]:
            self.running = False
        
        if key[K_PLUS] or key[K_KP_PLUS]:
            if self.zoom_level == 0:
                self.zoom_level = 1
        
        if key[K_MINUS] or key[K_KP_MINUS]:
            if self.zoom_level == 1:
                self.zoom_level = 0
    
        if key[K_UP]:
            self.vertical_offset -= 5
            if self.vertical_offset < -100:
                self.vertical_offset = 95
                self.map_center = (self.map_center[0] - 1, self.map_center[1])
            

        if key[K_DOWN]:
            self.vertical_offset += 5
            if self.vertical_offset > 100:
                self.vertical_offset = -95
                self.map_center = (self.map_center[0] + 1, self.map_center[1])
            
            
        if key[K_LEFT]:
            self.horizontal_offset -= 5
            if self.horizontal_offset < -150:
                self.horizontal_offset = 145
                self.map_center = (self.map_center[0], self.map_center[1] - 1)
            
                
        if key[K_RIGHT]:
            self.horizontal_offset += 5
            if self.horizontal_offset > 150:
                self.horizontal_offset = -145
                self.map_center = (self.map_center[0], self.map_center[1] + 1)

        print(self.zoom_level)
        
        self.create_areas()

    def create_areas(self):
        positions = self.get_area_near_center()
        for position in positions:
            if position in self.areas: continue
            self.areas[position] = Area(self.get_rid(position), position)
    
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

        for area in area_to_check:
            indexes = area["indexes"]
            camera = area["camera"]
            sub_map = self.areas[area["position"]].get_displayed_nodes(self.zoom_level, indexes)
            #print(area["position"], "[{}:{} , {}:{}]".format(camera["starting_y"], camera["ending_y"], camera["starting_x"], camera["ending_x"]))
            #print(sub_map.shape)
            #print(area["position"])
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

    def get_areas_to_check(self):
        # Calculer les positions de départ dans la grille de chunks

        area_near_center = self.get_area_near_center()

        if self.zoom_level == 0:
            max_width = 300
            max_height = 200

        if self.zoom_level == 1:
            max_width = 150
            max_height = 100
        
        if self.zoom_level == 2:
            max_width = 75
            max_height = 50
        
        if self.zoom_level == 3:
            max_width = 60
            max_height = 40
        
        if self.zoom_level == 4:
            max_width = 30
            max_height = 20

        if self.horizontal_offset == 0 and self.vertical_offset == 0:
            if self.zoom_level == 0: return [{"position": self.map_center, 
                                              "indexes": {"starting_y": 0, "ending_y": 200, "starting_x": 0, "ending_x": 300},
                                              "camera": {"starting_y": 0, "ending_y": 200, "starting_x": 0, "ending_x": 300}}]

            #if self.zoom_level == 1: return [{"position": self.map_center, 
            #                                  "indexes":{"starting_y": 0, "ending_y": 100, "starting_x": 0, "ending_x": 150},
            #                                  "indexes":{"starting_y": 0, "ending_y": 100, "starting_x": 0, "ending_x": 150}}, 
            #                               {"position": (self.map_center[0], self.map_center[1] + 1), "starting_y": 0, "ending_y": 100, "starting_x": 150, "ending_x": 300},
            #                               {"position": (self.map_center[0] + 1, self.map_center[1]), "starting_y": 100, "ending_y": 200, "starting_x": 0, "ending_x": 150},
            #                               {"position": (self.map_center[0] + 1, self.map_center[1] + 1), "starting_y": 100, "ending_y": 200, "starting_x": 150, "ending_x": 300}]
            
        if self.horizontal_offset < 0 and self.vertical_offset < 0:
            if self.zoom_level == 0:
                vertical_offset = abs(self.vertical_offset)
                horizontal_offset = abs(self.horizontal_offset)
                return [{"position": ((self.map_center[0] - 1, self.map_center[1] - 1)),
                         "indexes":{"starting_y": 200 - vertical_offset, "ending_y": 200, "starting_x": 300 - horizontal_offset, "ending_x": 300},
                         "camera":{"starting_y": 0, "ending_y": vertical_offset, "starting_x": 0, "ending_x": horizontal_offset}},

                        {"position": ((self.map_center[0] - 1, self.map_center[1])),
                         "indexes":{"starting_y": 200 - vertical_offset, "ending_y": 200 , "starting_x": 0, "ending_x": horizontal_offset},
                         "camera":{"starting_y": 0, "ending_y": vertical_offset, "starting_x": 300 - horizontal_offset, "ending_x": 300}},

                        {"position": ((self.map_center[0], self.map_center[1] - 1)),
                         "indexes":{"starting_y": 0, "ending_y": 200 - vertical_offset, "starting_x": 300 - horizontal_offset, "ending_x": 300},
                         "camera":{"starting_y": vertical_offset, "ending_y": 200, "starting_x": 0, "ending_x": horizontal_offset}}, 

                        {"position": (self.map_center),
                         "indexes":{"starting_y": 0, "ending_y": 200 - vertical_offset, "starting_x": 0, "ending_x": 300 - horizontal_offset},
                         "camera":{"starting_y": vertical_offset, "ending_y": 200, "starting_x": horizontal_offset, "ending_x": 300}}]
        
        if self.horizontal_offset > 0 and self.vertical_offset < 0:
            if self.zoom_level == 0:
                pass
        
        if self.horizontal_offset < 0 and self.vertical_offset > 0:
            if self.zoom_level == 0:
                pass
        
        if self.horizontal_offset < 0 and self.vertical_offset < 0:
            if self.zoom_level == 0:
                pass
            

        if self.horizontal_offset > 0:
            if self.zoom_level == 0:
                return [{"position": self.map_center,
                         "indexes":{"starting_y": 0, "ending_y": 200, "starting_x": self.horizontal_offset, "ending_x": 300},
                          "camera":{"starting_y": 0, "ending_y": 200, "starting_x": 0, "ending_x": 300 - self.horizontal_offset} }, 
                        {"position": (self.map_center[0], self.map_center[1] + 1),
                         "indexes":{"starting_y": 0, "ending_y": 200, "starting_x": 0, "ending_x": self.horizontal_offset},
                         "camera": {"starting_y": 0, "ending_y": 200, "starting_x": 300 - self.horizontal_offset, "ending_x": 300}}]

        if self.horizontal_offset < 0:
            horizontal_offset = abs(self.horizontal_offset)
            if self.zoom_level == 0:
                return [{"position": (self.map_center),
                         "indexes":{"starting_y": 0, "ending_y": 200, "starting_x": 0, "ending_x": 300 - horizontal_offset},
                          "camera":{"starting_y": 0, "ending_y": 200, "starting_x": horizontal_offset, "ending_x": 300} }, 
                        {"position": (self.map_center[0], self.map_center[1] - 1),
                         "indexes":{"starting_y": 0, "ending_y": 200, "starting_x": 300 - horizontal_offset, "ending_x": 300},
                         "camera": {"starting_y": 0, "ending_y": 200, "starting_x": 0, "ending_x": horizontal_offset}}]

        if self.vertical_offset > 0:
            if self.zoom_level == 0:
                return [{"position": self.map_center,
                         "indexes":{"starting_y": self.vertical_offset, "ending_y": 200, "starting_x": 0, "ending_x": 300},
                          "camera":{"starting_y": 0, "ending_y": 200 - self.vertical_offset, "starting_x": 0, "ending_x": 300} }, 
                        {"position": (self.map_center[0] + 1, self.map_center[1]),
                         "indexes":{"starting_y": 0, "ending_y": self.vertical_offset, "starting_x": 0, "ending_x": 300},
                         "camera": {"starting_y": 200 - self.vertical_offset, "ending_y": 200, "starting_x": 0, "ending_x": 300}}]

        if self.vertical_offset < 0:
            vertical_offset = abs(self.vertical_offset)
            if self.zoom_level == 0:
                return [{"position": (self.map_center),
                         "indexes":{"starting_y": 0, "ending_y": 200 - vertical_offset, "starting_x": 0, "ending_x": 300},
                          "camera":{"starting_y": vertical_offset, "ending_y": 200, "starting_x": 0, "ending_x": 300} }, 
                        {"position": (self.map_center[0] - 1, self.map_center[1]),
                         "indexes":{"starting_y": 200 - vertical_offset, "ending_y": 200, "starting_x": 0, "ending_x": 300},
                         "camera": {"starting_y": 0, "ending_y": vertical_offset, "starting_x": 0, "ending_x": 300}}]
    
    def find_changed_indices(self, original_array, modified_array):
    # Trouver les indices où les valeurs sont différentes
        changed_indices = np.argwhere(original_array != modified_array)
        return changed_indices

    def get_area_near_center(self):
        positions = []

        if self.zoom_level == 0: starting_point, ending_point =  -1, 2
        if self.zoom_level == 1: starting_point, ending_point =  -2, 3
        #if self.zoom_level == 2: starting_point, ending_point =  -1, 2
        #if self.zoom_level == 3: starting_point, ending_point =  -2, 3

        for i in range(-1,2):
            for j in range(-1,2):
                positions.append((self.map_center[0] + i, self.map_center[1] + j))

        return positions
        
    def get_array_and_camera(self):

        vertical_offset = abs(self.vertical_offset)
        horizontal_offset = abs(self.horizontal_offset)

        areas = []

        chunks_count, height_range_start, width_range_start = self.get_chunks_and_informations()

        print("----------------------------------")


        for y in range(height_range_start, height_range_start + chunks_count[0]):
            remaining_height_camera, remaining_width_camera = self.displayed_map.shape
            remaining_height_map, remaining_width_map = self.displayed_map.shape

            for x in range(width_range_start, width_range_start + chunks_count[1]):
                if y == height_range_start:
                    print("start_y")
                    camera_starting_height = 0
                    camera_ending_height = vertical_offset if self.vertical_offset < 0 else self.displayed_map.shape[0] - vertical_offset
                    remaining_height_camera -= vertical_offset

                    starting_y = self.displayed_map.shape[0] - vertical_offset if self.vertical_offset < 0 else vertical_offset
                    ending_y = self.displayed_map.shape[0]
                    remaining_height_map -= vertical_offset
                
                elif y == (height_range_start + chunks_count[0] - 1):
                    print("end_y")
                    camera_starting_height = vertical_offset if self.vertical_offset < 0 else self.displayed_map.shape[0] - vertical_offset
                    camera_ending_height = self.displayed_map.shape[0]

                    starting_y = 0
                    ending_y = self.displayed_map.shape[0] - vertical_offset if self.vertical_offset < 0 else vertical_offset

                else:
                    print("middle_y")
                    camera_starting_height = remaining_height_camera
                    camera_ending_height = remaining_height_camera - int(self.displayed_map.shape[0] / chunks_count[0])
                    remaining_height_camera -= int(self.displayed_map.shape[0] / chunks_count[0])

                    starting_y = remaining_height_map
                    ending_y = remaining_height_map - int(self.displayed_map.shape[0] / chunks_count[0])
                    remaining_height_map -= int(self.displayed_map.shape[0] / chunks_count[0])

                if x == width_range_start:
                    print("start_x")
                    camera_starting_width = 0
                    camera_ending_width = horizontal_offset if self.horizontal_offset < 0  else self.displayed_map.shape[1] - horizontal_offset
                    remaining_width_camera -= horizontal_offset

                    starting_x = self.displayed_map.shape[1] - horizontal_offset if self.horizontal_offset < 0 else horizontal_offset
                    ending_x = self.displayed_map.shape[1]
                    remaining_width_map -= horizontal_offset
                
                elif x == (width_range_start + chunks_count[1] - 1):
                    print("end_x")
                    camera_starting_width = horizontal_offset if self.horizontal_offset < 0 else remaining_width_map
                    camera_ending_width = self.displayed_map.shape[1]

                    starting_x = 0
                    ending_x = self.displayed_map.shape[1] - horizontal_offset if self.horizontal_offset < 0 else self.displayed_map.shape[1] - remaining_width_map

                else:
                    print("middle_x")
                    camera_starting_width = remaining_width_camera
                    camera_ending_width = remaining_width_camera - int(self.displayed_map.shape[1] / chunks_count[1])
                    remaining_width_camera -= int(self.displayed_map.shape[1] / chunks_count[1])

                    starting_x = remaining_width_camera
                    ending_x = remaining_width_camera - int(self.displayed_map.shape[1] / chunks_count[1])
                    remaining_width_camera -= int(self.displayed_map.shape[1] / chunks_count[1])

                camera = {"starting_y":  camera_starting_height, 
                           "ending_y": camera_ending_height, 
                           "starting_x": camera_starting_width, 
                           "ending_x": camera_ending_width}

                indexes = {"starting_y": starting_y , 
                           "ending_y": ending_y , 
                           "starting_x": starting_x, 
                           "ending_x": ending_x}
                
                print((self.map_center[0] + y, self.map_center[1] + x))
                print(camera)
                print(indexes)
                
                area = {"position": (self.map_center[0] + y, self.map_center[1] + x),
                        "indexes": indexes, 
                        "camera": camera}
                
                areas.append(area)
                
        
        return areas
    
    def get_chunks_and_informations(self):
        if self.zoom_level == 0:
            if self.horizontal_offset == 0 and self.vertical_offset == 0:
                chunks_count = (1,1)
                height_range_start = 0
                width_range_start = 0
                return chunks_count, height_range_start, width_range_start

            if self.horizontal_offset > 0 and self.vertical_offset > 0:
                chunks_count = (2,2)
                height_range_start = 0
                width_range_start = 0
                return chunks_count, height_range_start, width_range_start
            
            if self.horizontal_offset < 0 and self.vertical_offset < 0:
                chunks_count = (2,2)
                height_range_start = -1
                width_range_start = -1
                return chunks_count, height_range_start, width_range_start
            
            if self.horizontal_offset < 0 and self.vertical_offset > 0:
                chunks_count = (2,2)
                height_range_start = 0
                width_range_start = -1
                return chunks_count, height_range_start, width_range_start
            
            if self.horizontal_offset > 0 and self.vertical_offset < 0:
                chunks_count = (2,2)
                height_range_start = -1
                width_range_start = 0
                return chunks_count, height_range_start, width_range_start

            
            if self.horizontal_offset > 0:
                chunks_count = (1,2)
                height_range_start = 0
                width_range_start = 0
                return chunks_count, height_range_start, width_range_start
            
            if self.horizontal_offset < 0:
                chunks_count = (1,2)
                height_range_start = 0
                width_range_start = -1
                return chunks_count, height_range_start, width_range_start

            if self.vertical_offset > 0:
                chunks_count = (2,1)
                height_range_start = 0
                width_range_start = 0
                return chunks_count, height_range_start, width_range_start
            
            if self.vertical_offset < 0:
                chunks_count = (2,1)
                height_range_start = -1
                width_range_start = 0
                return chunks_count, height_range_start, width_range_start
        
        if self.zoom_level == 1:
            if self.horizontal_offset == 0 and self.vertical_offset == 0:
                height_range_start = 0
                width_range_start = 0
                chunks_count = (2,2)
                return chunks_count, height_range_start, width_range_start
        
        if self.zoom_level == 2:
            if self.horizontal_offset == 0 and self.vertical_offset == 0:
                chunks_count = (4,4)
                return chunks_count, height_range_start, width_range_start
        
        if self.zoom_level == 3:
            if self.horizontal_offset == 0 and self.vertical_offset == 0:
                chunks_count = (10,10)
                return chunks_count, height_range_start, width_range_start
        
        if self.zoom_level == 4:
            if self.horizontal_offset == 0 and self.vertical_offset == 0:
                chunks_count = (20,20)
                return chunks_count, height_range_start, width_range_start



        
        
        
    






@lru_cache
def interpolate(color_a, color_b, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(color_a, color_b))
