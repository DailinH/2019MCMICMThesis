import re
import csv
import json
import pandas as pd
import requests
from utils import InlineEncoder

LOCATIONS = {}

# --------------- Geo Locations ---------------

LOCATIONS_CSV = pd.read_csv("./data/raw/locations.csv")

for entry in LOCATIONS_CSV.values:
    entry[0] = entry[0].upper() # COUNTY NAME
    entry[2] = entry[2][1:] # FIPS
    fips = entry[2]
    LOCATIONS[fips] = { k:v for k, v in zip(LOCATIONS_CSV.columns, entry) }

def getCountyAdjacency():
    "Return a list of dicts where each dict has a county FIPS code (key) and a list of FIPS codes of the adjacent counties, not including that county (value)"
    with open("./data/raw/county_adjacency.txt", 'r', encoding="utf-8") as f:
        adj_data = f.read().split('\n')
    reader = csv.reader(adj_data, delimiter='\t')
    ls = {}
    d = {}
    countyfips = ""
    for row in reader:
        if len(row) == 0:
            continue
        if row[1] and row[1] != "":
            if d:
                ls.update(d)
            d = {}
            countyfips = row[1]
            d[countyfips] = []
            "Grab the record on the same line"
            try:
                st = row[3]
                if st != countyfips:
                    d[countyfips].append(st)
            except:
                pass
        else:
            "Grab the rest of the records"
            if row[3] and row[3] != "":
                st = row[3]
                if st != countyfips:
                    d[countyfips].append(st)
    return ls

# --------------- ACS Metadata ---------------

ACS_METADATA = {}

REG_HCVC = re.compile(r"HC(\d+)_VC(\d+)")
REG_FACTOR = re.compile(r"([^;]+); ([^-]+) - (.+)")

for yy in range(10, 16 + 1):
    ACS_METADATA[str(2000 + yy)] = {
        "HC": {},
        "VC": {}
    }
    ACS_CSV = pd.read_csv(f"./data/raw/ACS_{yy}_5YR_DP02_with_ann.csv")
    metadata = ACS_METADATA[str(2000 + yy)]
    raw_data = ACS_CSV.values[0]
    for i in range(3, len(ACS_CSV.columns)):
        hc_code, vc_code = REG_HCVC.match(ACS_CSV.columns[i]).groups()
        hc, vc_t, vc_sub = REG_FACTOR.match(raw_data[i]).groups()
        if not vc_t in metadata["VC"]:
            metadata["VC"][vc_t] = {}
        metadata["VC"][vc_t][vc_code] = vc_sub
        metadata["HC"][hc_code] = hc

# --------------- Save to json ---------------

if __name__ == "__main__":
    with open("./data/locations.json", 'w') as f:
        json.dump(LOCATIONS, f, indent=2)

    with open("./data/adjacency.json", 'w') as f:
        json.dump(getCountyAdjacency(), f, indent=2, cls=InlineEncoder)

    with open("./data/acs_metadata.json", 'w') as f:
        json.dump(ACS_METADATA, f, indent=2)
