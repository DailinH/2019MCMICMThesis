import re
import os
import csv
import json
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.plotly as py
import plotly.graph_objs as go
from scipy import interpolate, sparse
from scipy.ndimage import maximum_filter
from mpl_toolkits.mplot3d import Axes3D
from utils import DATASET

def exec_drugs(drug_type, b_thershold, a_threshold=None):
    drug_name = drug_type if drug_type is not None else "Total"
    drugs_by_year = []
    layering_by_year = {}
    if not os.path.exists(f"./part1/{drug_name}"):
        os.mkdir(f"./part1/{drug_name}")
    try:
        with open(f"./part1/{drug_name}/blocks.json", 'r') as f:
            blocks = json.load(f)
    except:
        blocks = {}
    for i, year in enumerate([f"20{yy}" for yy in range(10, 16 + 1)]):
        longitudes = {}
        latitudes = {}
        drugs = {}

        north, south, west, east = [float('nan')]*4

        for state in DATASET[year]["states"].values():
            for c_name, county in state["counties"].items():
                # new points
                [longitude, latitude] = county["location"]
                if drug_type is None:
                    drug_count = county["drugsTotal"]
                else:
                    drug_count = county["drugs"].get(drug_type, 0)
                latitudes[c_name] = latitude
                longitudes[c_name] = longitude
                drugs[c_name] = (drug_count)
                # max/min points
                east = max(longitude, east)
                west = min(longitude, west)
                north = max(latitude, north)
                south = min(latitude, south)

        drugs_by_year.append(drugs)

        # each step represents 0.1 degree
        x = np.linspace(west, east, int((east - west)*20))
        y = np.linspace(south, north, int((north - south)*20))
        meshgrid = tuple(np.meshgrid(x, y))
        hs = interpolate.griddata(list(zip(longitudes.values(), latitudes.values())), list(drugs.values()), meshgrid, fill_value=0)

        # fig = plt.figure()
        # ax = Axes3D(fig)
        # ax.scatter(list(longitudes.values()), list(latitudes.values()), list(drugs.values()))
        # [xs, ys] = zip(*[(x_, y_) for x_ in x for y_ in y])
        # ax.scatter(xs, ys, hs.flatten())
        # plt.contour(x, y, hs)
        # plt.colorbar()

        """Local Maximum"""
        filt = maximum_filter(hs, size=3)
        mhs = np.where(filt == hs, hs, 0)

        if i > 0:
            plt.subplot(2, 3, i)

        """Layering"""
        layering_by_year[year] = {}
        layers = layering_by_year[year]
        a_points = {}
        b_points = {}
        for lat in range(len(mhs)):
            for lng in range(len(mhs[lat])):
                if mhs[lat][lng] < b_thershold:
                    continue

                loc = f"({lat}, {lng})"
                lat_ = south + lat*0.05
                lng_ = west + lng*0.05
                if loc in blocks:
                    block = blocks[loc]
                else:
                    block = requests.get(f"https://geo.fcc.gov/api/census/block/find?latitude={lat_}&longitude={lng_}&showall=false&format=json").json()
                    blocks[loc] = block

                state = block["State"]["code"]
                county = block["County"]["name"]
                if state not in DATASET[year]["states"]:
                    continue # skip irrelevant states
                county_ = county.replace("Richmond City", "Richmond").upper()
                if county_ not in DATASET[year]["states"][state]["counties"]:
                    continue # skip mislead counties
                if state not in layers:
                    layers[state] = { "A": {}, "B": {} }
                drugs = mhs[lat][lng]
                if a_threshold is not None:
                    if drugs > a_threshold:
                        if county in b_points: # delete lower
                            del b_points[county]
                            del layers[state]["B"][county]
                        layers[state]["A"][county] = drugs
                        a_points[county] = (lng_, lat_, drugs)
                    else:
                        if county in a_points or county in b_points: # skip redundant
                            continue
                        layers[state]["B"][county] = drugs
                        b_points[county] = (lng_, lat_, drugs)
                else:
                    layers[state]["B"][county] = drugs
                    b_points[county] = (lng_, lat_, drugs)
                plt.text(lng_+0.1, lat_+0.1, f'{county}, {state}', fontsize=9)

        if i > 0:
            if a_threshold is not None:
                lngs, lats, drugs = zip(*a_points.values())
                plt.scatter(lngs, lats, c=drugs, marker="x", cmap="Oranges")
            lngs, lats, drugs = zip(*b_points.values())
            plt.scatter(lngs, lats, c=drugs, marker="o", cmap="summer")

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

        # plt.title("This is a title")

    with open(f"./part1/{drug_name}/layers.json", 'w') as f:
        json.dump(layering_by_year, f, indent=2)

    with open(f"./part1/{drug_name}/blocks.json", 'w') as f:
        json.dump(blocks, f)

    #show
    plt.show()

    """Start/Source/Potential Point Checking"""

    frequency = {}

    for year in [f"20{yy}" for yy in range(10, 16 + 1)]:
        for state in layering_by_year[year]:
            if state not in frequency:
                frequency[state] = {}
            for level in layering_by_year[year][state]:
                for county in layering_by_year[year][state][level]:
                    if county not in frequency[state]:
                        county_ = county.replace("Richmond City", "Richmond").upper()
                        lng, lat = DATASET[year]["states"][state]["counties"][county_]["location"]
                        frequency[state][county] = { "A": 0, "B": 0, "data": [lng, lat, 0] }
                    drugs = layering_by_year[year][state][level][county]
                    frequency[state][county][level] += 1
                    frequency[state][county]["data"][2] += drugs / 7

    START_POINTS = dict([(key, {}) for key in frequency.keys()])
    POTENTIAL_POINTS = dict([(key, {}) for key in frequency.keys()])

    for state in frequency:
        for county, freq in frequency[state].items():
            if a_threshold is None:
                if freq["B"] > 3:
                    START_POINTS[state][county] = freq["data"]
                    if len(START_POINTS[state]) > 3: # 3 at most
                        c, _ = min(START_POINTS[state].items(), key=lambda kv:kv[1][2])
                        del START_POINTS[state][c]
            elif freq["A"] + freq["B"] > 3:
                if freq["data"][2] > a_threshold:
                    START_POINTS[state][county] = freq["data"]
                elif freq["data"][2] > b_thershold:
                    POTENTIAL_POINTS[state][county] = freq["data"]

    for state in POTENTIAL_POINTS:
        if a_threshold is None:
            break
        pt_dict = {}
        for county in POTENTIAL_POINTS[state]:
            county = county.replace("Richmond City", "Richmond").upper()
            for yy in range(10, 16 + 1):
                year = f"20{yy}"
                if year not in pt_dict:
                    pt_dict[year] = []
                ct = DATASET[year]["states"][state]["counties"][county]
                pt_dict[year].append(ct["drugsTotal"] if drug_type is None else ct["drugs"].get(drug_type, 0))
        pt_csv = pd.DataFrame.from_dict(pt_dict)
        pt_csv.to_csv(f"./part1/{drug_name}/potential_{state}.csv", index=False)

    start_points = []
    for state in START_POINTS:
        for county in START_POINTS[state]:
            start_points.append((*START_POINTS[state][county], f"{county}, {state}"))
        # START_POINTS[state] = list(START_POINTS[state].keys())

    plt.subplot(1, 2, 1)
    lngs, lats, drugs, names = zip(*start_points)
    plt.scatter(lngs, lats, c=drugs, marker="o", cmap="Oranges")
    for lng, lat, name in zip(lngs, lats, names):
        plt.text(lng+0.1, lat+0.1, name, fontsize=9)

    if a_threshold is not None:
        potential_points = []
        for state in POTENTIAL_POINTS:
            for county in POTENTIAL_POINTS[state]:
                potential_points.append((*POTENTIAL_POINTS[state][county], f"{county}, {state}"))
            # POTENTIAL_POINTS[state] = list(POTENTIAL_POINTS[state].keys())

        plt.subplot(1, 2, 2)
        lngs, lats, drugs, names = zip(*potential_points)
        plt.scatter(lngs, lats, c=drugs, marker="o", cmap="Purples")
        for lng, lat, name in zip(lngs, lats, names):
            plt.text(lng+0.1, lat+0.1, name, fontsize=9)

    with open(f"./part1/{drug_name}/points.json", 'w') as f:
        json.dump({ "start": START_POINTS, "potential": POTENTIAL_POINTS }, f, indent=2)

    plt.show()

def avaialble_drugs():
    drug_names = set()
    for year in DATASET:
        for state in DATASET[year]["states"].values():
            for county in state["counties"].values():
                drug_names.update(set(county["drugs"].keys()))
    return drug_names

def drugs_average(drug_name):
    s, n = 0, 0
    for year in DATASET:
        for state in DATASET[year]["states"].values():
            for county in state["counties"].values():
                s += county["drugs"].get(drug_name, 0)
                n += 1
    return s / n

# print(avaialble_drugs())
drugs_avg = sorted([(drug, drugs_average(drug)) for drug in avaialble_drugs()], key=lambda x:x[1], reverse=True)
# print(drugs_avg)
# with open('./part1/drugs_avg.csv', 'w') as f:
#     writer = csv.writer(f , lineterminator='\n')
#     writer.writerow(("Drug name", "Average"))
#     for da in drugs_avg:
#         writer.writerow(da)

# exec_drugs("Heroin", 100)
# exec_drugs(None, 600, 2000)
exec_drugs(*drugs_avg[1])
