from __future__ import division

import random
import string

import numpy as np
from mido import Message, MidiTrack
from mido import MidiFile
from aco import ACO, Graph
from midiPlayer import prepare_and_play
from plot import plot


class AntsBand(object):
    def __init__(self, midi_file: MidiFile, tracks_numbers: [int], keep_old_timing: bool,
                 ant_count: int, generations: int, alpha: float, beta: float, rho: float, q: int):
        self.midi_file = midi_file  # strings podawać i tworzyć objekt
        self.tracks_numbers = tracks_numbers  # tracksNumbers  # tablica + pętle do tego
        self.available_distances = [0.1, 0.5, 1, 5, 10, 100]
        self.keep_old_timing = keep_old_timing
        self.Q = q
        self.rho = rho
        self.beta = beta
        self.alpha = alpha
        self.ant_count = ant_count
        self.generations = generations
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
        aco = ACO(self.ant_count, self.generations, self.alpha, self.beta, self.rho, self.Q, 2)
        # aco = ACO(10, 10, 1.0, 5, 0.1, 1, 2)
        # ACO(1, 1, 5.0, 0, 0.01, 1, 2) - ustawienie do odtworzenia orginalnego
        # utworu ( ale tylko gdy mrówka zaczenie w dobrym miejscu - w nucie początkowej ? - to zagra tak samo)
        # aco = ACO(10, 100, 1.0, 8.0, 0.5, 10, 2)
        graph = Graph(cost_matrix, rank)
        path, cost = aco.solve(graph)
        print('cost: {}, path: {}'.format(cost, path))
        plot(notes, path)  # wykres
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
        return int(self.clocks_per_click * round(value / self.clocks_per_click))  # przy tym tracimy krótkie dźwięki

    def start(self):
        self.clocks_per_click = self.midi_file.tracks[0][0].clocks_per_click
        for track_number in self.tracks_numbers:
            # odczyt nut i eventów midi ze ścieżek
            line_notes, line_notes_messages = self.read_notes_from_track(self.midi_file.tracks[track_number])
            # ACO dla lini melodycznych
            line_path = self.get_new_aco_melody_for_instrument(line_notes)
            # utworzenie nowej ścieżki dla instrumentu
            line_melody_track = self.build_new_melody_track(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            # utworzenie pliku wynikowego przez podmianę ścieżek
            self.midi_file.tracks[track_number] = line_melody_track

        self.midi_file.save("data/result.mid")
        # prepare_and_play("data/result.mid")

    def ordered_phrases_to_single_path(self, phrase_paths: list, phrases_notes_messages: list, order: [int]):
        line_path = []
        line_notes_messages = []
        for i in order:
            line_notes_messages.append(phrases_notes_messages[i])
            phrase_paths[i] = [x+i*len(phrase_paths[i]) for x in phrase_paths[i]]  # przemnożenie indeksów
            line_path.append(phrase_paths[i])
        line_path = [item for sublist in line_path for item in sublist]  # redukcja wymiaru tablicy z 3 na 2 wymiary
        line_notes_messages = [item for sublist in line_notes_messages for item in sublist]
        return [line_path, line_notes_messages]

    def start_and_divide(self, split: int):
        # print(self.midi_file.tracks[0][0])
        self.clocks_per_click = self.midi_file.tracks[0][0].clocks_per_click
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
            print(order)
            print(phrase_paths)
            line_path, line_notes_messages = self.ordered_phrases_to_single_path(phrase_paths, phrases_notes_messages, order)
            # utworzenie ścieżki
            line_melody_track = self.build_new_melody_track(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            # # utworzenie pliku wynikowego przez podmianę ścieżek
            self.midi_file.tracks[track_number] = line_melody_track

        self.midi_file.save("data/result.mid")
        # prepare_and_play("data/result.mid")


if __name__ == '__main__':
    antsBand = AntsBand(MidiFile('data/theRockingAntDrums.mid', clip=True), [2, 3], True, 10, 10, 1.0, 5, 0.1, 1)
    # antsBand.start()
    antsBand.start_and_divide(4)
