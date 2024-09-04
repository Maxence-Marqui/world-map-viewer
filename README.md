# world-map-viewer
This project's purpose is to display the earth topology using Pygame and the [USGS GMTED2010 dataset](https://topotools.cr.usgs.gov/gmted_viewer/viewer.htm).

The differents maps must be placed on a /maps folder in the project directory.  
These maps must be renamed with a pattern "y_x.tif", kind of like reading an 2D array.  

You will also need to create a .env file containing the following variables:
- POSTGRES_DB_NAME
- POSTGRES_DB_PASSWORD
- POSTGRES_USER
- IMAGE_PORT

To setup the project database, use the command:
`sh setup_project`
Doing so will create a postgres database with the extensions needed to run the project, and then convert each file in the /maps folder into an sql dump which will be created in the /sql_archives folder, which will finally be saved in the database.
The process can be quite long, as there is an huge amount of data being processed (each data point represent 250m²). Once it is done, you can start the map viewer. 

To start the map viewer, use the command:  
`python3 main.py`

### Controls

This project has 2 differents map styles and 3 render modes.
To switch map mode, press the "m" key:
Normal mode: all pixels have a color ranging from bright green to dark green depending of the elevation of the area, with elevation 0 being considered water level and thus blue.

Topology mode: group all nodes in sub ranges defined in the config file. An area will have an uniform color and drawn with a black line.

To switch render mode, press the "Tab" key:
Full rerender: It updates all pixels on the screen every tick. It is the smoothest mode.  
Partial rerender: It checks the difference between the previous and current state of the map and updates only the pixels that needs changing. It is pretty slow and looks like an old gameboy screen update.  
Hybrid rerender: Checks the difference between the states use the pygame partial render function.  

In order to move the camera around, use the 4 arrows keys.  
To zoom in, use the + key on the keypad.  
To zoom out, use the - key on the keypad.  

The differents zoom levels are:
- Maximum zoom: 1x1 raster map.
- The 4th zoom: 2x2 raster map.
- The 3rd zoom: 4x4 raster map.
- The 2d zoom: 10x10 raster map.
- the minimum zoom: 20x20 raster map.

In order to display the logs in the terminal, use the "s" key.  
In order to replace the central raster by a golden rectangle, use the "g" key.
