import matplotlib.pyplot as plt
from mido import MidiFile


def plot(points, path: list):
    x = []
    y = []
    # print(points)
    for i in range(len(points)):
        x.append(i)
        y.append(points[path[i]])

    plt.plot(x, y, 'co')
    plt.show()
    return plt


def delete_other_tracks(mid: MidiFile, track_number: int):
    reduced_mid = MidiFile()
    reduced_mid.type = mid.type
    reduced_mid.ticks_per_beat = mid.ticks_per_beat
    for i, track in enumerate(mid.tracks):
        if not (track[0].type == 'track_name' and i != track_number):
            reduced_mid.tracks.append(track)
    return reduced_mid


def evaluate_melody(midi_result: MidiFile, tracks_data, midi_input: MidiFile):
    # result = calculate_notes_in_time(midi_result, tracks_data)
    # result_from_oryginal = calculate_notes_from_midi_input(midi_input, tracks_data)
    # print("result", result)
    # print("result_from_oryginal", result_from_oryginal)
    # return result/result_from_oryginal  # TODO metoda kryterium globalnego

    clocks_per_click = midi_result.tracks[0][0].clocks_per_click
    numerator = midi_result.tracks[0][0].numerator
    denominator = midi_result.tracks[0][0].denominator
    eval_notes_time = [0] * len(tracks_data['line_path'])
    time_counter = 0
    notes_counter = 0
    # print(tracks_data['line_melody_track'])
    for i, msg in enumerate(tracks_data['line_melody_track']):
        if hasattr(msg, 'time'):  # 'note_on' or msg.type == 'note_off'
            time_counter += msg.time
            # print(msg.time)
            if msg.type == 'note_on':
                if time_counter % clocks_per_click == 0: # jeśli mieści się w siatce nut (trafia w szesnastkę) - ale może lepiej w ćwierćnutę i na raz w takcie
                    eval_notes_time[notes_counter] += 1
                if time_counter % (clocks_per_click*numerator*denominator) == 0:  # nuta na raz w takcie
                    eval_notes_time[notes_counter] += 10
                notes_counter += 1
            if msg.type == 'control_change' and msg.time != 0:  # po ostatnim note off jest control_change wyłączający instrument i
                # posiadający brakujący time - po nim eventów już nie uwzględniamy
                break
    print(eval_notes_time)
    print("notes_counter ", notes_counter)
    print("len(tracks_data['line_path'])", len(tracks_data['line_path']))
    return sum(eval_notes_time)/notes_counter


def calculate_notes_from_midi_input(midi_input, tracks_data):
    clocks_per_click = midi_input.tracks[0][0].clocks_per_click
    numerator = midi_input.tracks[0][0].numerator
    denominator = midi_input.tracks[0][0].denominator
    eval_notes_time = [0] * len(tracks_data['line_path'])
    time_counter = 0
    notes_counter = 0
    print(tracks_data['line_melody_track'])
    for i, msg in enumerate(midi_input.tracks[tracks_data['track_number']]):
        if msg.time != 0:  # 'note_on' or msg.type == 'note_off'
            time_counter += msg.time
            print(msg.time)
            if msg.type == 'note_on':
                if time_counter % clocks_per_click == 0: # jeśli mieści się w siatce nut (trafia w szesnastkę) - ale może lepiej w ćwierćnutę i na raz w takcie
                    eval_notes_time[notes_counter] += 1
                if time_counter % (clocks_per_click*numerator*denominator) == 0:  # nuta na raz w takcie
                    eval_notes_time[notes_counter] += 10
                notes_counter += 1
            if msg.type == 'control_change':  # po ostatnim note off jest control_change wyłączający instrument i
                # posiadający brakujący time - po nim eventów już nie uwzględniamy
                break
    print(eval_notes_time)
    print("notes_counter ", notes_counter)
    print("len(tracks_data['line_path'])", len(tracks_data['line_path']))

    return sum(eval_notes_time)/notes_counter


def calculate_notes_in_time(midi_result, tracks_data):
    clocks_per_click = midi_result.tracks[0][0].clocks_per_click
    numerator = midi_result.tracks[0][0].numerator
    denominator = midi_result.tracks[0][0].denominator
    eval_notes_time = [0] * len(tracks_data['line_path'])
    time_counter = 0
    notes_counter = 0
    print(tracks_data['line_melody_track'])
    for i, msg in enumerate(tracks_data['line_melody_track']):
        if msg.time != 0:  # 'note_on' or msg.type == 'note_off'  # TODO inny warunek potrzebny bo if msg.type == 'control_change' powoduje wyjście i błędy
            time_counter += msg.time
            print(msg.time)
            if msg.type == 'note_on':
                if time_counter % clocks_per_click == 0: # jeśli mieści się w siatce nut (trafia w szesnastkę) - ale może lepiej w ćwierćnutę i na raz w takcie
                    eval_notes_time[notes_counter] += 1
                if time_counter % (clocks_per_click*numerator*denominator) == 0:  # nuta na raz w takcie
                    eval_notes_time[notes_counter] += 10
                notes_counter += 1
            # if msg.type == 'control_change':  # po ostatnim note off jest control_change wyłączający instrument i
                # posiadający brakujący time - po nim eventów już nie uwzględniamy
                # break
    print(eval_notes_time)
    print("notes_counter ", notes_counter)
    print("len(tracks_data['line_path'])", len(tracks_data['line_path']))
    return sum(eval_notes_time)/notes_counter


class AntsBandActions(object):
    def __init__(self, midi_file: MidiFile, line_path, line_notes, line_melody_track):
        self.midi_file = midi_file

    def separate_track_and_save(self):
        return 0
