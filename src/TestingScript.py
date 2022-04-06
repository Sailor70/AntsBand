import time

from mido import MidiFile
import pandas as pd
from joblib import Parallel, delayed
from joblib._memmapping_reducer import has_shareable_memory

from AntsBandMain import AntsBand
from AntsBandService import calculate_similarity, evaluate_melody_for_testing

#  tylko 1 ścieżka melodyczna
#  46 węzłów ma graf w badanej ścieżce

testing = pd.DataFrame({'ant_count': [], 'generations': [], 'alpha': [], 'beta': [], 'rho': [], 'q': [], 'sigma': [],
                        'evaluation_result': [], 'notes_in_time_factor': [], 'repeated_sequences_factor': [],
                        'cosonance_factor': [],
                        'similar_notes_factor': [], 'similar_times_factor': [], 'midi_filename': []})
master_results = []


def get_test_mean(params: dict):
    result = []
    file_name = ''
    antsBand = AntsBand(midi_file=MidiFile('../data/theRockingAnt.mid', clip=True), tracks_numbers=[3],
                        keep_old_timing=True, result_track_length=1, algorithm_type=0, ant_count=params['ant_count'], generations=params['generations'],
                        alpha=params['alpha'], beta=params['beta'], rho=params['rho'], q=params['q'], phi=0.1, q_zero=0.9, sigma=params['sigma'])
    for i in range(10):
        start_time = time.time()
        midi_result, tracks_data, cost = antsBand.start()
        execution_time = time.time() - start_time
        if i == 1:
            file_name = "result_test" + str(time.time()) + ".mid"
            midi_result.save("../data/midi_results/" + file_name)
        evaluation_result, notes_in_time_factor, repeated_sequences_factor, cosonance_factor = evaluate_melody_for_testing(midi_result, tracks_data[0])
        similar_notes_factor, similar_times_factor = calculate_similarity(midi_result, tracks_data[0], MidiFile('../data/theRockingAnt.mid', clip=True))
        #  new_row = pd.Series(data={'evaluation_result': evaluation_result, 'notes_in_time_factor': notes_in_time_factor, 'repeated_sequences_factor': repeated_sequences_factor, 'cosonance_factor': cosonance_factor, 'similar_notes_factor': similar_notes_factor, 'similar_times_factor': similar_times_factor, 'midi_filename': file_name}, name=str(i))
        result.append({'evaluation_result': evaluation_result, 'notes_in_time_factor': notes_in_time_factor, 'repeated_sequences_factor': repeated_sequences_factor,
                       'cosonance_factor': cosonance_factor, 'similar_notes_factor': similar_notes_factor, 'similar_times_factor': similar_times_factor,
                       'execution_time': execution_time, 'cost': cost})

    # print(result)
    result = dict_mean(result)
    result["midi_filename"] = file_name
    test = params | result
    master_results.append(test)
    # return test

def dict_mean(dict_list):
    mean_dict = {}
    for key in dict_list[0].keys():
        mean_dict[key] = sum(d[key] for d in dict_list) / len(dict_list)
    return mean_dict

def get_tests_results():

    # params = [{'ant_count': 10, 'generations': 10, 'alpha': 1.0, 'beta': 5.0, 'rho': 0.5, 'q': 10, 'sigma': 10},
    #           {'ant_count': 10, 'generations': 100, 'alpha': 1.0, 'beta': 5.0, 'rho': 0.5, 'q': 10, 'sigma': 10},
    #           {'ant_count': 20, 'generations': 20, 'alpha': 1.0, 'beta': 5.0, 'rho': 0.5, 'q': 100, 'sigma': 20},
    #           {'ant_count': 20, 'generations': 30, 'alpha': 2.0, 'beta': 2.0, 'rho': 0.5, 'q': 10, 'sigma': 10},
    #           {'ant_count': 20, 'generations': 30, 'alpha': 0.1, 'beta': 10.0, 'rho': 0.5, 'q': 20, 'sigma': 10},
    #           {'ant_count': 100, 'generations': 10, 'alpha': 5.0, 'beta': 1.0, 'rho': 0.5, 'q': 10, 'sigma': 10},
    #           {'ant_count': 100, 'generations': 100, 'alpha': 5.0, 'beta': 1.0, 'rho': 0.5, 'q': 20, 'sigma': 10},
    #           {'ant_count': 30, 'generations': 30, 'alpha': 3.0, 'beta': 3.0, 'rho': 0.5, 'q': 10, 'sigma': 100},
    #           {'ant_count': 30, 'generations': 40, 'alpha': 1.0, 'beta': 5.0, 'rho': 0.1, 'q': 20, 'sigma': 10},
    #           {'ant_count': 40, 'generations': 50, 'alpha': 1.0, 'beta': 5.0, 'rho': 0.9, 'q': 10, 'sigma': 10},
    #           {'ant_count': 40, 'generations': 60, 'alpha': 5.0, 'beta': 5.0, 'rho': 0.5, 'q': 30, 'sigma': 30}]

    # na to potrzeba około 2dni by się wszystko wykonało
    # ant_counts = [1, 5, 10, 20, 30, 50, 100]
    # generations = [1, 10, 30, 50, 100]
    # alphas = [0.1, 0.5, 1.0, 2.0, 5.0]
    # betas = [0.1, 1.0, 2.0, 3.0, 5.0, 10.0]
    # rhos = [0.1, 0.5, 0.9]
    # qs = [1, 5, 10, 20, 100]
    # sigmas = [1, 5, 10, 20, 50, 100]

    ant_counts = [1, 5, 10]  # 100 to jest fest dużo
    generations = [1, 10]
    alphas = [0.1, 0.5]
    betas = [0.1, 1.0]
    rhos = [0.1, 0.5]
    qs = [1, 5]
    sigmas = [1, 5]
    param_sets = []
    for a, count in enumerate(ant_counts):
        for b, gen in enumerate(generations):
            for c, alp in enumerate(alphas):
                for d, bet in enumerate(betas):
                    for e, rho in enumerate(rhos):
                        for f, q in enumerate(qs):
                            for g, sig in enumerate(sigmas):
                                param_sets.append({'ant_count': count, 'generations': gen, 'alpha': alp, 'beta': bet, 'rho': rho, 'q': q, 'sigma': sig})
    print(str(len(param_sets)), " tests has been created")
    results = []
    start_t = time.time()

    # przy tej metodzie niewielki wzrost wydajności
    Parallel(n_jobs=6, require='sharedmem')(
        delayed(has_shareable_memory)(get_test_mean(params)) for params in param_sets)

    # for i, params in enumerate(param_sets):
    #     results.append(get_test_mean(params))

    execution_time = time.time() - start_t
    print("total execution time: ", execution_time)
    df = pd.DataFrame(master_results)
    df.to_csv('../data/results/antsBand_tests2.csv', index=False)  # bez kolumny indexu
    # df.to_csv('../data/results/antsBand_tests.csv', index_label='id')  # nazwanie kolumny z id bo teraz bez nazwy
    print(master_results)



if __name__ == '__main__':
    get_tests_results()

