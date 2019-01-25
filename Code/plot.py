import json
import numpy as np
import matplotlib.pyplot as plt
import plotly.plotly as py
import plotly.graph_objs as go
from scipy import interpolate
from mpl_toolkits.mplot3d import Axes3D

with open("./data/dataset.json", 'r') as f:
    DATASET = json.load(f)

longitudes = []
latitudes = []
heroins = []

north, south, west, east = [float('nan')]*4

for state in DATASET["2011"].values():
    for county in state["counties"].values():
        # new points
        [longitude, latitude] = county["location"]
        heroin_count = county["drugs"]["Morphine"] if "Morphine" in county["drugs"] else 0
        latitudes.append(latitude)
        longitudes.append(longitude)
        heroins.append(heroin_count)
        # max/min points
        east = max(longitude, east)
        west = min(longitude, west)
        north = max(latitude, north)
        south = min(latitude, south)

lngs = np.arange(west, east, (east - west) / 10)
lats = np.arange(south, north, (north - south) / 10)

x = np.linspace(west, east, 100)
y = np.linspace(south, north, 100)
meshgrid = np.meshgrid(x, y)
hs = interpolate.griddata(list(zip(longitudes, latitudes)), heroins, tuple(meshgrid), fill_value=0)

plt.contour(x, y, hs)

# hs = f(lngs, lats)

# #作图阶段
# fig = plt.figure()
# #定义画布为1*1个划分，并在第1个位置上进行作图
# ax = fig.add_subplot(111)
# #定义横纵坐标的刻度
# ax.set_yticks(range(len(x)))
# ax.set_yticklabels(x)
# ax.set_xticks(range(len(y)))
# ax.set_xticklabels(y)
# #作图并选择热图的颜色填充风格，这里选择hot
# im = ax.imshow(hs, cmap=plt.cm.hot)

# #增加右侧的颜色刻度条
# plt.colorbar(im)
# #增加标题
# plt.title("This is a title")


# fig = plt.figure()
# ax = Axes3D(fig)
# # ax.scatter(longitudes, latitudes, heroins)
# [xs, ys] = zip(*[(x_, y_) for x_ in x for y_ in y])
# ax.scatter(xs, ys, hs.flatten())

# plt.scatter(longitudes, latitudes)

#show
plt.show()
