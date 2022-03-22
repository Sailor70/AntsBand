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
    result_track = midi_result.tracks[track_number]
    all_notes = 0  # notes messages - liczba nut to all_notes/2
    similar_notes = 0
    similar_times = 0
    for i, msg in enumerate(midi_input.tracks[track_number]):  # iteruje po tracku wejściowym bo on może być krótszy
        if msg.type == 'note_on' or msg.type == 'note_off':
            all_notes += 1
            if msg.note == result_track[i].note:
                similar_notes += 1
            if msg.time == result_track[i].time:
                similar_times += 1
    print("similar notes", similar_notes)
    print("similar notes factor", str(similar_notes/all_notes))
    print("similar_times", similar_times)
    print("similar_times factor", str(similar_times/all_notes))
    print("all_notes", all_notes)
    return [similar_notes/all_notes, similar_times/all_notes]

def evaluate_melody(midi_result: MidiFile, track_data):
    clocks_per_click = midi_result.tracks[0][0].clocks_per_click
    numerator = midi_result.tracks[0][0].numerator
    denominator = midi_result.tracks[0][0].denominator
    notes_in_time_factor = calculate_notes_in_time(track_data, clocks_per_click, numerator, denominator)
    repeated_sequences_factor = check_notes_sequences_repetition(track_data)
    # base_notes_at_accents_factor = check_base_notes_at_accents(track_data, clocks_per_click, numerator, denominator)  # z tego chyba się zrezygnuje
    cosonance_dissonance_factor = check_cosonance_dissonance(track_data)
    print("cosonance_dissonance_factor: ", cosonance_dissonance_factor)  # <0,1>
    print("repeated_sequences_factor", repeated_sequences_factor)  # <0,1> zazwyczaj. czasem może być > 1
    print("notes_in_time_factor", notes_in_time_factor)  # <0,1>
    evaluation_result = 0.33 * notes_in_time_factor + 0.33 * repeated_sequences_factor + 0.33 * cosonance_dissonance_factor   # metoda ważonych kryteriów
    return evaluation_result

# liczy czy pomiędzy dźwiękami występuje kosonans, czy dysonans na podstawie interwałów
def check_cosonance_dissonance(track_data):
    notes = [track_data['line_notes'][track_data['line_path'][i]] for i in range(len(track_data['line_path']))]  # przenieść do evaluate_melody
    cosonance_intervals = [0, 3, 4, 5, 7, 8, 9, 12]  # konsonansy
    cosonances_counter = 0
    for i, prev_note in enumerate(notes, 1):
        interval = abs(prev_note-notes[i])
        if interval in cosonance_intervals:
            cosonances_counter += 1
        if i == len(notes)-1:
            break
    # print("cosonances_counter: ", cosonances_counter)
    return cosonances_counter/(len(notes)-1)

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
                if time_counter % (clocks_per_click * (numerator/2)) == 0:  # ósemka (nuta trafia w którąś z 1/8 taktu)
                # if time_counter % (clocks_per_click * numerator) == 0:  # ćwierćnuta
                    eval_notes_time[notes_counter] += 1
                notes_counter += 1
            if msg.type == 'control_change' and msg.time != 0:  # po ostatnim note off jest control_change wyłączający instrument i
                # posiadający brakujący time - po nim eventów już nie uwzględniamy
                break
    print("eval_notes_time: ", eval_notes_time)
    # print("notes_counter ", notes_counter)
    # print("len(tracks_data['line_path'])", len(tracks_data['line_path']))
    return sum(eval_notes_time) / (notes_counter*2)

def check_notes_sequences_repetition(track_data):  # mierzy powtarzalność sekwencji dźwięków w melodi
    notes = [track_data['line_notes'][track_data['line_path'][i]] for i in range(len(track_data['line_path']))]
    print(notes)
    phrase_occurances = 0
    max_phrase_occurances = 0
    minrun = 4   # minimalna długość szukanej frazy
    lendata = len(notes)
    for runlen in range(minrun, lendata // 2):  # iteruje po długościach paternu od 4 po połowy
        for i in range(0, lendata - runlen):  # sprawdza wszystkie pozycje dla frazy szukanej długości
            s1 = notes[i:i + runlen]
            j = i+runlen
            while j < lendata - runlen:  # znajduje wszystkie inne frazy za aktualnie szukaną
                s2 = notes[j:j+runlen]
                max_phrase_occurances += 1
                if s1 == s2:
                    # print(s1, " at ", j)
                    phrase_occurances += 1
                j += 1
    print("max_phrase_occurances: ", max_phrase_occurances)
    print("phrase_occurances: ", phrase_occurances)
    print("lendata: ", lendata)
    return phrase_occurances/max_phrase_occurances  # linia melodyczna złożona z dźwięków jednej wysokości (tych samych) ma factor 1
