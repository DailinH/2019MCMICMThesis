import re
import json
import pandas as pd

LOCATIONS = {}

# --------------- Geo Locations ---------------

LOCATIONS_CSV = pd.read_csv("./data/raw/locations.csv")

for entry in LOCATIONS_CSV.values:
    entry[0] = entry[0].upper() # COUNTY NAME
    entry[2] = entry[2][1:] # FIPS
    fips = entry[2]
    LOCATIONS[fips] = { k:v for k, v in zip(LOCATIONS_CSV.columns, entry) }

# --------------- ACS Metadata ---------------

ACS_METADATA = {}

REG_HCVC = re.compile(r"HC(\d+)_VC(\d+)")
REG_FACTOR = re.compile(r"([^;]+); ([^-]+) - (.+)")

for yy in range(10, 16 + 1):
    ACS_METADATA[2000 + yy] = {
        "HC": {},
        "VC": {}
    }
    ACS_CSV = pd.read_csv(f"./data/raw/ACS_{yy}_5YR_DP02/ACS_{yy}_5YR_DP02_with_ann.csv")
    metadata = ACS_METADATA[2000 + yy]
    raw_data = ACS_CSV.values[0]
    for i in range(3, len(ACS_CSV.columns)):
        hc_code, vc_code = REG_HCVC.match(ACS_CSV.columns[i]).groups()
        hc, vc_t, vc_sub = REG_FACTOR.match(raw_data[i]).groups()
        if not vc_t in metadata["VC"]:
            metadata["VC"][vc_t] = {}
        metadata["VC"][vc_t][vc_code] = vc_sub
        metadata["HC"][hc_code] = hc

# --------------- Save to json ---------------

with open("./data/locations.json", 'w') as f:
    json.dump(LOCATIONS, f, indent=2)

with open("./data/acs_metadata.json", 'w') as f:
    json.dump(ACS_METADATA, f, indent=2)
