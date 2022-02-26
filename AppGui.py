from tkinter import *
from tkinter import tix
from tkinter.filedialog import askopenfile
import os
from tkinter.tix import Balloon

from AntsBandActions import *
from ResultWindow import ResultWindow
from AntsBandMain import AntsBand


class MainWindow:

    def __init__(self, master):
        self.master = master
        master.title("AntsBand 1.0")
        master.geometry("600x300")
        # master.resizable(False, False)

        # zmienne pomocnicze
        self.midi_input = None
        self.paths_checkbox_dict = {}
        self.instruments = []
        self.keep_old_timing = BooleanVar()
        self.keep_old_timing.set(True)
        self.split_tracks = BooleanVar()
        self.split_tracks.set(False)

        canvas = Canvas(master, width=600, height=300)
        canvas.grid(columnspan=3, rowspan=7)

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
        self.browse_btn = Button(master, text="Wybierz", command=lambda: self.open_file(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.track_length = Label(master, text="Długość utworu: ", font="Raleway")
        vcmdInt = (master.register(self.validateInt), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        vcmdFloat = (master.register(self.validateFloat), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.track_length_entry = Entry(master, text='Długość utworu', validate="key", validatecommand=vcmdInt)
        self.keep_timing_checkbox = Checkbutton(master, text='Zachowaj timing', variable=self.keep_old_timing)
        self.split_tracks_checkbox = Checkbutton(master, text='Podziel ścieżki', variable=self.split_tracks)
        self.split_entry = Entry(master, text='Liczba części', validate="key", validatecommand=vcmdInt)
        self.ant_count_entry = Entry(master, text='liczba mrówek', validate="key", validatecommand=vcmdInt)
        self.generations = Entry(master, text='liczba iteracji', validate="key", validatecommand=vcmdInt)
        self.alpha = Entry(master, text='alpha', validate="key", validatecommand=vcmdFloat)
        self.beta = Entry(master, text='beta', validate="key", validatecommand=vcmdFloat)
        self.rho = Entry(master, text='rho', validate="key", validatecommand=vcmdFloat)
        self.q = Entry(master, text='intensywność feromonu', validate="key", validatecommand=vcmdInt)
        self.start_btn = Button(master, text='Komponuj', command=lambda: self.start_ants_band(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.exit_btn = Button(master, text='Zakończ', command=self.master.destroy, font="Raleway", bg="#41075e", fg="white", height=1, width=15)

        # położenie elementów layoutu
        self.file_label.grid(row=0, column=1, columnspan=2)
        self.browse_btn.grid(row=0, column=0)
        self.track_length.grid(row=2, column=0)
        self.track_length_entry.grid(row=2, column=1)
        self.split_tracks_checkbox.grid(row=3, column=0)
        self.split_entry.grid(row=3, column=1)
        self.keep_timing_checkbox.grid(row=3, column=2)
        self.ant_count_entry.grid(row=4, column=0)
        self.generations.grid(row=4, column=1)
        self.alpha.grid(row=4, column=2)
        self.beta.grid(row=5, column=0)
        self.rho.grid(row=5, column=1)
        self.q.grid(row=5, column=2)
        self.start_btn.grid(row=6, column=0)
        self.exit_btn.grid(row=6, column=2)

        self.ant_count_entry.insert(END, 10)
        self.generations.insert(END, 10)
        self.alpha.insert(END, 1.0)
        self.beta.insert(END, 5)
        self.rho.insert(END, 0.1)
        self.q.insert(END, 1)
        self.split_entry.insert(END, 4)
        self.track_length_entry.insert(END, 1)

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

    def open_file(self):
        file = askopenfile(parent=self.master, mode='rb', title="Wybierz plik midi", filetypes=[("Midi file", "*.mid")])
        if file:
            self.file_label.config(text=os.path.basename(file.name))
        self.midi_input = MidiFile(file.name, clip=True)
        self.init_instruments_checkboxes(self.midi_input)

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
        # print(self.instruments)
        self.start_btn["state"] = "normal"
        for j in range(len(self.instruments)):  # utworzenie checkboxów
            var = IntVar()
            c = Checkbutton(self.master, text=self.instruments[j]['name'], variable=var)
            self.paths_checkbox_dict[self.instruments[j]['id']] = var
            c.grid(row=1, column=j)

    def start_ants_band(self):
        selected_paths = []
        not_selected_paths = []
        for track_number, check in self.paths_checkbox_dict.items():
            if check.get() == 1:
                selected_paths.append(track_number)
            else:
                not_selected_paths.append(track_number)
        # ants_band = AntsBand(MidiFile('data/theRockingAnt.mid', clip=True), [2, 3])
        ants_band = AntsBand(self.midi_input, selected_paths, self.keep_old_timing.get(), self.track_length_entry.get(),
                             int(self.ant_count_entry.get()), int(self.generations.get()), float(self.alpha.get()),
                             float(self.beta.get()), float(self.rho.get()), int(self.q.get()))
        if self.split_tracks.get():
            if int(self.track_length_entry.get()) > 1:
                midi_result, tracks_data = ants_band.start_divide_and_extend(int(self.split_entry.get()), int(self.track_length_entry.get()), not_selected_paths)
            else:
                midi_result, tracks_data = ants_band.start_and_divide(int(self.split_entry.get()))
            self.openNext(midi_result, tracks_data)
        else:
            midi_result, tracks_data = ants_band.start()
            self.openNext(midi_result, tracks_data)

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

    def openNext(self, midi_result, tracks_data):
        self.newWindow = Toplevel(self.master)
        self.app = ResultWindow(self.newWindow, midi_result, tracks_data, self.midi_input)


root = tix.Tk()
app = MainWindow(root)
root.mainloop()
