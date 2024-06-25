from world_map import WorldMap
import cProfile
import io
import pstats

if __name__ == "__main__":
    
    #profiler = cProfile.Profile()
    #profiler.enable()
    #map = WorldMap((1,1))
    #map = WorldMap((33,45))
    map = WorldMap((33+47,46))
    map.start()
    print("----------------------------")
    #map = WorldMap((47,1))
    #map.start()

    #s = io.StringIO()
    #profiler.disable()
    #stats = pstats.Stats(profiler, stream=s).sort_stats('percall')
    #stats.print_stats()
    #stats.strip_dirs()
    #with open("test.txt", "w+") as f:
    #    f.write(s.getvalue())
    
    