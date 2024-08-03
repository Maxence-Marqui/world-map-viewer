# world-map-viewer
This project's purpose is to display the earth topology using Pygame and the [USGS GMTED2010 dataset](https://topotools.cr.usgs.gov/gmted_viewer/viewer.htm).

The differents maps must be placed on a /maps folder in the project directory.  
These maps must be renamed with a pattern "y_x.tif", kind of like reading an 2D array.  
During development I focused on Europe, so the X is offset and Y_00.tif files represent the 6th map starting from the right.

The database used is PostgreSQL with the postgis extension to store topographical data using rasters.
To create that database, use this command:  
`docker compose up -d`

The next step is to save the maps in the database using the map_transfer.sh script.
That script takes all the files in the /maps folder, convert them to .sql file and save them in tables with the file name as table name (For example the 00_00.tif file with create the 00_00 table filled with rasters).

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

