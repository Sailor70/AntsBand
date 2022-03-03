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

def calculate_similarity(midi_result: MidiFile, track_data, midi_input: MidiFile):
    track_number = track_data['track_number']
    input_track = midi_input.tracks[track_number]
    all_notes = 0  # notes messages - liczba nut to all_notes/2
    similar_notes = 0
    similar_times = 0
    for i, msg in enumerate(midi_result.tracks[track_number]):
        if msg.type == 'note_on' or msg.type == 'note_off':
            all_notes += 1
            if msg.note == input_track[i].note:
                similar_notes += 1
            if msg.time == input_track[i].time:
                similar_times += 1
    print("similar notes", similar_notes)
    print("similar notes factor", str(similar_notes/all_notes))
    print("similar_times", similar_times)
    print("all_notes", all_notes)
    return [similar_notes, similar_times]

def evaluate_melody(midi_result: MidiFile, track_data):
    clocks_per_click = midi_result.tracks[0][0].clocks_per_click
    numerator = midi_result.tracks[0][0].numerator
    denominator = midi_result.tracks[0][0].denominator
    notes_in_time_factor = calculate_notes_in_time(track_data, clocks_per_click, numerator, denominator)
    repeated_sequences_factor = check_notes_sequences_repetition(track_data)
    base_notes_at_accents_factor = check_base_notes_at_accents(track_data, clocks_per_click, numerator, denominator)
    print("repeated_sequences_factor", repeated_sequences_factor)
    print("base_notes_at_accents_factor", base_notes_at_accents_factor)
    evaluation_result = 1 * notes_in_time_factor + 0.4 * repeated_sequences_factor + 0.5 * base_notes_at_accents_factor  # metoda ważonych kryteriów
    return evaluation_result


def check_base_notes_at_accents(track_data, clocks_per_click, numerator, denominator):
    base_note_value = 41  # dźwięk F w pierwszej oktawie
    base_notes = [17, 29, 41, 53, 65, 77, 89]  # to trzeba jakoś wyliczać - są co 12
    time_counter = 0
    notes_counter = 0
    tact_time = clocks_per_click * numerator * denominator
    # print(track_data['line_melody_track'])
    for i, msg in enumerate(track_data['line_melody_track']):
        if hasattr(msg, 'time'):  # 'note_on' or msg.type == 'note_off'
            time_counter += msg.time
            if msg.type == 'note_on':
                if time_counter % tact_time == 0 and (msg.note in base_notes):
                    # jeśli nuta na raz i jest dźwiękiem bazowym
                    notes_counter += 1
                # tack_count = time_counter // tact_time  # w którym takcie jesteśmy
                # if (prev_msg.note in base_notes) and time_counter  # jeśli ostatnia nuta w takcie to bazowa
                # prev_msg = msg
    return notes_counter

def calculate_notes_in_time(track_data, clocks_per_click, numerator, denominator):
    eval_notes_time = [0] * len(track_data['line_path'])
    time_counter = 0
    notes_counter = 0
    # print(tracks_data['line_melody_track'])
    for i, msg in enumerate(track_data['line_melody_track']):
        if hasattr(msg, 'time'):  # 'note_on' or msg.type == 'note_off'
            time_counter += msg.time
            # print(msg.time)
            if msg.type == 'note_on':
                if time_counter % clocks_per_click == 0:  # jeśli mieści się w siatce nut (trafia w szesnastkę) - ale może lepiej w ćwierćnutę i na raz w takcie
                    eval_notes_time[notes_counter] += 1
                if time_counter % (clocks_per_click * numerator * denominator) == 0:  # nuta na raz w takcie
                    eval_notes_time[notes_counter] += 10
                notes_counter += 1
            if msg.type == 'control_change' and msg.time != 0:  # po ostatnim note off jest control_change wyłączający instrument i
                # posiadający brakujący time - po nim eventów już nie uwzględniamy
                break
    # print(eval_notes_time)
    # print("notes_counter ", notes_counter)
    # print("len(tracks_data['line_path'])", len(tracks_data['line_path']))
    return sum(eval_notes_time) / notes_counter

def check_notes_sequences_repetition(track_data):  # mierzy powtarzalność sekwencji dźwięków w melodi
    notes = [track_data['line_notes'][track_data['line_path'][i]] for i in range(len(track_data['line_path']))]
    print(notes)
    phrase_occurances = 1
    minrun = 4   # minimalna długość szukanej frazy
    lendata = len(notes)
    for runlen in range(minrun, lendata // 2):  # iteruje po długościach paternu od 3 po połowy
        i = 0
        for i in range(0, lendata - runlen):  # sprawdza wszystkie pozycje dla frazy szukanej długości
            s1 = notes[i:i + runlen]
            j = i+runlen
            while j < lendata - runlen:  # znajduje wszystkie inne frazy za aktualnie szukaną
                s2 = notes[j:j+runlen]
                if s1 == s2:
                    # print(s1, " at ", j)
                    phrase_occurances += 1  # może jakieś wagi wprowadzić dla fraz różnej długości?
                    j += runlen
                else:
                    j += 1
    return phrase_occurances
