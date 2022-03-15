import random
import string

import numpy as np
from mido import Message, MidiTrack
from mido import MidiFile
from aco import ACO, Graph
from acs import ACS, GraphACS
from midiPlayer import prepare_and_play
from AntsBandActions import plot, evaluate_melody, calculate_similarity


class AntsBand(object):
    def __init__(self, midi_file: MidiFile, tracks_numbers: [int], keep_old_timing: bool, result_track_length: int, algorithm_type: int,
                 ant_count: int, generations: int, alpha: float, beta: float, rho: float, q: int, phi: float, q_zero: float, sigma: float):
        self.midi_file = midi_file  # strings podawać i tworzyć objekt
        self.tracks_numbers = tracks_numbers  # tracksNumbers  # tablica + pętle do tego
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

    def msg2dict(self, msg):
        result = dict()
        # print(msg)
        if 'note_on' in msg:
            on_ = True
        elif 'note_off' in msg:
            on_ = False
        else:
            on_ = None
        result['time'] = int(msg[msg.rfind('time'):].split(' ')[0].split('=')[1].translate(
            str.maketrans({a: None for a in string.punctuation})))

        if on_ is not None:
            for k in ['channel', 'note', 'velocity']:
                result[k] = int(msg[msg.rfind(k):].split(' ')[0].split('=')[1].translate(
                    str.maketrans({a: None for a in string.punctuation})))
        return [result, on_]

    def read_notes_from_track(self, melody_track: MidiTrack):
        notes = []  # zawiera wysokości kolejno zagranych dźwięków w oryginalnej ścieżce
        notes_messages = []  # zawiera kolejne pełne eventy midi z oryginalnej ścieżki
        for event in range(len(melody_track)):  # przeanalizuj każdy event midi z ścieżki
            if isinstance(melody_track[event],
                          Message):  # interesują nas tylko obiekty typu Message (MetaMessage nieistotne)
                message, on_ = self.msg2dict(str(melody_track[event]))
                if on_:
                    notes.append(message['note'])
                    notes_messages.append(
                        [melody_track[event],
                         melody_track[event + 1]])  # zapisuje do tablicy eventy midi  # TODO poprawić
                    # dla tego dźwięku (zawsze para note_on i note_off)
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
            aco = ACO(self.ant_count, self.generations, self.alpha, self.beta, self.rho, self.Q, 2)
            # aco = ACO(10, 10, 1.0, 5, 0.9, 1, 2)
            # ACO(1, 1, 5.0, 0, 0.01, 1, 2) - ustawienie do odtworzenia orginalnego
            # utworu ( ale tylko gdy mrówka zaczenie w dobrym miejscu - w nucie początkowej ? - to zagra tak samo)
            # aco = ACO(10, 100, 1.0, 8.0, 0.5, 10, 2)
            graph = Graph(cost_matrix, rank, self.sigma)
            path, cost = aco.solve(graph)
            print('cost: {}, path: {}'.format(cost, path))
        else:
            acs = ACS(self.ant_count, self.generations, self.alpha, self.beta, self.rho, phi=self.phi, q_zero=self.q_zero)  # self.phi, self.q_zero
            graph = GraphACS(cost_matrix, rank, self.sigma)
            path, cost = acs.solve(graph)
            print('cost2: {}, path2: {}'.format(cost, path))
        # plot(notes, path)  # wykres
        return path


    def build_new_melody_track(self, melody_track: MidiTrack, path: list, notes_messages: list):
        path_counter = 0
        for event in range(len(melody_track)):
            # if isinstance(melodyTrack[event], Message):
            old_message, on_ = self.msg2dict(str(melody_track[event]))
            if on_ and (path_counter < len(path)):
                new_message, on_must_be = self.msg2dict(str(notes_messages[path[path_counter]][0]))  # weź tą nute do dicta
                # utwórz nowy message, ale daj odpowiedni czas - czasy trwania nut pozostają z oryginalnego utworu
                melody_track[event] = Message('note_on', channel=old_message['channel'], note=new_message['note'], velocity=new_message['velocity'], time=old_message['time'])\
                    if self.keep_old_timing \
                    else Message('note_on', channel=old_message['channel'], note=new_message['note'], velocity=new_message['velocity'], time=self.quantizeRound(new_message['time']))
                # utworzenie pauzy starej długości ale nuty nowej wysokości
                old_off_message, off_ = self.msg2dict(str(melody_track[
                                                            event + 1]))  # TODO zabezpieczenie gdy nie ma note_off zaraz po note_on lub są w innej kolejności
                new_off_message, off = self.msg2dict(str(notes_messages[path[path_counter]][1]))
                melody_track[event + 1] = Message('note_off', channel=old_off_message['channel'], note=new_off_message['note'], velocity=new_off_message['velocity'], time=old_off_message['time'])\
                    if self.keep_old_timing\
                    else Message('note_off', channel=old_off_message['channel'], note=new_off_message['note'], velocity=new_off_message['velocity'], time=self.quantizeRound(new_off_message['time']))
                path_counter += 1
        return melody_track


    def quantizeRound(self, value):
        # print(self.clocks_per_click)
        # print(value, " -> ", self.clocks_per_click * round(value / self.clocks_per_click))
        # jakaś reguła że jak value < 16 to nie daje 0, ale wtedy dalsza część się rozjedzie
        # if value < 8:
        #     return int(4 * round(value / 4))
        # else:
        # TODO poprawiona kwantyzacja
        return int(self.clocks_per_click * round(value / self.clocks_per_click))  # przy tym tracimy krótkie dźwięki

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
            # plot(line_notes, line_path)
            # utworzenie nowej ścieżki dla instrumentu
            line_melody_track = self.build_new_melody_track(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            # utworzenie pliku wynikowego przez podmianę ścieżek
            self.midi_file.tracks[track_number] = line_melody_track
            tracks_data.append({'track_number': track_number, 'line_path': line_path, 'line_notes': line_notes, 'line_melody_track': line_melody_track})

        # self.midi_file.save("data/result.mid")
        # prepare_and_play("data/result.mid")
        return [self.midi_file, tracks_data]

    def start_and_extend(self, track_length: int, not_selected_paths: [int]):
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
            line_path = []
            for l in range(track_length):
                line_path.extend(self.get_new_aco_melody_for_instrument(line_notes))  # TODO line_notes i line_notes_messages rozszerzyć i build_new_melody_track_extend
            # plot(line_notes, line_path)
            # utworzenie nowej ścieżki dla instrumentu
            line_melody_track = self.build_new_melody_track(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            # utworzenie pliku wynikowego przez podmianę ścieżek
            self.midi_file.tracks[track_number] = line_melody_track
            tracks_data.append({'track_number': track_number, 'line_path': line_path, 'line_notes': line_notes, 'line_melody_track': line_melody_track})

        # self.midi_file.save("data/result.mid")
        # prepare_and_play("data/result.mid")
        return [self.midi_file, tracks_data]

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

    def start_and_divide(self, split: int):
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
            # plot(line_notes, line_path)  # sumaryczny wykres dla złożonych w całość fraz
            # utworzenie ścieżki
            line_melody_track = self.build_new_melody_track(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            # TODO ta funkcja (up) bierze stare eventy z midi_file.track więc timing będzie ten sam co w pliku wejściowym
            # # utworzenie pliku wynikowego przez podmianę ścieżek
            self.midi_file.tracks[track_number] = line_melody_track
            tracks_data.append({'track_number': track_number, 'line_path': line_path, 'line_notes': line_notes, 'line_melody_track': line_melody_track})

        self.midi_file.save("data/result.mid")
        # prepare_and_play("data/result.mid")
        return [self.midi_file, tracks_data]

    def build_new_melody_track_extend(self, melody_track: MidiTrack, path: list, notes_messages: list):
        path_counter = 0
        result_msg_sequence = []
        for i, msg in enumerate(notes_messages):  # old message to msg
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
                    result_msg_sequence.append(Message('note_on', channel=old_off_msg.channel, note=new_off_msg.note, velocity=new_off_msg.velocity, time=self.quantizeRound(new_off_msg.time)))
                path_counter += 1
        # TODO przy podwajaniu długości tracka trzeba doliczyć pomiędzy czas z końcowych meta messegów
        notes_messages_detected = False
        for i, msg in enumerate(melody_track):  # kopiowanie starych settings messegów do nowego tracka
            if msg.type != 'note_on' and msg.type != 'note_off' and not notes_messages_detected:
                result_msg_sequence.insert(i, msg)
            elif msg.type != 'note_on' and msg.type != 'note_off' and notes_messages_detected:
                result_msg_sequence.append(msg)
            elif msg.type == 'note_on':
                notes_messages_detected = True
        return MidiTrack(result_msg_sequence)

    def extend_unedited_paths(self, not_selected_paths: [int]):
        print("not_selected_paths", not_selected_paths)
        for i in not_selected_paths:
            notes_end_index = 0
            notes_messages = []
            for j, msg in enumerate(self.midi_file.tracks[i]):
                if msg.type == 'note_on' or msg.type == 'note_off':
                    notes_messages.append(msg)
                if msg.type != 'note_on' and msg.type != 'note_off' and len(notes_messages) > 0:
                    notes_end_index = j
                    break
            self.midi_file.tracks[i][notes_end_index:notes_end_index] = notes_messages


    def start_divide_and_extend(self, split: int, track_length: int, not_selected_paths: [int]):  # track_length określa liczbę fraz w finalnym utworze
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
                    phrase_paths.append(self.get_new_aco_melody_for_instrument(phrase_notes[i]))  # tworzy 8 różnych ścieżek ale później
                    order.append(i)  # jak track_length = 2 a split=4, to order będzie miał 8 elementów ale o wartości 0-4 TODO i+(l*split)
            random.shuffle(order)  # losowanie kolejności tablic - może mrówkami?
            line_path, line_notes_messages, line_notes = self.ordered_phrases_to_single_path(phrase_paths, phrases_notes_messages, phrase_notes, order)
            # plot(line_notes, line_path)  # sumaryczny wykres dla złożonych w całość fraz
            # utworzenie ścieżki
            line_melody_track = self.build_new_melody_track_extend(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            # # utworzenie pliku wynikowego przez podmianę ścieżek
            self.midi_file.tracks[track_number] = line_melody_track
            tracks_data.append({'track_number': track_number, 'line_path': line_path, 'line_notes': line_notes, 'line_melody_track': line_melody_track})
        self.extend_unedited_paths(not_selected_paths)
        self.midi_file.save("data/result.mid")
        # prepare_and_play("data/result.mid")
        return [self.midi_file, tracks_data]


if __name__ == '__main__':
    antsBand = AntsBand(midi_file=MidiFile('data/theRockingAntDrums.mid', clip=True), tracks_numbers=[2, 3],
                        keep_old_timing=True, result_track_length=1, algorithm_type=0, ant_count=10, generations=10,
                        alpha=1.0, beta=5, rho=0.9, q=1, phi=0.1, q_zero=0.9, sigma=10.0)
    # antsBand.start()
    midi_result, tracks_data = antsBand.start_and_divide(4)
    # midi_result, tracks_data = antsBand.start_divide_and_extend(4, 2, [4])
    # midi_result, tracks_data = antsBand.start()
    print(evaluate_melody(midi_result, tracks_data[1]))
    calculate_similarity(midi_result, tracks_data[1], MidiFile('data/theRockingAntDrums.mid', clip=True))
