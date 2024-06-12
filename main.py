from world_map import WorldMap
import cProfile
import io
import pstats

if __name__ == "__main__":
    
    #profiler = cProfile.Profile()
    #profiler.enable()
    map = WorldMap(601)
    #map = WorldMap(2000)
    #print(len(map.color_set))
    #s = io.StringIO()
    #profiler.disable()
    #stats = pstats.Stats(profiler, stream=s).sort_stats('percall')
    #stats.print_stats()
    #stats.strip_dirs()
    #with open("test.txt", "w+") as f:
    #    f.write(s.getvalue())
    
    