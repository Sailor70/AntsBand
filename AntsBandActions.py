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


def delete_other_tracks(mid: MidiFile, track_number: int):
    print(mid)
    reduced_mid = MidiFile()
    reduced_mid.type = mid.type
    reduced_mid.ticks_per_beat = mid.ticks_per_beat
    print(reduced_mid)
    for i, track in enumerate(mid.tracks):
        if not (track[0].type == 'track_name' and i != track_number):
            reduced_mid.tracks.append(track)
    print(reduced_mid)
    return reduced_mid


class AntsBandActions(object):
    def __init__(self, midi_file: MidiFile, line_path, line_notes, line_melody_track):
        self.midi_file = midi_file

    def separate_track_and_save(self):
        return 0
