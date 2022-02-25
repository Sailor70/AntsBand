# import tkinter as tk
from tkinter import *
from tkinter import tix, messagebox, filedialog
from tkinter.filedialog import askopenfile
import os
from tkinter.tix import Balloon
import threading

from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mido import MidiFile

from AntsBandActions import delete_other_tracks
from midiPlayer import *
from AntsBandMain import AntsBand


class ResultWindow:
    def __init__(self, master, midi_file: MidiFile, tracks_data):
        self.master = master
        master.title("Uzyskany wynik")
        master.geometry("500x600")

        self.midi_file = midi_file
        self.tracks_data = tracks_data
        self.is_playing = False
        self.is_paused = False
        self.radio_var = IntVar()

        canvas = Canvas(master, width=500, height=600)
        canvas.grid(columnspan=3, rowspan=4)

        self.play_pause_btn = Button(master, text="Graj", command=lambda: self.play_pause(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.stop_btn = Button(master, text='Stop', command=lambda: self.stop_playing(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.save_btn = Button(master, text="Zapisz plik", command=lambda: self.save_file(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.sepatate_btn = Button(master, text='Odseparuj ścieżkę', command=lambda: self.separate_track(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)

        self.play_pause_btn.grid(row=0, column=0, sticky='n', pady=15)
        self.stop_btn.grid(row=0, column=1, sticky='n', pady=15)
        self.save_btn.grid(row=0, column=2, sticky='n', pady=15)
        self.sepatate_btn.grid(row=3, column=0, sticky='n')

        self.init_radio_buttons()
        self.print_plot()

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

    def init_radio_buttons(self):
        for i in range(len(self.tracks_data)):
            for msg in self.tracks_data[i]['line_melody_track']:
                if hasattr(msg, 'name'):
                    radio_btn = Radiobutton(self.master, text=msg.name, variable=self.radio_var, value=i, command=self.print_plot)
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
        self.midi_file.save("data/result.mid")
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
        self.midi_file.save(path.name)

    def separate_track(self):
        new_midi = delete_other_tracks(self.midi_file, self.tracks_data[self.radio_var.get()]['track_number'])
        path = filedialog.asksaveasfile(mode='w', title="Zapisz odseparowaną ścieżkę", defaultextension=".mid", filetypes=(("Midi file", "*.mid"),("All Files", "*.*")))
        new_midi.save(path.name)
        self.midi_file = new_midi


class MainWindow:  # (Frame)

    def __init__(self, master):
        # super().__init__(master)
        self.master = master
        master.title("AntsBand 1.0")
        master.geometry("600x300")
        # master.resizable(False, False)

        # zmienne pomocnicze
        self.midi_file_name = ''
        self.paths_checkbox_dict = {}
        self.instruments = []
        self.keep_old_timing = BooleanVar()
        self.keep_old_timing.set(True)
        self.split_tracks = BooleanVar()
        self.split_tracks.set(False)

        canvas = Canvas(master, width=600, height=300)
        canvas.grid(columnspan=3, rowspan=6)

        """
        :param ant_count: liczba mrówek
        :param generations: liczba iteracji
        :param alpha: ważność feromonu
        :param beta: ważność informacji heurystycznej
        :param rho: współczynnik odparowania śladu feromonowego
        :param q: intensywność feromonu
        :param strategy: strategia aktualizacji śladu feromonowego. 0 - ant-cycle, 1 - ant-quality, 2 - ant-density
        """

        # definicje elementów layoutu
        self.file_label = Label(master, text="Wybierz pik midi", font="Raleway")
        self.paths_label = Label(master, text="Ścieżki: ", font="Raleway")
        self.browse_btn = Button(master, text="Wybierz", command=lambda: self.open_file(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.keep_timing_checkbox = Checkbutton(master, text='Zachowaj timing', variable=self.keep_old_timing)
        self.split_tracks_checkbox = Checkbutton(master, text='Podziel ścieżki', variable=self.split_tracks)
        vcmdInt = (master.register(self.validateInt), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        vcmdFloat = (master.register(self.validateFloat), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.split_entry = Entry(master, text='Liczba części', validate="key", validatecommand=vcmdInt)
        self.ant_count_entry = Entry(master, text='liczba mrówek', validate="key", validatecommand=vcmdInt)
        self.generations = Entry(master, text='liczba iteracji', validate="key", validatecommand=vcmdInt)
        self.alpha = Entry(master, text='alpha', validate="key", validatecommand=vcmdFloat)
        self.beta = Entry(master, text='beta', validate="key", validatecommand=vcmdFloat)
        self.rho = Entry(master, text='rho', validate="key", validatecommand=vcmdFloat)
        self.q = Entry(master, text='intensywność feromonu', validate="key", validatecommand=vcmdInt)
        self.start_btn = Button(master, text='Komponuj', command=lambda: self.start_ants_band(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.play_btn = Button(master, text='Graj', command=lambda: self.play(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.exit_btn = Button(master, text='Zakończ', command=self.master.destroy, font="Raleway", bg="#41075e", fg="white", height=1, width=15)

        # położenie elementów layoutu
        self.file_label.grid(row=0, column=1, columnspan=2)
        self.browse_btn.grid(row=0, column=0)
        self.split_tracks_checkbox.grid(row=2, column=0)
        self.split_entry.grid(row=2, column=1)
        self.keep_timing_checkbox.grid(row=2, column=2)
        self.ant_count_entry.grid(row=3, column=0)
        self.generations.grid(row=3, column=1)
        self.alpha.grid(row=3, column=2)
        self.beta.grid(row=4, column=0)
        self.rho.grid(row=4, column=1)
        self.q.grid(row=4, column=2)
        self.start_btn.grid(row=5, column=0)
        self.play_btn.grid(row=5, column=1)
        self.exit_btn.grid(row=5, column=2)

        self.ant_count_entry.insert(END, 10)
        self.generations.insert(END, 10)
        self.alpha.insert(END, 1.0)
        self.beta.insert(END, 5)
        self.rho.insert(END, 0.1)
        self.q.insert(END, 1)
        self.split_entry.insert(END, 4)

        ant_count_entry_tip = Balloon(master)
        generations_tip = Balloon(master)
        analpha_tip = Balloon(master)
        beta_tip = Balloon(master)
        rho_tip = Balloon(master)
        q_tip = Balloon(master)
        split_tip = Balloon(master)

        ant_count_entry_tip.bind_widget(self.ant_count_entry, balloonmsg="liczba mrówek")
        generations_tip.bind_widget(self.generations, balloonmsg="liczba iteracji")
        analpha_tip.bind_widget(self.alpha, balloonmsg="ważność feromonu")
        beta_tip.bind_widget(self.beta, balloonmsg="ważność informacji heurystycznej")
        rho_tip.bind_widget(self.rho, balloonmsg="współczynnik odparowania śladu feromonowego")
        q_tip.bind_widget(self.q, balloonmsg="intensywność feromonu")
        split_tip.bind_widget(self.split_entry, balloonmsg="Liczba części")

        self.start_btn["state"] = "disabled"
        self.play_btn["state"] = "disabled"

    def open_file(self):
        file = askopenfile(parent=self.master, mode='rb', title="Wybierz plik midi", filetypes=[("Midi file", "*.mid")])
        if file:
            self.file_label.config(text=os.path.basename(file.name))
            self.midi_file_name = file.name
        mid = MidiFile(self.midi_file_name, clip=True)
        self.init_instruments_checkboxes(mid)

    def init_instruments_checkboxes(self, mid: MidiFile):
        self.instruments = []
        for label in self.master.grid_slaves():  # usunięcie starych checkboxów
            if int(label.grid_info()["row"]) == 1:
                label.grid_forget()
        for i in range(len(mid.tracks)):  # szukanie instrumentów w pliku
            for msg in mid.tracks[i]:
                if hasattr(msg, 'name'):
                    self.instruments.append(
                        {'name': msg.name, 'id': i})  # potrzebujemy nazwę instrumentu i index ścieżki
                    break
        print(self.instruments)
        self.start_btn["state"] = "normal"
        for j in range(len(self.instruments)):  # utworzenie checkboxów
            var = IntVar()
            c = Checkbutton(self.master, text=self.instruments[j]['name'], variable=var)
            self.paths_checkbox_dict[self.instruments[j]['id']] = var
            c.grid(row=1, column=j)

    def start_ants_band(self):
        selected_paths = []
        for track_number, check in self.paths_checkbox_dict.items():
            if check.get() == 1:
                selected_paths.append(track_number)
        print(selected_paths)
        # ants_band = AntsBand(MidiFile('data/theRockingAnt.mid', clip=True), [2, 3])
        ants_band = AntsBand(MidiFile(self.midi_file_name, clip=True), selected_paths, self.keep_old_timing.get(),
                             int(self.ant_count_entry.get()), int(self.generations.get()), float(self.alpha.get()),
                             float(self.beta.get()), float(self.rho.get()), int(self.q.get()))
        if self.split_tracks.get():
            midi_file, tracks_data = ants_band.start_and_divide(int(self.split_entry.get()))
            self.openNext(midi_file, tracks_data)
        else:
            midi_file, tracks_data = ants_band.start()
            self.openNext(midi_file, tracks_data)
        self.play_btn["state"] = "normal"

    def play(selfself):
        prepare_and_play("data/result.mid")

    def validateInt(self, action, index, value_if_allowed,
                       prior_value, text, validation_type, trigger_type, widget_name):
        if value_if_allowed:
            try:
                int(value_if_allowed)
                return True
            except ValueError:
                return False
        else:
            return False

    def validateFloat(self, action, index, value_if_allowed,
                       prior_value, text, validation_type, trigger_type, widget_name):
        if value_if_allowed:
            try:
                float(value_if_allowed)
                return True
            except ValueError:
                return False
        else:
            return False

    def openNext(self, midi_file, tracks_data):
        self.newWindow = Toplevel(self.master)
        self.app = ResultWindow(self.newWindow, midi_file, tracks_data)


root = tix.Tk()
app = MainWindow(root)
root.mainloop()
