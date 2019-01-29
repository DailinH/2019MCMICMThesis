import json
import numpy as np
import random
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.interpolate import griddata
from collections import deque
from utils import DATASET, LOCATIONS
from vc import get_adjacency, srcs_fips, county_by_fips, drugs_by_fips, calc_srcs_lambda

class AugmentList(list):
    def __init__(self, *args):
        super().__init__(args)

    def __getitem__(self, index):
        if self.__len__() <= index:
            self.extend([0] * (index - self.__len__() + 1))
        return super().__getitem__(index)

    def __setitem__(self, index, value):
        if self.__len__() <= index:
            self.extend([0] * (index - self.__len__() + 1))
        return super().__setitem__(index, value)

class Network:
    def __init__(self, phi=1.0):
        """Members"""
        self.srcs = set(srcs_fips(True))
        self.adjs = {}
        self.step = 0 # time step
        self.l = {} # lambda
        self.d = {} # delta
        self.S = {} # storages
        self.phi = phi

        """Initializing"""
        self.l = calc_srcs_lambda(self.srcs, range(2010, 2016 + 1))
        self.l = {src:np.mean(list(lambdas.values())) for src, lambdas in self.l.items()}
        # l = np.mean(list(self.l.values()))
        l = 0.6
        self.l = {src:l for src, lambdas in self.l.items()}
        cands = deque()
        cands.extend(self.srcs)
        while len(cands) != 0:
            fips = cands.popleft()
            if fips in self.S:
                continue
            drugs = drugs_by_fips(fips, 2017)
            if drugs == 0:
                continue
            if fips not in self.l:
                self.l[fips] = np.random.uniform(0.8, 0.9)
            self.d[fips] = min(np.random.uniform(0.0, 0.1), 1 - self.l[fips])
            self.S[fips] = AugmentList(drugs)
            self.adjs[fips] = [adj for adj in get_adjacency(fips) if drugs_by_fips(adj, 2017) > 0]
            cands.extend(self.adjs[fips])

        self.keep = {}
        for fips in self.srcs:
            self.keep[fips] = self.S[fips][self.step] + sum([self.S[adj][self.step] for adj in self.adjs[fips]])

        self.levels = { "A": [], "B": [] }

    def run_step(self):
        for fips in self.S:
            l, d, S = self.l[fips], self.d[fips], self.S[fips][-1]
            adjs = [adj for adj in self.adjs[fips] if adj not in self.srcs]
            if fips in self.srcs:
                self.S[fips].append(self.phi * self.keep[fips]) # stay the same
            else:
                self.S[fips][self.step + 1] += self.d[fips] * self.S[fips][self.step] # add surplus
            props = np.array([self.S[adj][-1] for adj in adjs])
            props = props / props.sum()
            Tout = (1 - l - d) * self.S[fips][self.step]
            Touts = Tout * props
            for i, adj in enumerate(adjs):
                self.S[adj][self.step + 1] += Touts[i]
        self.step += 1

    def calc_levels(self):
        self.levels = { "A": [], "B": [] }
        for fips, Ss in self.S.items():
            if Ss[self.step] > 2000:
                self.levels["A"].append(fips)
            elif Ss[self.step] > 600:
                self.levels["B"].append(fips)


network = Network()

def map_data():
    locations = []
    storages = []
    north, south, west, east = [float('nan')]*4
    for fips in network.S:
        loc = LOCATIONS[fips]
        lng = loc["lng"]
        lat = loc["lat"]
        locations.append([lng, lat])
        storages.append(network.S[fips][network.step])
        east = max(lng, east)
        west = min(lng, west)
        north = max(lat, north)
        south = min(lat, south)

    x = np.linspace(west, east, int((east - west)*100))
    y = np.linspace(south, north, int((north - south)*100))
    meshgrid = tuple(np.meshgrid(x, y))
    hs = griddata(locations, storages, meshgrid, fill_value=0)
    return hs, [west, east, south, north]

a_numbers = []
b_numbers = []


# for _ in range(150):
#     network.run_step()
#     network.calc_levels()
#     a_numbers.append(len(network.levels["A"]))
#     b_numbers.append(len(network.levels["B"]))

hs, extent = map_data()

# fig = plt.figure()
# im = plt.imshow(hs, interpolation='nearest', cmap="hot", extent=extent, animated=True)
# cbar = plt.colorbar()
# plt.clim(0, 22500)
# plt.show()



# def update(*args):
#     global network, cbar
#     network.run_step()
#     network.calc_levels()
#     a_numbers.append(len(network.levels["A"]))
#     b_numbers.append(len(network.levels["B"]))
#     # print(network.levels)
#     hs, _ = map_data()
#     cbar.remove()
#     im.set_array(hs)
#     cbar = plt.colorbar()
#     return im

# ani = FuncAnimation(fig, update, interval=10)

# plt.show()

skip = 5


# plt.plot(range(skip, len(a_numbers)), a_numbers[skip:], label="A")
# plt.plot(range(skip, len(b_numbers)), b_numbers[skip:], label="B")
# plt.plot(range(skip, len(a_numbers)), [a + b for a, b in zip(a_numbers, b_numbers)][skip:], label="Source Number")
# plt.legend(loc="upper left")
# plt.show()

phis = np.arange(0.5, 0.2, -0.1)
for phi in phis:
    network = Network(phi)
    a_numbers = []
    b_numbers = []

    print("current phi:", phi)
    for i in range(150):
        network.run_step()
        network.calc_levels()
        a_numbers.append(len(network.levels["A"]))
        b_numbers.append(len(network.levels["B"]))
    plt.plot(range(skip, len(a_numbers)), [a + b for a, b in zip(a_numbers, b_numbers)][skip:], label=f"φ={phi:.1f}")

plt.legend(loc="upper left")
plt.show()

# src_pts = []
# phis = np.arange(0.1, 1, 0.05)
# for phi in phis:
#     network = Network(phi)
#     a_numbers = []
#     b_numbers = []

#     print("current phi:", phi)
#     for i in range(150):
#         network.run_step()
#         network.calc_levels()

#     src_pts.append(len(network.levels["A"]) + len(network.levels["B"]))

# plt.scatter(phis, src_pts)
# plt.gca().invert_xaxis()
# plt.show()
