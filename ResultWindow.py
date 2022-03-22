import random
from tkinter import *
from tkinter import filedialog
import threading
from pygame import mixer
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox

from AntsBandService import *


class ResultWindow:
    def __init__(self, master, midi_result: MidiFile, tracks_data, midi_input: MidiFile, execution_time: float):
        self.master = master
        master.title("Uzyskany wynik")
        master.geometry("500x600")
        mixer.init()  # initializing the mixer

        self.midi_result = midi_result
        self.tracks_data = tracks_data
        self.midi_base_input = midi_input
        self.execution_time = execution_time
        self.is_playing = False
        self.is_paused = False
        self.radio_var = IntVar()
        self.file_name = "result" + str(random.randint(0, 10000)) + ".mid"

        canvas = Canvas(master, width=500, height=600)
        canvas.grid(columnspan=3, rowspan=5)

        self.play_pause_btn = Button(master, text="Graj", command=lambda: self.play_pause(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.stop_btn = Button(master, text='Stop', command=lambda: self.stop_playing(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.save_btn = Button(master, text="Zapisz plik", command=lambda: self.save_file(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.sepatate_btn = Button(master, text='Odseparuj ścieżkę', command=lambda: self.separate_track(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.evaluation_value_label = Label(master, text="", font="Raleway")
        self.execution_time_label = Label(master, text="Czas: "+f"{self.execution_time:.3f} s", font="Raleway")
        self.similarity_label = Label(master, text="", font="Raleway")

        self.play_pause_btn.grid(row=0, column=0, sticky='n', pady=15)
        self.stop_btn.grid(row=0, column=1, sticky='n', pady=15)
        self.save_btn.grid(row=0, column=2, sticky='n', pady=15)
        self.sepatate_btn.grid(row=3, column=0, sticky='n')
        self.evaluation_value_label.grid(row=3, column=1, sticky='n')
        self.execution_time_label.grid(row=3, column=2, sticky='n')
        self.similarity_label.grid(row=4, column=0, columnspan=3, sticky='n')

        self.init_radio_buttons()
        self.print_plot()
        self.evaluate_melody()

    def print_plot(self):
        points = self.tracks_data[self.radio_var.get()]['line_notes']
        path = self.tracks_data[self.radio_var.get()]['line_path']
        x = []
        y = []
        for i in range(len(points)):
            x.append(i)
            y.append(points[path[i]])
        figure = plt.Figure(figsize=(5, 4), dpi=100)
        ax = figure.add_subplot(111)
        ax.scatter(x, y, color='g')
        scatter = FigureCanvasTkAgg(figure, self.master)
        scatter.get_tk_widget().grid(row=2, column=0, columnspan=3, sticky="enw")
        ax.legend(['Wartości kolejnych nut'])
        ax.set_xlabel('Czas')
        ax.set_title('Linia melodyczna instrumentu')

        # return messagebox.showinfo('PythonGuides', f'You Selected {output}.')

    def evaluate_melody(self):
        try:
            self.evaluation_value_label.config(text="Ocena: "+f"{evaluate_melody(self.midi_result, self.tracks_data[self.radio_var.get()]):.3f}")
            similar_notes_factor, similar_times_factor = calculate_similarity(self.midi_result, self.tracks_data[self.radio_var.get()], self.midi_base_input)
            self.similarity_label.config(text="Podobieństwo nut: "+f"{similar_notes_factor*100:.1f}%" + ", czasów: " + f"{similar_times_factor*100:.1f}%")
        except Exception as e:
            messagebox.showerror('Błąd', 'Wystąpił błąd: ' + str(e))
            raise  # pluje błędem do konsoli

    def init_radio_buttons(self):
        for i in range(len(self.tracks_data)):
            for msg in self.tracks_data[i]['line_melody_track']:
                if hasattr(msg, 'name'):
                    radio_btn = Radiobutton(self.master, text=msg.name, variable=self.radio_var, value=i, command=lambda:[self.print_plot(), self.evaluate_melody()])
                    radio_btn.grid(row=1, column=i, sticky='new')
                    break

    def refresh(self):
        self.master.update()
        self.master.after(1000, self.refresh)
        # if check_if_playing():
        if mixer.music.get_busy():
            self.is_playing = True
        else:
            self.play_pause_btn.config(text="Graj")
            self.is_playing = False

    def stop_playing(self):
        # stop_music()
        mixer.music.stop()
        self.play_pause_btn.config(text="Graj")
        self.is_playing = False
        self.is_paused = False

    def play_pause(self):
        self.midi_result.save("data/" + self.file_name)
        self.refresh()
        if not self.is_playing:
            if self.is_paused:
                # unpause_music()
                mixer.music.unpause()
                self.play_pause_btn.config(text="Pauza")
                self.is_paused = False
            else:
                self.play_pause_btn.config(text="Pauza")
                mixer.music.load("data/" + self.file_name)
                mixer.music.play()
                # threading.Thread(target=prepare_and_play("data/" + self.file_name)).start()
                self.is_playing = True
        else:
            # pause_music()
            # threading.Thread(target=pause_music()).start()
            mixer.music.pause()
            self.play_pause_btn.config(text="Graj")
            self.is_playing = False
            self.is_paused = True

    def save_file(self):
        path = filedialog.asksaveasfile(mode='w', title="Zapisz plik", defaultextension=".mid", filetypes=(("Midi file", "*.mid"),("All Files", "*.*")))
        self.midi_result.save(path.name)

    def separate_track(self):
        new_midi = delete_other_tracks(self.midi_result, self.tracks_data[self.radio_var.get()]['track_number'])
        path = filedialog.asksaveasfile(mode='w', title="Zapisz odseparowaną ścieżkę", defaultextension=".mid", filetypes=(("Midi file", "*.mid"),("All Files", "*.*")))
        new_midi.save(path.name)
        self.midi_result = new_midi
