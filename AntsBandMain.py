import random
import string

from mido import Message, MidiTrack
from mido import MidiFile
from aco import ACO, Graph
from midiPlayer import prepare_and_play
from plot import plot


class AntsBand(object):
    def __init__(self, midiFile: MidiFile, tracksNumbers: [int]):
        self.midiFile = midiFile  # strings podawać i tworzyć objekt
        self.tracksNumbers = tracksNumbers  # tracksNumbers  # tablica + pętle do tego
        self.availableDistances = [0.1, 0.5, 1, 5, 10, 100]
        # self.Q = q
        # self.rho = rho
        # self.beta = beta
        # self.alpha = alpha
        # self.ant_count = ant_count
        # self.generations = generations

    def distance(self, a: int, b: int):
        result = abs(a - b)
        if result == 0:
            return self.availableDistances[random.randint(4, 5)]  # availableDistances[random.randint(3, 5)]
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

    def readNotesFromTrack(self, melodyTrack: MidiTrack):  # TODO od razu cięcie na frazy tu zrobić?
        notes = []  # zawiera wysokości kolejno zagranych dźwięków w oryginalnej ścieżce
        notesMessages = []  # zawiera kolejne pełne eventy midi z oryginalnej ścieżki
        for event in range(len(melodyTrack)):  # przeanalizuj każdy event midi z ścieżki
            if isinstance(melodyTrack[event],
                          Message):  # interesują nas tylko obiekty typu Message (MetaMessage nieistotne)
                message, on_ = self.msg2dict(str(melodyTrack[event]))
                if on_:
                    notes.append(message['note'])
                    notesMessages.append(
                        [melodyTrack[event],
                         melodyTrack[event + 1]])  # zapisuje do tablicy eventy midi  # TODO poprawić
                    # dla tego dźwięku (zawsze para note_on i note_off)
        return [notes, notesMessages]

    def getNewACOMelodyForInstrument(self, notes: list):
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

    def buildNewMelodyTrack(self, melodyTrack: MidiTrack, path: list, notesMessages: list):
        pathCounter = 0
        for event in range(len(melodyTrack)):
            # if isinstance(melodyTrack[event], Message):
            oldMessage, on_ = self.msg2dict(str(melodyTrack[event]))
            if on_ and (pathCounter < len(path)):
                newMessage, on_must_be = self.msg2dict(str(notesMessages[path[pathCounter]][0]))  # weź tą nute do dicta
                # utwórz nowy message, ale daj odpowiedni czas - czasy trwania nut pozostają z oryginalnego utworu
                melodyTrack[event] = Message('note_on', channel=oldMessage['channel'], note=newMessage['note'],
                                             velocity=newMessage['velocity'], time=oldMessage['time'])
                # utworzenie pauzy starej długości ale nuty nowej wysokości
                oldOffMessage, off_ = self.msg2dict(str(melodyTrack[
                                                            event + 1]))  # TODO zabezpieczenie gdy nie ma note_off zaraz po note_on lub są w innej kolejności
                newOffMessage, off = self.msg2dict(str(notesMessages[path[pathCounter]][1]))
                melodyTrack[event + 1] = Message('note_off', channel=oldOffMessage['channel'],
                                                 note=newOffMessage['note'],
                                                 velocity=newOffMessage['velocity'], time=oldOffMessage['time'])
                pathCounter += 1
        return melodyTrack

    def line_notes_messages_to_phrases(self, line_notes_messages: list, ticksPerPhrase: int):
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
                if phrase_counter >= ticksPerPhrase:  # TODO cięcie w połowie duetu - co zrobić?
                    print("phrase counter: ", phrase_counter)
                    phrases.append(phrase_notes_messages)
                    phrase_notes_messages = []
                    phrase_counter = 0
            phrase_notes_messages.append(event_duo)
        return phrases

    def start(self):
        print(self.midiFile.tracks[0][0])
        print("Ticks per bit: ", self.midiFile.ticks_per_beat)  # jeden bit to 96 tickow
        msg = str(self.midiFile.tracks[0][0])
        meter = int(msg[msg.rfind('numerator'):].split(' ')[0].split('=')[1][0])
        print("meter: ", meter)
        tactsInPhrase = 2
        ticksPerPhrase = self.midiFile.ticks_per_beat * meter * tactsInPhrase
        print("Ticks per phrase: ", ticksPerPhrase)

        for trackNumber in self.tracksNumbers:
            # odczyt nut i eventów midi ze ścieżek
            lineNotes, lineNotesMessages = self.readNotesFromTrack(self.midiFile.tracks[trackNumber])
            # print(self.midiFile.tracks[trackNumber])
            # Cięcie na frazy
            phrases_notes_messages = self.line_notes_messages_to_phrases(lineNotesMessages, ticksPerPhrase)
            # print(phrases_notes_messages)

            # ACO dla lini melodycznych
            linePath = self.getNewACOMelodyForInstrument(lineNotes)
            # utworzenie nowej ścieżki dla instrumentu
            lineMelodyTrack = self.buildNewMelodyTrack(self.midiFile.tracks[trackNumber], linePath, lineNotesMessages)
            # utworzenie pliku wynikowego przez podmianę ścieżek
            self.midiFile.tracks[trackNumber] = lineMelodyTrack

        self.midiFile.save("data/result.mid")
        # prepare_and_play("data/result.mid")



if __name__ == '__main__':
    antsBand = AntsBand(MidiFile('data/theRockingAnt.mid', clip=True), [2, 3])
    antsBand.start()
