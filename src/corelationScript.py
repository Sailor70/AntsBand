import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

try:
    df = pd.read_csv('../data/results/antsBand_tests2.csv')  # todo global
except FileNotFoundError:
    print("brak pliku do analizy! ")
# print(df.dtypes)
# print(df.to_string())
# print(df.corr().to_string())
# print(df.corr(method='pearson'))
# cor = df.corr(method='kendall')
df = df.drop('notes_in_time_factor', axis=1)  # usunięcie kolumny bo zawsze taka sama wartość
df = df.drop('similar_times_factor', axis=1)
df = df.drop('midi_filename', axis=1)  # usunięcie kolumny bo niepotrzebna do statystyk - tylko do odsłuchu

rows, number_of_cols = df.shape  # liczba kolumn
col_names = list(df.columns)  # nazwy kolumn
correlation = df.corr(method='spearman')  # spearman bardziej uniwersalny, dla cech o charakterze jakościowym
# correlation = df.corr()  # Pearson domyślnie
# correlation.to_csv('../data/results/correlation_results.csv')

# df_droped = df.drop('midi_filename', axis=1)  # usunięcie kolumny z data frame
# przerobienie macierzy korelacji na serie, pofiltrowanie i sortowanie
corr_series = correlation[correlation < 1].unstack().transpose()\
    .sort_values(ascending=False)\
    .drop_duplicates()
corr_series = corr_series[corr_series != 0]
corr_series.to_csv('../data/results/correlation_all_sorted.csv')  # wszystkie korelacje posortowane

positive_corr = corr_series[corr_series > 0.4]
print(positive_corr)
negative_corr = corr_series[corr_series < -0.4]
print(negative_corr)
filtered_corr = pd.concat([positive_corr, negative_corr])
# filtered_corr = dropped_corr.where(dropped_corr > 0.55, dropped_corr < -0.55)
# filtered_corr = filtered_corr[dropped_corr < -0.6]
print(filtered_corr)
filtered_corr.to_csv('../data/results/correlation_filtered.csv')  # odfiltrowane korelacje posortowane

f = plt.figure(figsize=(19, 15))
plt.matshow(correlation, fignum=f.number)
plt.xticks(range(df.select_dtypes(['number']).shape[1]), df.select_dtypes(['number']).columns, fontsize=14, rotation=45)
plt.yticks(range(df.select_dtypes(['number']).shape[1]), df.select_dtypes(['number']).columns, fontsize=14)
cb = plt.colorbar()
cb.ax.tick_params(labelsize=14)
plt.title('Macierz korelacji', fontsize=16)
plt.show()

# plot alternatywny
# plt.figure(figsize=(12,8))
# sns.heatmap(correlation, cmap="Greens")
# plt.show()

#### MAX/MIN values
# print(col_names)
result_columns = ['evaluation_result', 'repeated_sequences_factor', 'cosonance_factor', 'similar_notes_factor', 'execution_time', 'cost']
max_min_data = []
for i, column in enumerate(result_columns):  # col_names dla wszystkich
    row_min_id = df[column].idxmin()
    min_val = df[column].min()
    print('min value of column ', column, ' is: ', min_val)
    print('whole min test for ', column, ' \n', df.loc[[row_min_id]].to_string())
    row_max_id = df[column].idxmax()
    max_val = df[column].max()
    print('max value of ', column, ' is: ', max_val)
    print('whole max test for ', column, ' \n', df.loc[[row_max_id]].to_string())
    max_min_data.append({'parameter': column, 'type': 'min', 'value': min_val, 'row_id': row_min_id})
    max_min_data.append({'parameter': column, 'type': 'max', 'value': max_val, 'row_id': row_max_id})

max_min_df = pd.DataFrame(max_min_data)
max_min_df.to_csv('../data/results/max_min_tests_results.csv', index=False)

