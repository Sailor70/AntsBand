import math
import random
import string

from mido import MidiFile
from mido import Message
from aco import ACO, Graph
from midiPlayer import prepare_and_play
from plot import plot


# randomizacja dystansu tych samych dźwięków (ale to przekłamanie)
availableDistances = [0.1, 0.5, 1, 5, 10, 100]

def distance(a: int, b: int):
    result = abs(a-b)
    if result == 0:
        return availableDistances[random.randint(4, 5)]
    else:
        return result


def msg2dict(msg):
    result = dict()
    if 'note_on' in msg:
        on_ = True
    elif 'note_off' in msg:
        on_ = False
    else:
        on_ = None
    result['time'] = int(msg[msg.rfind('time'):].split(' ')[0].split('=')[1].translate(
        str.maketrans({a: None for a in string.punctuation})))

    if on_ is not None:
        for k in ['note', 'velocity']:
            result[k] = int(msg[msg.rfind(k):].split(' ')[0].split('=')[1].translate(
                str.maketrans({a: None for a in string.punctuation})))
    return [result, on_]

def main():

    # mid = MidiFile('data/simple-Am-melody.mid', clip=True)
    mid = MidiFile('data/simple-Am-melody2.mid', clip=True)
    # mid = MidiFile('FishPolka.mid', clip=True)

    notes = []
    notesMessages = []
    melodyTrack = mid.tracks[2]
    # print(melodyTrack)
    for event in range(len(melodyTrack)):
        if isinstance(melodyTrack[event], Message):
            message, on_ = msg2dict(str(melodyTrack[event]))
            # if on_ is not None:
            #     notesMessages.append()
            if on_:
                notes.append(message['note'])
                notesMessages.append([melodyTrack[event], melodyTrack[event+1]])  # zapisuje do tablicy eventy midi
                # dla tego dźwięku (zawsze para note_on i note_off)

    cost_matrix = []

    rank = len(notes)
    for i in range(rank):
        row = []
        for j in range(rank):
            row.append(distance(notes[i], notes[j]))
        cost_matrix.append(row)
    aco = ACO(10, 100, 1.0, 8.0, 0.5, 10, 2)
    graph = Graph(cost_matrix, rank)
    path, cost = aco.solve(graph)
    print('cost: {}, path: {}'.format(cost, path))
    plot(notes, path)

    # buduje plik wynikowy
    pathCounter = 0
    for event in range(len(melodyTrack)):
        if isinstance(melodyTrack[event], Message):
            message, on_ = msg2dict(str(melodyTrack[event]))
            if on_:
                melodyTrack[event] = notesMessages[path[pathCounter]][0]
                melodyTrack[event+1] = notesMessages[path[pathCounter]][1]
                # print(notesMessages[path[pathCounter]][0])
                # print(notesMessages[path[pathCounter]][1])
                pathCounter += 1

    mid.tracks[2] = melodyTrack
    mid.save("data/samo_graj.mid")
    prepare_and_play("data/samo_graj.mid")


if __name__ == '__main__':
    main()
