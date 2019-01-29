from utils import InlineEncoder, DATASET, LOCATIONS, get_metadata
import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import scale

# VC = {}
# for year, data in DATASET.items():
#     for n_state, state in data["states"].items():
#         for n_county, county in state["counties"].items():
#             if "factors" not in county:
#                 continue
#             for i, factor in enumerate(county["factors"]):
#                 n_factor = data["factors"][i]
#                 description = get_metadata(year, n_factor)
#                 if description not in VC:
#                     VC[description] = {}
#                 if n_county not in VC[description]:
#                     VC[description][n_county] = {}
#                 VC[description][n_county][year] = factor
# with open("./part2/vc.json", 'w') as f:
#     json.dump(VC, f, indent=2, cls=InlineEncoder)

with open("./data/adjacency.json", 'r') as f:
    ADJACENCY = json.load(f)

with open("./part1/Total/points.json", 'r') as f:
    START_POINTS, POTENTIAL_POINTS = json.load(f).values()


def srcs_fips(potential=False):
    sources = []
    for n_state in START_POINTS:
        for n_county in START_POINTS[n_state]:
            for data in DATASET.values():
                try:
                    n_county = n_county.replace("Richmond City", "Richmond").upper()
                    sources.append(data["states"][n_state]["counties"][n_county]["fips"])
                    break
                except:
                    continue
    if potential:
        for n_state in POTENTIAL_POINTS:
            for n_county in POTENTIAL_POINTS[n_state]:
                for data in DATASET.values():
                    try:
                        n_county = n_county.replace("Richmond City", "Richmond").upper()
                        sources.append(data["states"][n_state]["counties"][n_county]["fips"])
                        break
                    except:
                        continue
    return sources


def county_by_fips(fips, year):
    try:
        loc = LOCATIONS[fips]
        n_state = loc["state"]
        n_county = loc["county"]
        return DATASET[str(year)]["states"][n_state]["counties"][n_county]
    except:
        return None


def drugs_by_fips(fips, year):
    try:
        return county_by_fips(fips, year)["drugsTotal"]
    except:
        return 0


def calc_srcs_lambda(sources, years, store_years=True):
    lambdas = {}
    for year in years:
        for source in sources:
            adjs = get_adjacency(source)
            Fsrc = drugs_by_fips(source, year)
            sFdes = [drugs_by_fips(adj, year) for adj in adjs]
            if store_years:
                if source not in lambdas:
                    lambdas[source] = {}
                lambdas[source][int(year)] = Fsrc / (Fsrc + sum(sFdes))
            else:
                if source not in lambdas:
                    lambdas[source] = []
                lambdas[source].append(Fsrc / (Fsrc + sum(sFdes)))
    return lambdas


def get_adjacency(fips):
    return [
        adj for adj in ADJACENCY[fips]
        if LOCATIONS[adj]["state"] in START_POINTS
    ]


def get_factors(sources, n_factors):
    factors = {
        n_factor: {src: []
                   for src in sources}
        for n_factor in n_factors
    }
    for year in [f"20{yy}" for yy in range(10, 16 + 1)]:
        iks = [DATASET[year]["factors"].index(ik) for ik in n_factors]
        for source in sources:
            loc = LOCATIONS[source]
            n_state = loc["state"]
            n_county = loc["county"]
            ks = [
                DATASET[year]["states"][n_state]["counties"][n_county]
                ["factors"][i] for i in iks
            ]
            for factor, k in zip(factors.values(), ks):
                factor[source].append(k)
    return factors


if __name__ == "__main__":
    sources = srcs_fips()
    sources.pop()
    sources = sources[1:]
    years = list(map(str, range(2010, 2016 + 1)))
    lambdas = calc_srcs_lambda(sources, years, False)
    print(lambdas)

    fig = plt.figure()
    for source in lambdas:
        plt.plot(years, lambdas[source], label=source)

    plt.legend(loc="upper left")
    plt.show()

    # y
    mean_lambdas = np.mean(list(lambdas.values()))
    lambdas_diff = np.mean(list(lambdas.values()), 1) # - mean_lambdas

    # X
    n_factors = [
        # "HC03_VC07",
        # "HC03_VC17",
        "HC03_VC93",
        "HC03_VC13"
    ]
    factors = list(get_factors(sources, n_factors).values())
    means = []
    diffs = []
    for i, factor in enumerate(factors):
        values = np.array(list(factor.values()))
        # values = (values - np.min(values)) / (np.max(values) - np.min(values))
        means.append(np.mean(values))
        diffs.append(np.mean(values, 1))

    # diffs = (diffs - np.min(diffs)) / (np.max(diffs) - np.min(diffs))
    fig = plt.figure()
    plt.plot(sources, 10*lambdas_diff, label="λ")
    for n_factor, diff in zip(n_factors, diffs):
        plt.plot(sources, diff, label=get_metadata(2010, n_factor, False))
    plt.legend(loc="upper left")
    plt.show()

    X = [np.array(list(xs)) for xs in zip(*diffs)]
    # X = np.array([np.array(diffs[0]) * np.array(diffs[1])]).reshape(-1, 1)
    y = lambdas_diff
    # plt.plot(sources, 3*y)
    # plt.plot(sources, X)
    # plt.show()

    reg = LinearRegression()
    reg.fit(X, y)
    print(reg.score(X, y))
    print(reg.coef_)
    print(reg.intercept_)
