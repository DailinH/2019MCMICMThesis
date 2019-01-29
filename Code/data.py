import re
import json
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile
from utils import InlineEncoder

with open("./data/locations.json") as f:
    LOCATIONS = json.load(f)

with open("./data/accept_factors.json") as f:
    ACCEPT_FACTORS = json.load(f)

DATASET = {}

# --------------- NFLIS ---------------

NFLIS_EXCEL = pd.read_excel("./data/raw/MCM_NFLIS_Data.xlsx", sheet_name=1) # read data sheet

for [year, state, county, fipsS, fipsC, fips, drug, count, countC, countS] in NFLIS_EXCEL.values:
    year = str(year)
    fipsS = f'{fipsS:02d}'
    fipsC = f'{fipsC:03d}'
    fips = f'{fips:05d}'

    if not year in DATASET:
        DATASET[year] = {
            "factors": [],
            "weights": [],
            "states": {}
        }

    states = DATASET[year]["states"]
    if not state in states:
        states[state] = {
            "fips": fipsS,
            "drugsTotal": countS,
            "counties": {}
        }

    counties = states[state]["counties"]
    if not county in counties:
        counties[county] = {
            "fipsLocal": fipsC,
            "fips": fips,
            "location": [LOCATIONS[fips]["lng"], LOCATIONS[fips]["lat"]],
            "drugsTotal": countC,
            "drugs": {}
        }

    counties[county]["drugs"][drug] = count

# --------------- ACS ---------------

for yy in range(10, 16 + 1):
    ASC_CSV = pd.read_csv(f"./data/raw/ACS_{yy}_5YR_DP02_with_ann.csv")
    year = str(2000 + yy)
    metadata = { v:i for i, v in enumerate(ASC_CSV.columns)}
    accepts = ACCEPT_FACTORS[year]
    indices = []
    for vc in sum([list(vc_t.keys()) for vc_t in accepts["VC"].values()], []):
        for hc in accepts["HC"]:
            code = f"HC{hc}_VC{vc}"
            if code in metadata:
                indices.append(metadata[code])
                DATASET[year]["factors"].append(code)
    for entry in ASC_CSV.values[1:]:
        fips = str(entry[1])
        state = LOCATIONS[fips]["state"]
        county = LOCATIONS[fips]["county"]
        # there may be a county where factor exists but drugs report does not.
        counties = DATASET[year]["states"][state]["counties"]
        if county in counties:
            counties[county]["factors"] = [float(entry[i]) for i in indices]

# --------------- Save to json ---------------

if __name__ == "__main__":
    with open("./data/dataset.json", 'w') as f:
        json.dump(DATASET, f, indent=2, cls=InlineEncoder)
