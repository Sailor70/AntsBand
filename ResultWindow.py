from tkinter import *
from tkinter import filedialog
import threading

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from AntsBandActions import *
from midiPlayer import *


class ResultWindow:
    def __init__(self, master, midi_result: MidiFile, tracks_data, midi_input: MidiFile):
        self.master = master
        master.title("Uzyskany wynik")
        master.geometry("500x600")

        self.midi_result = midi_result
        self.tracks_data = tracks_data
        self.midi_base_input = midi_input
        self.is_playing = False
        self.is_paused = False
        self.radio_var = IntVar()

        canvas = Canvas(master, width=500, height=600)
        canvas.grid(columnspan=3, rowspan=4)

        self.play_pause_btn = Button(master, text="Graj", command=lambda: self.play_pause(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.stop_btn = Button(master, text='Stop', command=lambda: self.stop_playing(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.save_btn = Button(master, text="Zapisz plik", command=lambda: self.save_file(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.sepatate_btn = Button(master, text='Odseparuj ścieżkę', command=lambda: self.separate_track(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.evaluation_value_label = Label(master, text="", font="Raleway")

        self.play_pause_btn.grid(row=0, column=0, sticky='n', pady=15)
        self.stop_btn.grid(row=0, column=1, sticky='n', pady=15)
        self.save_btn.grid(row=0, column=2, sticky='n', pady=15)
        self.sepatate_btn.grid(row=3, column=0, sticky='n')
        self.evaluation_value_label.grid(row=3, column=1, sticky='n')

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
        figure3 = plt.Figure(figsize=(5, 4), dpi=100)
        ax3 = figure3.add_subplot(111)
        ax3.scatter(x, y, color='g')
        scatter3 = FigureCanvasTkAgg(figure3, self.master)
        scatter3.get_tk_widget().grid(row=2, column=0, columnspan=3, sticky="enw")
        ax3.legend(['Wartości kolejnych nut'])
        ax3.set_xlabel('Czas')
        ax3.set_title('Linia melodyczna instrumentu')

        # return messagebox.showinfo('PythonGuides', f'You Selected {output}.')

    def evaluate_melody(self):
        self.evaluation_value_label.config(text="Ocena: "+f"{evaluate_melody(self.midi_result, self.tracks_data[self.radio_var.get()], self.midi_base_input):.1f}")

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
        if check_if_playing():
            self.is_playing = True
        else:
            self.play_pause_btn.config(text="Graj")
            self.is_playing = False

    def stop_playing(self):
        stop_music()
        self.play_pause_btn.config(text="Graj")
        self.is_playing = False
        self.is_paused = False

    def play_pause(self):
        self.midi_result.save("data/result.mid")
        self.refresh()
        if not self.is_playing:
            if self.is_paused:
                unpause_music()
                self.play_pause_btn.config(text="Pauza")
                self.is_paused = False
            else:
                self.play_pause_btn.config(text="Pauza")
                threading.Thread(target=prepare_and_play("data/result.mid")).start()
                self.is_playing = True
        else:
            # pause_music()
            threading.Thread(target=pause_music()).start()
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
