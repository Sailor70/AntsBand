import random
import string

from mido import Message, MidiTrack
from mido import MidiFile
from aco import ACO, Graph
from midiPlayer import prepare_and_play
from plot import plot


class AntsBand(object):
    def __init__(self, midi_file: MidiFile, tracks_numbers: [int]):
        self.midi_file = midi_file  # strings podawać i tworzyć objekt
        self.tracks_numbers = tracks_numbers  # tracksNumbers  # tablica + pętle do tego
        self.available_distances = [0.1, 0.5, 1, 5, 10, 100]
        # self.Q = q
        # self.rho = rho
        # self.beta = beta
        # self.alpha = alpha
        # self.ant_count = ant_count
        # self.generations = generations

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

    def read_notes_from_track(self, melody_track: MidiTrack):  # TODO od razu cięcie na frazy tu zrobić?
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
        aco = ACO(10, 10, 1.0, 5, 0.1, 1, 2)
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
                melody_track[event] = Message('note_on', channel=old_message['channel'], note=new_message['note'],
                                              velocity=new_message['velocity'], time=old_message['time'])
                # utworzenie pauzy starej długości ale nuty nowej wysokości
                old_off_message, off_ = self.msg2dict(str(melody_track[
                                                            event + 1]))  # TODO zabezpieczenie gdy nie ma note_off zaraz po note_on lub są w innej kolejności
                new_off_message, off = self.msg2dict(str(notes_messages[path[path_counter]][1]))
                melody_track[event + 1] = Message('note_off', channel=old_off_message['channel'],
                                                  note=new_off_message['note'],
                                                  velocity=new_off_message['velocity'], time=old_off_message['time'])
                path_counter += 1
        return melody_track

    def line_notes_messages_to_phrases(self, line_notes_messages: list, ticks_per_phrase: int):
        phrases = []
        phrase_notes_messages = []
        phrase_counter = 0
        for message in line_notes_messages:  # jedzie po duetach
            event_duo = []
            for event in message:  # tutaj wejście do pary note_on i note_off - event_duo
                message, on_ = self.msg2dict(str(event))
                # print(message['time'])
                phrase_counter += message['time']
                event_duo.append(event)
                # print(phrase_counter)
                if phrase_counter >= ticks_per_phrase:  # TODO cięcie w połowie duetu - co zrobić? + jak jedna pauza w aktualnej i kolejnej frazie to za dużo nalicza
                    print("phrase counter: ", phrase_counter)
                    phrases.append(phrase_notes_messages)
                    phrase_notes_messages = []
                    phrase_counter = 0
            phrase_notes_messages.append(event_duo)
        return phrases

    def start(self):
        print(self.midi_file.tracks[0][0])
        print("Ticks per bit: ", self.midi_file.ticks_per_beat)  # jeden bit to 96 tickow
        msg = str(self.midi_file.tracks[0][0])
        meter = int(msg[msg.rfind('numerator'):].split(' ')[0].split('=')[1][0])
        print("meter: ", meter)
        tacts_in_phrase = 2
        ticks_per_phrase = self.midi_file.ticks_per_beat * meter * tacts_in_phrase
        print("Ticks per phrase: ", ticks_per_phrase)

        for track_number in self.tracks_numbers:
            # odczyt nut i eventów midi ze ścieżek
            line_notes, line_notes_messages = self.read_notes_from_track(self.midi_file.tracks[track_number])
            # print(self.midi_file.tracks[track_number])
            # Cięcie na frazy
            phrases_notes_messages = self.line_notes_messages_to_phrases(line_notes_messages, ticks_per_phrase)
            # print(phrases_notes_messages)

            # ACO dla lini melodycznych
            line_path = self.get_new_aco_melody_for_instrument(line_notes)
            # utworzenie nowej ścieżki dla instrumentu
            line_melody_track = self.build_new_melody_track(self.midi_file.tracks[track_number], line_path, line_notes_messages)
            # utworzenie pliku wynikowego przez podmianę ścieżek
            self.midi_file.tracks[track_number] = line_melody_track

        self.midi_file.save("data/result.mid")
        prepare_and_play("data/result.mid")



if __name__ == '__main__':
    antsBand = AntsBand(MidiFile('data/theRockingAnt.mid', clip=True), [2, 3])
    antsBand.start()
