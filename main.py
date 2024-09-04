from world_map import WorldMap
from dotenv import load_dotenv

import cProfile
import io
import pstats

if __name__ == "__main__":

    load_dotenv()
    
    #profiler = cProfile.Profile()
    #profiler.enable()

    map = WorldMap((40, 0))
    map.start()

    #s = io.StringIO()
    #profiler.disable()
    #stats = pstats.Stats(profiler, stream=s).sort_stats('percall')
    #stats.print_stats()
    #stats.strip_dirs()
    #with open("test.txt", "w+") as f:
    #    f.write(s.getvalue())
    
    