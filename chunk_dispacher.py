from pygame_config import *


class ChunkDispacher:
    def __init__(self, chunk_height, chunk_width, horizontal_offset, vertical_offset) -> None:

        self.remaining_height = MAP_DIMENSIONS[0]
        self.remaining_width = MAP_DIMENSIONS[1]

        self.chunk_height = chunk_height
        self.chunk_width = chunk_width

        self.real_vertical_offset = vertical_offset
        self.real_horizontal_offset = horizontal_offset

        self.vertical_offset = abs(vertical_offset)
        self.horizontal_offset = abs(horizontal_offset)

        self.y_start = 0
        self.x_start = 0

    def get_start_y(self):

        camera_start = 0

        if self.real_vertical_offset == 0: 
            starting_index = 0
            camera_end = self.chunk_height
        elif self.real_vertical_offset > 0: 
            starting_index = self.vertical_offset
            camera_end = self.chunk_height - self.vertical_offset
        else:
            starting_index = self.chunk_height - self.vertical_offset
            camera_end = self.vertical_offset

        ending_index = self.chunk_height
        self.remaining_height -= abs(camera_end - camera_end)
        self.y_start = camera_end
        
        #if not camera_start < 0:
        #    raise OutOfBoundError(self.chunk_height, "start_y", ) 

        return camera_start, camera_end, starting_index, ending_index


    def get_middle_y(self):
        camera_start = self.y_start
        camera_end = camera_start + self.chunk_height

        self.remaining_height -= self.chunk_height
        self.y_start += self.chunk_height
        
        return camera_start, camera_end, 0, self.chunk_height

    def get_ending_y(self):
        #print("end_y")
        starting_index = 0
        camera_start = self.y_start
        camera_end = self.y_start + self.chunk_height

        if self.real_vertical_offset == 0:
            ending_index = self.chunk_height
        elif self.real_vertical_offset > 0:
            ending_index = self.vertical_offset
        else:
            ending_index = self.chunk_height - self.vertical_offset
        
        return camera_start, camera_end, starting_index, ending_index

    def get_start_x(self):
        #print("start_x")
        camera_start = 0

        if self.real_horizontal_offset == 0:
            camera_end = self.chunk_width
            starting_index = 0
        elif self.real_horizontal_offset > 0:
            camera_end = self.chunk_width - self.horizontal_offset
            starting_index = self.horizontal_offset
        else:
            camera_end = self.horizontal_offset
            starting_index = self.chunk_width - self.horizontal_offset

        ending_index = self.chunk_width
        self.remaining_width -= abs(camera_end - camera_end)
        self.x_start = camera_end

        return camera_start, camera_end, starting_index, ending_index

    def get_middle_x(self):
        #print("middle_x")
        
        camera_start = self.x_start
        camera_end = camera_start + self.chunk_width

        self.remaining_width -= self.chunk_width
        self.x_start += self.chunk_width
        
        return camera_start, camera_end, 0, self.chunk_width
    
    def get_ending_x(self):
        #print("ending_x")
        
        camera_start = self.x_start
        camera_end = self.x_start + self.chunk_width

        if self.real_horizontal_offset == 0:
            starting_index = 0
            ending_index = self.chunk_width
        elif self.real_horizontal_offset > 0:
            starting_index = 0
            ending_index = self.horizontal_offset
        else:
            starting_index = 0
            ending_index = self.chunk_width - self.horizontal_offset
        
        return camera_start, camera_end, starting_index, ending_index

class OutOfBoundError(Exception):
    def __init__(self, max_dimension, type, position, value_type, actual_value) -> None:

        self.message = f"{type} error at chunk position {position}:"
        self.message += f"\n expected {value_type} between 0 and {max_dimension}, recieved {actual_value}"
        
        super().__init__(self.message)
