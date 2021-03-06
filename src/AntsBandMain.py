import copy
import random

import numpy as np
from mido import Message, MidiTrack
from mido import MidiFile

from AntColonySystem import ACS, GraphACS
from AntSystem import AntSystem, GraphAS


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
        try:
            self.ticks_per_beat = midi_file.ticks_per_beat
        except AttributeError:
            print('Nie masz w pliku ticks_per_beat!')
            raise
        self.ticks_per_semiquaver = self.ticks_per_beat / (16/midi_file.tracks[0][0].denominator)

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
            if msg.type == 'note_on' and msg.velocity != 0:  # interesują nas eventy włączające dźwięk
                notes.append(msg.note)
                j = i+1
                while True:  # do znalezienia eventu wyłączająecgo dźwięk
                    if melody_track[j].type == 'note_off' and melody_track[j].note == msg.note:
                        break  # standardowa forma note_on -> note_off
                    if melody_track[j].type == 'note_on' and melody_track[j].note == msg.note and melody_track[j].velocity == 0:
                        break  # nietypowa forma note_on -> note_on (velocity==0) w fishpolka
                    j += 1
                notes_messages.append([msg,melody_track[j]])
        return [notes, notes_messages]

    def get_new_aco_melody_for_instrument(self, notes: list):
        cost_matrix = []
        number_of_notes = len(notes)
        for i in range(number_of_notes):
            row = []
            for j in range(number_of_notes):
                row.append(self.distance(notes[i], notes[j]))
            cost_matrix.append(row)
        if self.algorithm_type == 0:
            aco = AntSystem(self.ant_count, self.generations, self.alpha, self.beta, self.rho, self.Q)
            graph = GraphAS(cost_matrix, number_of_notes, self.sigma)
            path, cost = aco.solve(graph)
        else:
            acs = ACS(self.ant_count, self.generations, self.alpha, self.beta, self.rho, phi=self.phi, q_zero=self.q_zero)
            graph = GraphACS(cost_matrix, number_of_notes, self.sigma)
            path, cost = acs.solve(graph)
        return [path, cost]

    def quantize_round(self, value):
        return int(self.ticks_per_semiquaver * round(value / self.ticks_per_semiquaver))

    def start(self):
        tracks_data = []
        cost = 0
        for track_number in self.tracks_numbers:
            # odczyt nut i eventów midi ze ścieżek
            line_notes, line_notes_messages = self.read_notes_from_track(self.midi_file.tracks[track_number])
            # ACO dla lini melodycznych
            line_path, cost = self.get_new_aco_melody_for_instrument(line_notes)
            # utworzenie nowej ścieżki dla instrumentu
            line_melody_track = self.build_new_melody_track_from_original(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            # utworzenie pliku wynikowego przez podmianę ścieżek
            self.midi_file.tracks[track_number] = line_melody_track
            tracks_data.append({'track_number': track_number, 'line_path': line_path, 'line_notes': line_notes, 'line_melody_track': line_melody_track})
        return [self.midi_file, tracks_data, cost]

    def start_and_extend(self, track_length: int, not_selected_paths: [int]):
        tracks_data = []
        for track_number in self.tracks_numbers:
            line_notes, line_notes_messages = self.read_notes_from_track(self.midi_file.tracks[track_number])
            line_path = []
            for l in range(track_length):
                line_path.extend(self.get_new_aco_melody_for_instrument(line_notes)[0])  # ścieżka składa się tylko z indeksów line_notes nierozszerzonego utworu
            line_notes = line_notes*track_length  # replikacja
            line_notes_messages = self.replicate_and_correct_time(line_notes_messages, track_length)
            line_melody_track = self.build_new_melody_track(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            self.midi_file.tracks[track_number] = line_melody_track
            tracks_data.append({'track_number': track_number, 'line_path': line_path, 'line_notes': line_notes, 'line_melody_track': line_melody_track})
        self.extend_unedited_paths(not_selected_paths, track_length)
        return [self.midi_file, tracks_data]

    def replicate_and_correct_time(self, line_notes_messages: list, track_length):
        tact_length = self.ticks_per_beat * self.midi_file.tracks[0][0].numerator
        time_counter = 0
        for i, msg in enumerate(line_notes_messages):  # obliczenie całkowitego czasu melodii
            time_counter += msg[0].time
            time_counter += msg[1].time
        last_tact_time = time_counter % tact_length  # taka wartość czasu brakuje w ostatnim takcie aby był pełny
        time_to_add = tact_length - last_tact_time  # taką wartość czasu należy dodać do kolejnej powtórzonej melodii
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
        tracks_data = []
        tracks_cost = []
        for track_number in self.tracks_numbers:
            line_notes, line_notes_messages = self.read_notes_from_track(self.midi_file.tracks[track_number])
            phrase_notes = np.array_split(line_notes, split)
            phrases_notes_messages = np.array_split(line_notes_messages, split)
            phrase_paths = []
            order = []
            total_cost = 0
            for i in range(split):
                path, cost = self.get_new_aco_melody_for_instrument(phrase_notes[i])
                phrase_paths.append(path)
                total_cost += cost
                order.append(i)
            tracks_cost.append(total_cost)
            random.shuffle(order)  # losowanie kolejności tablic
            line_path, line_notes_messages, line_notes = self.ordered_phrases_to_single_path(phrase_paths, phrases_notes_messages, phrase_notes, order)
            if not mix_phrases:  # jeśli zachowujemy oryginalną kolejność fraz to odczytujemy eventy w pierwotnej kolejności i budujemy melodię na podstawie oryginalnej melodii
                fake_notes, line_notes_messages = self.read_notes_from_track(self.midi_file.tracks[track_number])
                line_melody_track = self.build_new_melody_track_from_original(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            else:  # jak mieszamy kolejność fraz to budujemy melodię z wymieszanych eventów midi
                line_melody_track = self.build_new_melody_track(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            self.midi_file.tracks[track_number] = line_melody_track
            tracks_data.append({'track_number': track_number, 'line_path': line_path, 'line_notes': line_notes, 'line_melody_track': line_melody_track})
        return [self.midi_file, tracks_data, tracks_cost]

    def build_new_melody_track_from_original(self, melody_track: MidiTrack, path: list, notes_messages: list):
        path_counter = 0
        for i, msg in enumerate(melody_track):
            if msg.type == 'note_on' and msg.velocity != 0 and (path_counter < len(path)):
                new_on_msg = notes_messages[path[path_counter]][0]
                new_off_msg = notes_messages[path[path_counter]][1]
                if self.keep_old_timing:
                    melody_track[i] = Message('note_on', channel=msg.channel, note=new_on_msg.note, velocity=new_on_msg.velocity, time=msg.time)
                    melody_track[i + 1] = Message('note_off', channel=msg.channel, note=new_off_msg.note, velocity=new_off_msg.velocity,time=melody_track[i + 1].time)
                else:
                    melody_track[i] = Message('note_on', channel=msg.channel, note=new_on_msg.note, velocity=new_on_msg.velocity, time=self.quantize_round(new_on_msg.time))
                    melody_track[i + 1] = Message('note_off', channel=msg.channel, note=new_off_msg.note, velocity=new_off_msg.velocity, time=self.quantize_round(new_off_msg.time))
                path_counter += 1
        return melody_track

    def build_new_melody_track(self, melody_track: MidiTrack, path: list, notes_messages: list):
        path_counter = 0
        result_msg_sequence = []
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
                    result_msg_sequence.append(Message('note_on', channel=old_on_msg.channel, note=new_on_msg.note, velocity=new_on_msg.velocity, time=self.quantize_round(new_on_msg.time)))
                    result_msg_sequence.append(Message('note_off', channel=old_off_msg.channel, note=new_off_msg.note, velocity=new_off_msg.velocity, time=self.quantize_round(new_off_msg.time)))
                path_counter += 1
        notes_messages_detected = False
        for i, msg in enumerate(melody_track):  # kopiowanie starych settings messegów do nowego tracka
            if msg.type != 'note_on' and msg.type != 'note_off' and not notes_messages_detected:
                result_msg_sequence.insert(i, msg)
            elif msg.type != 'note_on' and msg.type != 'note_off' and notes_messages_detected:
                result_msg_sequence.append(msg)
            elif msg.type == 'note_on':
                notes_messages_detected = True
        return MidiTrack(result_msg_sequence)

    def extend_unedited_paths(self, not_selected_paths: [int], track_length: int):  # zawiera też korekcję czasu
        tact_length = self.ticks_per_beat * self.midi_file.tracks[0][0].numerator
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
        tracks_data = []
        for track_number in self.tracks_numbers:
            line_notes, line_notes_messages = self.read_notes_from_track(self.midi_file.tracks[track_number])
            phrase_notes = np.array_split(line_notes, split)
            phrases_notes_messages = np.array_split(line_notes_messages, split)
            phrase_paths = []
            order = []
            for l in range(track_length):
                for i in range(split):
                    phrase_paths.append(self.get_new_aco_melody_for_instrument(phrase_notes[i])[0])
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
        return [self.midi_file, tracks_data]
