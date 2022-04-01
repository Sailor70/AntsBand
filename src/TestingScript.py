from mido import MidiFile

from AntsBandMain import AntsBand
from src.AntsBandService import evaluate_melody, calculate_similarity


for i in range(1, 200, 5):  # parametr
    result = []
    for _ in range(10):   # 10 powtórzeń i brać średnią
        # zbierać dane do resulta i później do pliku albo od razu do pliku.
        antsBand = AntsBand(midi_file=MidiFile('./data/theRockingAnt.mid', clip=True), tracks_numbers=[2, 3],
                            keep_old_timing=True, result_track_length=1, algorithm_type=0, ant_count=i, generations=10,
                            alpha=1.0, beta=5, rho=0.9, q=1, phi=0.1, q_zero=0.9, sigma=10.0)
        midi_result, tracks_data = antsBand.start()
        print("Eval result: ", evaluate_melody(midi_result, tracks_data[1]))
        calculate_similarity(midi_result, tracks_data[1], MidiFile('./data/theDreamingAnt.mid', clip=True))