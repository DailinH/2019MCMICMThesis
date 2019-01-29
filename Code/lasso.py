from utils import DATASET, ACS_METADATA, train_data, get_metadata

import re
import json
from sklearn import linear_model
from sklearn.metrics import mean_squared_error

RESULT = {}

for yy in range(10, 16 + 1):
    year = str(2000 + yy)
    metadata = ACS_METADATA[year]
    train_x, train_y = train_data(year)
    RESULT[year] = {}

    clf = linear_model.LassoLars(alpha=0.1, max_iter=100000)
    clf.fit(train_x, train_y)

    coefs = sorted(list(enumerate(clf.coef_)), key=lambda k: abs(k[1]), reverse=True)
    factors = [(i, v, DATASET[year]["factors"][i]) for (i, v) in [v for v in coefs if True]]
    for i, coef, factor in factors:
        RESULT[year][get_metadata(year, factor)] = coef

if __name__ == "__main__":
    with open("./part2/lasso_result.json", 'w') as f:
        json.dump(RESULT, f, indent=2)
