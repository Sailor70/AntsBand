import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

#  wybrać 1 zestaw - pozostałe zakomentować i uruchomić.
# test1_name = 'antsBand_tests2'
# test2_name = 'antsBand_tests2_next1'
# folder_name = 'results2'
# excluded_columns = ['notes_in_time_factor', 'similar_times_factor', 'midi_filename']  # results2

# test1_name = 'antsBand_tests3_1'  # + nie usuwać kolumn notes_in_time_factor i similar_times_factor
# test2_name = 'antsBand_tests3_2'
# folder_name = 'results3'
# excluded_columns = ['midi_filename']  # results3

# test1_name = 'antsBand_test_2lines'  # dodatkowe kolumny wynikowe 'xxx2'
# test2_name = 'antsBand_test_2lines2'
# folder_name = 'results_2lines'
# excluded_columns = ['notes_in_time_factor', 'notes_in_time_factor2', 'similar_times_factor', 'similar_times_factor2', 'midi_filename']  # results_2lines

# test1_name = 'antsBand_test_acs'
# test2_name = 'antsBand_tests_acs2'
# folder_name = 'results_acs'
# excluded_columns = ['q', 'notes_in_time_factor', 'similar_times_factor', 'midi_filename']  # results_acs - q zawsze takie same

test1_name = 'antsBand_test_acs2'   # + nie usuwać kolumn
test2_name = 'antsBand_test_acs2_2'
folder_name = 'results_acs2'
excluded_columns = ['midi_filename']

root_path = '../../data/results/'
df = pd.read_csv(root_path + folder_name + '/' + test1_name + '.csv')  # wczytanie serii danych
df2 = pd.read_csv(root_path + folder_name + '/' + test2_name + '.csv')
data = pd.concat([df, df2], ignore_index=True, sort=False)  # połączenie serii danych
data.to_csv(root_path + folder_name + '/' + test1_name + '_merged.csv', index=False)
# print(df.dtypes)
# print(df.to_string())
# print(df.corr().to_string())
# print(df.corr(method='pearson'))
for i, column in enumerate(excluded_columns):
    data = data.drop(column, axis=1)

rows, number_of_cols = data.shape  # liczba kolumn
col_names = list(data.columns)  # nazwy kolumn
correlation = data.corr(method='spearman')  # spearman bardziej uniwersalny, dla cech o charakterze jakościowym
# correlation = df.corr()  # Pearson domyślnie
# correlation.to_csv('../data/results/correlation_results.csv')

# przerobienie macierzy korelacji na serie, pofiltrowanie i sortowanie
corr_series = correlation[correlation < 1].unstack().transpose()\
    .sort_values(ascending=False)\
    .drop_duplicates()
# corr_series = corr_series[corr_series != 0]  # wiedza które nie są w ogóle skorelowane może się przydać
corr_series.to_csv(root_path + folder_name + '/correlation_' + folder_name + '_all_sorted.csv')  # wszystkie korelacje posortowane

positive_corr = corr_series[corr_series > 0.4]  # odfiltrowanie tylko istotniejszych korelacji
print(positive_corr)
negative_corr = corr_series[corr_series < -0.4]
print(negative_corr)
filtered_corr = pd.concat([positive_corr, negative_corr])
print(filtered_corr)
filtered_corr.to_csv(root_path + folder_name + '/correlation_' + folder_name + '_filtered.csv')  # odfiltrowane korelacje posortowane

f = plt.figure(figsize=(19, 15))
plt.matshow(correlation, fignum=f.number)
plt.xticks(range(data.select_dtypes(['number']).shape[1]), data.select_dtypes(['number']).columns, fontsize=14, rotation=45)
plt.yticks(range(data.select_dtypes(['number']).shape[1]), data.select_dtypes(['number']).columns, fontsize=14)
cb = plt.colorbar()
cb.ax.tick_params(labelsize=14)
plt.title('Macierz korelacji', fontsize=16)
plt.savefig(root_path + folder_name + '/' + test1_name + '_plot.png')
plt.show()

# plot alternatywny
# plt.figure(figsize=(12,8))
# sns.heatmap(correlation, cmap="Greens")
# plt.show()

#### MAX/MIN values
# print(col_names)
file_names = ['evaluation_result', 'notes_in_time_factor', 'repeated_sequences_factor', 'cosonance_factor', 'similar_notes_factor',
              'similar_times_factor', 'execution_time', 'cost',
                  'evaluation_result', 'notes_in_time_factor', 'repeated_sequences_factor', 'cosonance_factor', 'similar_notes_factor', 'similar_times_factor', 'cost']
result_columns = ['evaluation_result', 'notes_in_time_factor', 'repeated_sequences_factor', 'cosonance_factor', 'similar_notes_factor', 'similar_times_factor', 'execution_time', 'cost']
if folder_name == 'results_2lines':
    result_columns.extend(['evaluation_result2', 'notes_in_time_factor2', 'repeated_sequences_factor2', 'cosonance_factor2',
                      'similar_notes_factor2', 'similar_times_factor2', 'cost2'])  # dla testu acs2
for j, col in enumerate(excluded_columns):  # usunięcie kolumn niepotrzebnych w danym teście
    if col in file_names:
        file_names.remove(col)
        file_names.remove(col)  # bo podwójne wystąpienia dla testu 2lines
    if col in result_columns:
        result_columns.remove(col)
max_min_data = []
for i, column in enumerate(result_columns):  # col_names dla wszystkich
    row_min_id = data[column].idxmin()
    min_val = data[column].min()
    print('min value of column ', column, ' is: ', min_val)
    file_min = open(root_path + '/max_min_results/' + file_names[i] + '_min.txt', 'a')
    file_min.write(data.loc[[row_min_id]].to_string() + ' test_name: ' + folder_name + ' \n')  # zapisujemy do tekstu bo różne są liczby atrybutów w wynikach
    file_min.close()
    print('whole min test for ', column, ' \n', data.loc[[row_min_id]].to_string())
    row_max_id = data[column].idxmax()
    max_val = data[column].max()
    print('max value of ', column, ' is: ', max_val)
    file_max = open(root_path + '/max_min_results/' + file_names[i] + '_max.txt', 'a')
    file_max.write(data.loc[[row_max_id]].to_string() + ' test_name: ' + folder_name + '\n')
    file_max.close()
    print('whole max test for ', column, ' \n', data.loc[[row_max_id]].to_string())
    max_min_data.append({'parameter': column, 'type': 'min', 'value': min_val, 'row_id': row_min_id})
    max_min_data.append({'parameter': column, 'type': 'max', 'value': max_val, 'row_id': row_max_id})

max_min_df = pd.DataFrame(max_min_data)
max_min_df.to_csv(root_path + folder_name + '/max_min_' + folder_name + '.csv', index=False)

