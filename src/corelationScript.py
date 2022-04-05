import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def histogram_intersection(a, b):
    v = np.minimum(a, b).sum().round(decimals=1)
    return v


df = pd.read_csv('../data/antsBand_tests.csv')
# with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified al
#     print(df)
# print(df.corr(method='pearson'))
print(df.dtypes)
print(df.to_string())
print(df.corr().to_string())
# print(df.corr(method=histogram_intersection))
# cor = df.corr(method=histogram_intersection)
cor = df.corr(method='kendall')

plt.matshow(cor)
plt.show()