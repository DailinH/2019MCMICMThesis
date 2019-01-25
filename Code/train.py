import json
from sklearn import linear_model

with open("./data/dataset.json", 'r') as f:
    DATASET = json.load(f)

def train(year):
    train_y = []
    train_x = []

    for state in DATASET[year]["states"].values():
        for county in state["counties"].values():
            if "factors" in county:
                train_x.append(county["factors"])
                train_y.append(county["drugsTotal"])

    clf = linear_model.Lasso(alpha=0.1)
    clf.fit(train_x, train_y)

    # print(clf.coef_)
    # print(clf.intercept_)
    return clf

for yy in range(10, 16 + 1):
    year = str(2000 + 16)
    print(train(year))
