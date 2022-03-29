import copy
import random

import numpy as np
from mido import Message, MidiTrack
from mido import MidiFile
from AntSystem import ACO, GraphAS
from AntColonySystem import ACS, GraphACS
from midiPlayer import prepare_and_play
from AntsBandService import plot, evaluate_melody, calculate_similarity


class AntsBand(object):
    def __init__(self, midi_file: MidiFile, tracks_numbers: [int], keep_old_timing: bool, result_track_length: int,
                 algorithm_type: int, ant_count: int, generations: int, alpha: float, beta: float, rho: float,
                 q: int, phi: float, q_zero: float, sigma: float):

        self.midi_file = midi_file
        self.tracks_numbers = tracks_numbers
        self.available_distances = [0.1, 0.5, 1, 5, 10, 100]
        self.keep_old_timing = keep_old_timing
        self.result_track_length = result_track_length
        self.algorithm_type = algorithm_type
        self.Q = q
        self.rho = rho
        self.beta = beta
        self.alpha = alpha
        self.ant_count = ant_count
        self.generations = generations
        self.phi = phi
        self.q_zero = q_zero
        self.sigma = sigma
        self.clocks_per_click = 24

    def distance(self, a: int, b: int):
        result = abs(a - b)
        if result == 0:
            return self.available_distances[random.randint(4, 5)]  # availableDistances[random.randint(3, 5)]
        else:
            return result

    def read_notes_from_track(self, melody_track: MidiTrack):
        notes = []  # zawiera wysokości kolejno zagranych dźwięków w oryginalnej ścieżce
        notes_messages = []  # zawiera kolejne pełne eventy midi z oryginalnej ścieżki
        for i, msg in enumerate(melody_track):  # przeanalizuj każdy event midi z ścieżki
            if msg.type == 'note_on':  # interesują nas tylko eventy dla nut
                notes.append(msg.note)
                j = i+1
                while melody_track[j].type != 'note_off' or melody_track[j].note != msg.note:
                    j += 1
                notes_messages.append([msg,melody_track[j]])
                # notes_messages.append([msg,
                #                        Message('note_off', channel=msg.channel, note=msg.note, velocity=msg.velocity, time=melody_track[i+1].time)])
        return [notes, notes_messages]

    def get_new_aco_melody_for_instrument(self, notes: list):
        cost_matrix = []
        rank = len(notes)
        for i in range(rank):
            row = []
            for j in range(rank):
                row.append(self.distance(notes[i], notes[j]))
            cost_matrix.append(row)
        if self.algorithm_type == 0:
            aco = ACO(self.ant_count, self.generations, self.alpha, self.beta, self.rho, self.Q)
            # aco = ACO(10, 10, 1.0, 5, 0.9, 1, 2)
            # ACO(1, 1, 5.0, 0, 0.01, 1, 2) - ustawienie do odtworzenia orginalnego
            # utworu ( ale tylko gdy mrówka zaczenie w dobrym miejscu - w nucie początkowej ? - to zagra tak samo)
            # aco = ACO(10, 100, 1.0, 8.0, 0.5, 10, 2)
            graph = GraphAS(cost_matrix, rank, self.sigma)
            path, cost = aco.solve(graph)
            print('cost: {}, path: {}'.format(cost, path))
        else:
            acs = ACS(self.ant_count, self.generations, self.alpha, self.beta, self.rho, phi=self.phi, q_zero=self.q_zero)
            graph = GraphACS(cost_matrix, rank, self.sigma)
            path, cost = acs.solve(graph)
            print('cost_acs: {}, path_acs: {}'.format(cost, path))
        # plot(notes, path)  # wykres
        return path

    def quantizeRound(self, value):  # obcina dźwięki krótsze niż self.clocks_per_click/2 ?
        return int(self.clocks_per_click * round(value / self.clocks_per_click))

    def start(self):
        try:
            self.clocks_per_click = self.midi_file.tracks[0][0].clocks_per_click
        except AttributeError:
            print("Nie masz w pliku clocks_per_click!")
            raise
        tracks_data = []
        for track_number in self.tracks_numbers:
            # odczyt nut i eventów midi ze ścieżek
            line_notes, line_notes_messages = self.read_notes_from_track(self.midi_file.tracks[track_number])
            # ACO dla lini melodycznych
            line_path = self.get_new_aco_melody_for_instrument(line_notes)
            # utworzenie nowej ścieżki dla instrumentu
            line_melody_track = self.build_new_melody_track_from_original(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            # utworzenie pliku wynikowego przez podmianę ścieżek
            self.midi_file.tracks[track_number] = line_melody_track
            tracks_data.append({'track_number': track_number, 'line_path': line_path, 'line_notes': line_notes, 'line_melody_track': line_melody_track})

        # self.midi_file.save("./data/result.mid")
        # prepare_and_play("./data/result.mid")
        return [self.midi_file, tracks_data]

    def start_and_extend(self, track_length: int, not_selected_paths: [int]):
        try:
            self.clocks_per_click = self.midi_file.tracks[0][0].clocks_per_click
        except AttributeError:
            print("Nie masz w pliku clocks_per_click!")
            raise
        tracks_data = []
        for track_number in self.tracks_numbers:
            line_notes, line_notes_messages = self.read_notes_from_track(self.midi_file.tracks[track_number])
            line_path = []
            for l in range(track_length):
                line_path.extend(self.get_new_aco_melody_for_instrument(line_notes))  # ścieżka składa się tylko z indeksów line_notes nierozszerzonego utworu
            line_notes = line_notes*track_length  # replikacja
            # line_notes_messages = line_notes_messages*track_length
            line_notes_messages = self.replicate_and_correct_time(line_notes_messages, track_length)
            line_melody_track = self.build_new_melody_track(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            self.midi_file.tracks[track_number] = line_melody_track
            tracks_data.append({'track_number': track_number, 'line_path': line_path, 'line_notes': line_notes, 'line_melody_track': line_melody_track})
        self.extend_unedited_paths(not_selected_paths, track_length)
        # self.midi_file.save("./data/result.mid")
        # prepare_and_play("./data/result.mid")
        return [self.midi_file, tracks_data]

    def replicate_and_correct_time(self, line_notes_messages: list, track_length):
        tact_length = self.clocks_per_click * self.midi_file.tracks[0][0].numerator * self.midi_file.tracks[0][0].denominator
        print("tact length: ", tact_length)
        time_counter = 0
        for i, msg in enumerate(line_notes_messages):  # obliczenie całkowitego czasu linii melodycznej
            time_counter += msg[0].time
            time_counter += msg[1].time
        last_tact_time = time_counter % tact_length  # taka wartość czasu brakuje w ostatnim takcie aby był pełny
        time_to_add = tact_length - last_tact_time  # taką wartość czasu należy dodać do kolejnej powtórzonej linii melodycznej
        print("time_counter: ", time_counter)
        print("time_to_add: ", time_to_add)
        next_line = copy.deepcopy(line_notes_messages)
        next_line[0][0].time += time_to_add  # dodanie brakującego czasu do pierwszego eventu kolejnego powtórzenia melodii
        for i in range(track_length-1):
            line_notes_messages.extend(next_line)
        return line_notes_messages

    def ordered_phrases_to_single_path(self, phrase_paths: list, phrases_notes_messages: list, phrase_notes: list, order: [int]):
        line_path = []
        line_notes_messages = []
        line_notes = []  # potrzebne do sumarycznego wykresu
        for i in order:
            line_notes_messages.extend(phrases_notes_messages[i])
            line_notes.extend(phrase_notes[i])
            phrase_paths[i] = [x+i*len(phrase_paths[i]) for x in phrase_paths[i]]  # przemnożenie indeksów
            line_path.extend(phrase_paths[i])
        return [line_path, line_notes_messages, line_notes]

    def start_and_divide(self, split: int, mix_phrases: bool):
        # print(self.midi_file.tracks[0][0])
        try:
            self.clocks_per_click = self.midi_file.tracks[0][0].clocks_per_click
        except AttributeError:
            print("Nie masz w pliku clocks_per_click!")
            raise
        tracks_data = []
        for track_number in self.tracks_numbers:
            # odczyt nut i eventów midi ze ścieżek
            line_notes, line_notes_messages = self.read_notes_from_track(self.midi_file.tracks[track_number])
            phrase_notes = np.array_split(line_notes, split)
            phrases_notes_messages = np.array_split(line_notes_messages, split)
            phrase_paths = []
            order = []
            for i in range(split):
                phrase_paths.append(self.get_new_aco_melody_for_instrument(phrase_notes[i]))
                order.append(i)
            random.shuffle(order)  # losowanie kolejności tablic - może mrówkami?
            # print(order)
            # print(phrase_paths)
            line_path, line_notes_messages, line_notes = self.ordered_phrases_to_single_path(phrase_paths, phrases_notes_messages, phrase_notes, order)
            if not mix_phrases:  # jeśli zachowujemy oryginalną kolejność fraz to odczytujemy eventy w pierwotnej kolejności i budujemy melodię na podstawie oryginalnej melodii
                fake_notes, line_notes_messages = self.read_notes_from_track(self.midi_file.tracks[track_number])
                line_melody_track = self.build_new_melody_track_from_original(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            else:  # jak mieszamy kolejność fraz to budujemy melodię z wymieszanych eventów midi
                line_melody_track = self.build_new_melody_track(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            # plot(line_notes, line_path)  # sumaryczny wykres dla złożonych w całość fraz
            # utworzenie pliku wynikowego przez podmianę ścieżek
            self.midi_file.tracks[track_number] = line_melody_track
            tracks_data.append({'track_number': track_number, 'line_path': line_path, 'line_notes': line_notes, 'line_melody_track': line_melody_track})

        # self.midi_file.save("./data/result.mid")
        # prepare_and_play("./data/result.mid")
        return [self.midi_file, tracks_data]

    def build_new_melody_track_from_original(self, melody_track: MidiTrack, path: list, notes_messages: list):
        path_counter = 0
        for i, msg in enumerate(melody_track):
            if msg.type == 'note_on' and (path_counter < len(path)):
                new_on_msg = notes_messages[path[path_counter]][0]
                new_off_msg = notes_messages[path[path_counter]][1]
                if self.keep_old_timing:
                    melody_track[i] = Message('note_on', channel=msg.channel, note=new_on_msg.note, velocity=new_on_msg.velocity, time=msg.time)
                    melody_track[i + 1] = Message('note_off', channel=msg.channel, note=new_off_msg.note, velocity=new_off_msg.velocity,time=melody_track[i + 1].time)
                else:
                    melody_track[i] = Message('note_on', channel=msg.channel, note=new_on_msg.note, velocity=new_on_msg.velocity, time=self.quantizeRound(new_on_msg.time))
                    melody_track[i + 1] = Message('note_off', channel=msg.channel, note=new_off_msg.note, velocity=new_off_msg.velocity, time=self.quantizeRound(new_off_msg.time))
                path_counter += 1
        return melody_track

    def build_new_melody_track(self, melody_track: MidiTrack, path: list, notes_messages: list):
        path_counter = 0
        result_msg_sequence = []
        time_counter = 0
        time_values = []
        for i, msg in enumerate(notes_messages):
            old_on_msg = msg[0]
            old_off_msg = msg[1]
            if path_counter < len(path):
                new_on_msg = notes_messages[path[path_counter]][0]
                new_off_msg = notes_messages[path[path_counter]][1]
                if self.keep_old_timing:
                    result_msg_sequence.append(Message('note_on', channel=old_on_msg.channel, note=new_on_msg.note, velocity=new_on_msg.velocity, time=old_on_msg.time))
                    result_msg_sequence.append(Message('note_off', channel=old_off_msg.channel, note=new_off_msg.note, velocity=new_off_msg.velocity, time=old_off_msg.time))
                else:
                    result_msg_sequence.append(Message('note_on', channel=old_on_msg.channel, note=new_on_msg.note, velocity=new_on_msg.velocity, time=self.quantizeRound(new_on_msg.time)))
                    # result_msg_sequence.append(Message('note_on', channel=old_on_msg.channel, note=new_on_msg.note, velocity=new_on_msg.velocity, time=new_on_msg.time))
                    time_counter += new_on_msg.time
                    time_values.append(new_on_msg.time)
                    result_msg_sequence.append(Message('note_off', channel=old_off_msg.channel, note=new_off_msg.note, velocity=new_off_msg.velocity, time=self.quantizeRound(new_off_msg.time)))
                    # result_msg_sequence.append(Message('note_on', channel=old_off_msg.channel, note=new_off_msg.note, velocity=new_off_msg.velocity, time=new_off_msg.time))
                    time_counter += new_off_msg.time
                    time_values.append(new_off_msg.time)
                path_counter += 1
        # if not self.keep_old_timing:
        #     result_msg_sequence = self.quantize_track(result_msg_sequence, time_values, time_counter)
        notes_messages_detected = False
        for i, msg in enumerate(melody_track):  # kopiowanie starych settings messegów do nowego tracka
            if msg.type != 'note_on' and msg.type != 'note_off' and not notes_messages_detected:
                result_msg_sequence.insert(i, msg)
            elif msg.type != 'note_on' and msg.type != 'note_off' and notes_messages_detected:
                result_msg_sequence.append(msg)
            elif msg.type == 'note_on':
                notes_messages_detected = True
        return MidiTrack(result_msg_sequence)

    def quantize_track(self, msg_sequence: list, time_list: list, time_counter: int):  # gra bardzo sztywno i robi pauzy
        # TODO trzeba unaturalnić czasy i dopasować sumaryczną długość do time_sum
        tact_length = self.clocks_per_click * self.midi_file.tracks[0][0].numerator * self.midi_file.tracks[0][0].denominator
        time_sum = sum(time_list)
        corrected_time_list = copy.deepcopy(time_list)
        for i, time_value in enumerate(corrected_time_list):
            corrected_time_list[i] = int(self.clocks_per_click * np.ceil(time_value / self.clocks_per_click))
            if corrected_time_list[i] == 0:
                corrected_time_list[i] = self.clocks_per_click
        corrected_time_list[0] = 0  # pierwsza nuta bez pauzy
        # corrected_time_list = [4 if i < 4 else i for i in corrected_time_list]  # najmnieje czasy to 4
        corrected_time_sum = sum(corrected_time_list)
        error = sum(corrected_time_list) - sum(time_list)
        last_tact_time = time_counter % tact_length
        time_to_add = tact_length - last_tact_time + error
        # while time_to_add != 0:
        for j, msg in enumerate(msg_sequence):
            msg_sequence[j].time = corrected_time_list[j]
        return msg_sequence

    def extend_unedited_paths(self, not_selected_paths: [int], track_length: int):  # zawiera też korekcję czasu
        tact_length = self.clocks_per_click * self.midi_file.tracks[0][0].numerator * self.midi_file.tracks[0][0].denominator
        for i in not_selected_paths:
            notes_end_index = 0
            notes_messages = []
            time_counter = 0
            for j, msg in enumerate(self.midi_file.tracks[i]):
                if msg.type == 'note_on' or msg.type == 'note_off':
                    notes_messages.append(msg)
                    time_counter += msg.time
                if msg.type != 'note_on' and msg.type != 'note_off' and len(notes_messages) > 0:
                    notes_end_index = j
                    break
            last_tact_time = time_counter % tact_length
            time_to_add = tact_length - last_tact_time
            expansion_part = copy.deepcopy(notes_messages)
            expansion_part[0].time += time_to_add  # dodanie brakującego czasu do pierwszego eventu kolejnego powtórzenia ścieżki
            expansion_part = expansion_part*(track_length-1)
            self.midi_file.tracks[i][notes_end_index:notes_end_index] = expansion_part  # wstawienie po oryginalnej ścieżce części rozszerzającej

    def start_divide_and_extend(self, split: int, track_length: int, not_selected_paths: [int], mix_phrases: bool):  # track_length określa liczbę fraz w finalnym utworze
        try:
            self.clocks_per_click = self.midi_file.tracks[0][0].clocks_per_click
        except AttributeError:
            print("Nie masz w pliku clocks_per_click!")
            raise
        tracks_data = []
        for track_number in self.tracks_numbers:
            line_notes, line_notes_messages = self.read_notes_from_track(self.midi_file.tracks[track_number])
            phrase_notes = np.array_split(line_notes, split)
            phrases_notes_messages = np.array_split(line_notes_messages, split)
            phrase_paths = []
            order = []
            for l in range(track_length):
                for i in range(split):
                    phrase_paths.append(self.get_new_aco_melody_for_instrument(phrase_notes[i]))
                    order.append(i+(l*split))
            phrase_notes = phrase_notes*track_length
            phrases_notes_messages = phrases_notes_messages*track_length
            random.shuffle(order)
            line_path, line_notes_messages, line_notes = self.ordered_phrases_to_single_path(phrase_paths, phrases_notes_messages, phrase_notes, order)
            if not mix_phrases:
                fake_notes, line_notes_messages = self.read_notes_from_track(self.midi_file.tracks[track_number])
                line_notes_messages = self.replicate_and_correct_time(line_notes_messages, track_length)
            # utworzenie ścieżki
            line_melody_track = self.build_new_melody_track(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            # # utworzenie pliku wynikowego przez podmianę ścieżek
            self.midi_file.tracks[track_number] = line_melody_track
            tracks_data.append({'track_number': track_number, 'line_path': line_path, 'line_notes': line_notes, 'line_melody_track': line_melody_track})
        self.extend_unedited_paths(not_selected_paths, track_length)
        # self.midi_file.save("./data/result.mid")
        # prepare_and_play("./data/result.mid")
        return [self.midi_file, tracks_data]


if __name__ == '__main__':
    # antsBand = AntsBand(midi_file=MidiFile('./data/theRockingAntDrums.mid', clip=True), tracks_numbers=[2, 3],
    #                     keep_old_timing=False, result_track_length=1, algorithm_type=0, ant_count=10, generations=10,
    #                     alpha=1.0, beta=5, rho=0.9, q=1, phi=0.1, q_zero=0.9, sigma=10.0)
    antsBand = AntsBand(midi_file=MidiFile('./data/theDreamingAnt.mid', clip=True), tracks_numbers=[2, 3],
                        keep_old_timing=True, result_track_length=1, algorithm_type=0, ant_count=10, generations=10,
                        alpha=1.0, beta=5, rho=0.9, q=1, phi=0.1, q_zero=0.9, sigma=10.0)
    # antsBand.start()
    # midi_result, tracks_data = antsBand.start_and_divide(4)
    # midi_result, tracks_data = antsBand.start_and_extend(3, [4])
    midi_result, tracks_data = antsBand.start()
    print("Eval result: ", evaluate_melody(midi_result, tracks_data[1]))
    calculate_similarity(midi_result, tracks_data[1], MidiFile('./data/theDreamingAnt.mid', clip=True))