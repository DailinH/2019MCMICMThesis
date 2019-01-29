import re
import json
from sklearn.preprocessing import StandardScaler, scale

with open("./data/dataset.json", 'r') as f:
    DATASET = json.load(f)

with open("./data/locations.json", 'r') as f:
    LOCATIONS = json.load(f)

with open("./data/acs_metadata.json", 'r') as f:
    ACS_METADATA = json.load(f)

def train_data(year, standardise=True):
    train_x = []
    train_y = []

    for state in DATASET[year]["states"].values():
        for county in state["counties"].values():
            if "factors" in county:
                train_x.append(county["factors"])
                train_y.append(county["drugsTotal"])

    if standardise:
        train_x = scale(train_x)
    return (train_x, train_y)

REG_HCVC = re.compile(r"HC(\d+)_VC(\d+)")

def get_metadata(year, code, detail=True):
    metadata = ACS_METADATA[str(year)]
    hc, vc = REG_HCVC.match(code).groups()
    for vc_t in metadata["VC"]:
        if vc in metadata["VC"][vc_t]:
            if detail:
                return f"{metadata['HC'][hc]}; {vc_t} - {metadata['VC'][vc_t][vc]}"
            else:
                return metadata['VC'][vc_t][vc]

REG_BLANK = re.compile(r'\s+')

# from https://stackoverflow.com/questions/13249415/
class InlineEncoder(json.JSONEncoder):
    def iterencode(self, o, _one_shot=False):
        list_lvl = 0
        for s in super(InlineEncoder, self).iterencode(o, _one_shot=_one_shot):
            if s.startswith('['):
                list_lvl += 1
                s = REG_BLANK.sub('', s).rstrip()
            elif 0 < list_lvl:
                s = REG_BLANK.sub(' ', s).rstrip()
                if s and s[-1] == ',':
                    s = s[:-1] + self.item_separator
                elif s and s[-1] == ':':
                    s = s[:-1] + self.key_separator
            if s.endswith(']'):
                list_lvl -= 1
            yield s
