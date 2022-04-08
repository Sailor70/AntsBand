import time

from mido import MidiFile
import pandas as pd

from AntsBandMain import AntsBand
from AntsBandService import calculate_similarity, evaluate_melody_for_testing

#  2 ścieżki melodyczne - dreaming ant
#  z podziałem i zachowaniem czasu
# 2 iteracje testu


def get_test_mean(params: dict):
    result = []
    file_name = ''
    antsBand = AntsBand(midi_file=MidiFile('../data/theDreamingAnt.mid', clip=True), tracks_numbers=[2, 3],     # 2 - lead, 3 - bas
                        keep_old_timing=True, result_track_length=1, algorithm_type=0, ant_count=params['ant_count'], generations=params['generations'],
                        alpha=params['alpha'], beta=params['beta'], rho=params['rho'], q=params['q'], phi=0.1, q_zero=0.9, sigma=params['sigma'])
    for i in range(10):
        start_time = time.time()
        midi_result, tracks_data, cost = antsBand.start_and_divide(4, False)
        execution_time = time.time() - start_time
        if i == 1:
            file_name = "result_test" + str(time.time()) + ".mid"
            midi_result.save("../data/results/results_2lines/1/" + file_name)
            # midi_result.save("../data/results/results_2lines/2/" + file_name)
        evaluation_result, notes_in_time_factor, repeated_sequences_factor, cosonance_factor = evaluate_melody_for_testing(midi_result, tracks_data[0])
        evaluation_result2, notes_in_time_factor2, repeated_sequences_factor2, cosonance_factor2 = evaluate_melody_for_testing(midi_result, tracks_data[1])
        similar_notes_factor, similar_times_factor = calculate_similarity(midi_result, tracks_data[0], MidiFile('../data/theDreamingAnt.mid', clip=True))
        similar_notes_factor2, similar_times_factor2 = calculate_similarity(midi_result, tracks_data[1], MidiFile('../data/theDreamingAnt.mid', clip=True))
        result.append({'evaluation_result': evaluation_result, 'notes_in_time_factor': notes_in_time_factor, 'repeated_sequences_factor': repeated_sequences_factor,
                       'cosonance_factor': cosonance_factor, 'similar_notes_factor': similar_notes_factor, 'similar_times_factor': similar_times_factor,
                       'execution_time': execution_time, 'cost': cost[0], 'evaluation_result2': evaluation_result2, 'notes_in_time_factor2': notes_in_time_factor2,
                       'repeated_sequences_factor2': repeated_sequences_factor2, 'cosonance_factor2': cosonance_factor2, 'similar_notes_factor2': similar_notes_factor2,
                       'similar_times_factor2': similar_times_factor, 'cost2': cost[1]})
    result = dict_mean(result)
    result["midi_filename"] = file_name
    test = params | result
    return test

def dict_mean(dict_list):
    mean_dict = {}
    for key in dict_list[0].keys():
        mean_dict[key] = sum(d[key] for d in dict_list) / len(dict_list)
    return mean_dict

def get_tests_results():
    # params = {'ant_count': 25, 'generations': 20, 'alpha': 1.0, 'beta': 2.0, 'rho': 0.2, 'q': 1, 'sigma': 10}
    # param_sets = [{'ant_count': 1, 'generations': 1, 'alpha': 1.0, 'beta': 5.0, 'rho': 0.5, 'q': 10, 'sigma': 10},
    #           {'ant_count': 1, 'generations': 10, 'alpha': 1.0, 'beta': 5.0, 'rho': 0.5, 'q': 10, 'sigma': 10},
    #           {'ant_count': 2, 'generations': 2, 'alpha': 1.0, 'beta': 5.0, 'rho': 0.5, 'q': 100, 'sigma': 20},
    #           {'ant_count': 2, 'generations': 3, 'alpha': 2.0, 'beta': 2.0, 'rho': 0.5, 'q': 10, 'sigma': 10}]

    # faza 1 - 4320 testów
    ant_counts = [1, 5, 10, 20]
    generations = [1, 10, 20]
    # faza druga - tylko ant_counts i generations zmieniono. 1440 testów
    # ant_counts = [30, 60]
    # generations = [30, 50]
    alphas = [0.1, 0.5, 2.0, 5.0]
    betas = [0.1, 1.0, 2.0, 5.0, 10.0]
    rhos = [0.2, 0.5, 0.9]
    qs = [1, 5]
    sigmas = [1, 5, 10]
    param_sets = []
    for a, count in enumerate(ant_counts):
        for b, gen in enumerate(generations):
            for c, alp in enumerate(alphas):
                for d, bet in enumerate(betas):
                    for e, rho in enumerate(rhos):
                        for f, q in enumerate(qs):
                            for g, sig in enumerate(sigmas):
                                param_sets.append({'ant_count': count, 'generations': gen,
                                                   'alpha': alp, 'beta': bet, 'rho': rho, 'q': q, 'sigma': sig})
    print(str(len(param_sets)), " tests has been created")
    results = []
    start_t = time.time()

    for i, params in enumerate(param_sets):
        results.append(get_test_mean(params))
        if i % 50 == 0:  # dla bezpieczeństwa zapis co 50 testów
            df = pd.DataFrame(results)
            df.to_csv('../data/results/results_2lines/antsBand_test_2lines.csv', index=False)   # faza pierwsza
            # df.to_csv('../data/results/results_2lines/antsBand_tests_2lines2.csv', index=False)

    execution_time = time.time() - start_t
    print("total execution time: ", execution_time)
    df = pd.DataFrame(results)
    df.to_csv('../data/results/results_2lines/antsBand_test_2lines.csv', index=False)
    # df.to_csv('../data/results/results_2lines/antsBand_test_2lines.csv', index=False)  # bez kolumny indexu  todo jakiś generowany name



if __name__ == '__main__':
    get_tests_results()

