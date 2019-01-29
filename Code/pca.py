from utils import DATASET, ACS_METADATA, train_data

import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import mean_squared_error

def evaluate(pca: PCA, x: np.array):
    z = pca.transform(x)
    x_ = pca.inverse_transform(z)
    return ((x-x_)**2).mean(1) / (x**2).mean(1)

for yy in range(10, 16 + 1):
    year = f"20{yy}"
    train_x, train_y = train_data(year)

    try:
        pca = PCA(n_components="mle")
        pca.fit(train_x)
    except:
        continue

    epsilon = evaluate(pca, train_x)
    print(pca.explained_variance_ratio_)
    print(pca.singular_values_)
