import rasterio
from matplotlib import pyplot
src = rasterio.open("maps/00_02.tif")

dataset = src.read()[0]

dataset[dataset <= 0] = 5000

pyplot.imshow(dataset, cmap='pink')
pyplot.show()