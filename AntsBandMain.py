import random
import string

from mido import Message, MidiTrack
from mido import MidiFile
from aco import ACO, Graph
from midiPlayer import prepare_and_play
from plot import plot

# randomizacja dystansu tych samych dźwięków (ale to przekłamanie)
availableDistances = [0.1, 0.5, 1, 5, 10, 100]

def distance(a: int, b: int):
    result = abs(a-b)
    if result == 0:
        return availableDistances[random.randint(4, 5)]  # availableDistances[random.randint(3, 5)]
    else:
        return result


def msg2dict(msg):
    result = dict()
    print(msg)
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


def readNotesFromTrack(melodyTrack: MidiTrack):
    notes = []  # zawiera wysokości kolejno zagranych dźwięków w oryginalnej ścieżce
    notesMessages = []  # zawiera kolejne pełne eventy midi z oryginalnej ścieżki
    for event in range(len(melodyTrack)):  # przeanalizuj każdy event midi z ścieżki
        if isinstance(melodyTrack[event], Message):  # interesują nas tylko obiekty typu Message (MetaMessage nieistotne)
            message, on_ = msg2dict(str(melodyTrack[event]))
            if on_:
                notes.append(message['note'])
                notesMessages.append([melodyTrack[event], melodyTrack[event+1]])  # zapisuje do tablicy eventy midi  # TODO poprawić
                # dla tego dźwięku (zawsze para note_on i note_off)
    return[notes, notesMessages]


def getNewACOMelodyForInstrument(notes: list):
    cost_matrix = []
    rank = len(notes)
    for i in range(rank):
        row = []
        for j in range(rank):
            row.append(distance(notes[i], notes[j]))
        cost_matrix.append(row)
    aco = ACO(10, 10, 5.0, 2, 0.1, 1, 2)  # ACO(1, 1, 5.0, 0, 0.01, 1, 2) - ustawienie do odtworzenia orginalnego
    # utworu ( ale tylko gdy mrówka zaczenie w dobrym miejscu - w nucie początkowej ? - to zagra tak samo)
    # aco = ACO(10, 100, 1.0, 8.0, 0.5, 10, 2)
    graph = Graph(cost_matrix, rank)
    path, cost = aco.solve(graph)
    print('cost: {}, path: {}'.format(cost, path))
    plot(notes, path)  # wykres
    return path


def buildNewMelodyTrack(melodyTrack: MidiTrack, path: list, notesMessages: list):
    pathCounter = 0
    for event in range(len(melodyTrack)):
        if isinstance(melodyTrack[event], Message):
            oldMessage, on_ = msg2dict(str(melodyTrack[event]))
            if on_:
                newMessage, on_must_be = msg2dict(str(notesMessages[path[pathCounter]][0]))  # weź tą nute do dicta
                # utwórz nowy message, ale daj odpowiedni czas
                melodyTrack[event] = Message('note_on', channel=newMessage['channel'], note=newMessage['note'], velocity=newMessage['velocity'], time=oldMessage['time'])
                melodyTrack[event+1] = notesMessages[path[pathCounter]][1]
                pathCounter += 1
    return melodyTrack


def main():
    midiFile = MidiFile('data/Am-melody+bas.mid', clip=True)  # TODO zrobić klase i to globalnie + dostęp przez self
    leadTrackNumber = 2
    basTrackNumber = 3

    # odczyt nut i eventów midi ze ścieżek
    leadNotes, leadNotesMessages = readNotesFromTrack(midiFile.tracks[leadTrackNumber])
    basNotes, basNotesMessages = readNotesFromTrack(midiFile.tracks[basTrackNumber])

    # ACO dla lini melodycznych
    leadPath = getNewACOMelodyForInstrument(leadNotes)
    basPath = getNewACOMelodyForInstrument(basNotes)

    # utworzenie nowych ścieżek dla instrumentów
    leadMelodyTrack = buildNewMelodyTrack(midiFile.tracks[leadTrackNumber], leadPath, leadNotesMessages)
    basMelodyTrack = buildNewMelodyTrack(midiFile.tracks[basTrackNumber], basPath, basNotesMessages)

    # utworzenie pliku wynikowego przez podmianę ścieżek
    midiFile.tracks[leadTrackNumber] = leadMelodyTrack
    midiFile.tracks[basTrackNumber] = basMelodyTrack
    midiFile.save("data/result.mid")
    prepare_and_play("data/result.mid")


if __name__ == '__main__':
    main()
