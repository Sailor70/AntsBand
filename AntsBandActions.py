import matplotlib.pyplot as plt
from mido import MidiFile


def plot(points, path: list):
    x = []
    y = []
    print(points)
    for i in range(len(points)):
        x.append(i)
        y.append(points[path[i]])

    plt.plot(x, y, 'co')
    plt.show()
    return plt


class AntsBandActions(object):
    def __init__(self, midi_file: MidiFile, line_path, line_notes, line_melody_track):
        self.midi_file = midi_file

    def separate_track_and_save(self):
        return 0
