import copy
import time
from tkinter import *
from tkinter import tix
from tkinter.filedialog import askopenfile
import os
from tkinter.tix import Balloon
from tkinter import messagebox
from mido import MidiFile

from ResultWindow import ResultWindow
from AntsBandMain import AntsBand


class MainWindow:

    def __init__(self, master):
        self.master = master
        master.title("AntsBand 1.0")
        master.geometry("600x350")
        # master.resizable(False, False)
        master.option_add("*Font", "Raleway")  # czcionka globalnie
        master.iconbitmap(r'G:\ProgProjects\Python\AntsBand\src\antIcon.ico')

        # zmienne pomocnicze
        self.midi_input = None
        self.paths_checkbox_dict = {}
        self.instruments = []
        self.keep_old_timing = BooleanVar()
        self.keep_old_timing.set(True)
        self.mix_phrases = BooleanVar()
        self.mix_phrases.set(False)
        self.split_tracks = BooleanVar()
        self.split_tracks.set(False)
        self.algorithm_var = IntVar()

        canvas = Canvas(master, width=600, height=350)
        canvas.grid(columnspan=3, rowspan=9)

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
        self.track_length_entry = Entry(master, text='Długość utworu', validate="key", validatecommand=vcmdInt, width=8)
        self.keep_timing_checkbox = Checkbutton(master, text='Zachowaj timing', variable=self.keep_old_timing)
        self.mix_phrases_checkbox = Checkbutton(master, text='Mieszaj podział', variable=self.mix_phrases)
        self.split_tracks_checkbox = Checkbutton(master, text='Podziel ścieżki', variable=self.split_tracks, command=lambda: self.split_tracks_change())
        self.algorithm_label = Label(master, text="Algorytm: ", font="Raleway")
        self.split_entry = Entry(master, text='Liczba części', validate="key", validatecommand=vcmdInt, width=8)
        self.as_radio_btn = Radiobutton(self.master, text='AS', variable=self.algorithm_var, value=0, command=lambda: self.algorithm_change())
        self.acs_radio_btn = Radiobutton(self.master, text='ACS', variable=self.algorithm_var, value=1, command=lambda: self.algorithm_change())
        self.ant_count_label = Label(master, text='l. mrówek')
        self.generations_label = Label(master, text='l. iteracji')
        self.alpha_label = Label(master, text='\u03B1')
        self.beta_label = Label(master, text='\u03B2')
        self.rho_label = Label(master, text='\u03C1')
        self.q_label = Label(master, text='q')
        self.phi_label = Label(master, text='\u03C6')
        self.q_zero_label = Label(master, text='q0')
        self.sigma_label = Label(master, text='\u03C3')
        self.ant_count_entry = Entry(master, text='liczba mrówek', validate="key", validatecommand=vcmdInt, width=8)
        self.generations = Entry(master, text='liczba iteracji', validate="key", validatecommand=vcmdInt, width=8)
        self.alpha = Entry(master, text='alpha', validate="key", validatecommand=vcmdFloat, width=8)
        self.beta = Entry(master, text='beta', validate="key", validatecommand=vcmdFloat, width=8)
        self.rho = Entry(master, text='rho', validate="key", validatecommand=vcmdFloat, width=8)
        self.q = Entry(master, text='intensywność feromonu', validate="key", validatecommand=vcmdInt, width=8)
        self.phi = Entry(master, text='współczynnik parowania (lokalny)', validate="key", validatecommand=vcmdFloat, width=8)
        self.q_zero = Entry(master, text='współczynnik chciwości', validate="key", validatecommand=vcmdFloat, width=8)
        self.sigma = Entry(master, text='feromon inicjalny', validate="key", validatecommand=vcmdFloat, width=8)
        self.start_btn = Button(master, text='Komponuj', command=lambda: self.start_ants_band(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.exit_btn = Button(master, text='Zakończ', command=self.master.destroy, font="Raleway", bg="#41075e", fg="white", height=1, width=15)

        # położenie elementów layoutu
        self.file_label.grid(row=0, column=1, columnspan=2)
        self.browse_btn.grid(row=0, column=0)
        self.track_length.grid(row=2, column=0)
        self.track_length_entry.grid(row=2, column=1)
        self.keep_timing_checkbox.grid(row=2, column=2)
        self.split_tracks_checkbox.grid(row=3, column=0)
        self.split_entry.grid(row=3, column=1)
        self.mix_phrases_checkbox.grid(row=3, column=2)
        self.algorithm_label.grid(row=4, column=0)
        self.as_radio_btn.grid(row=4, column=1, sticky='ew')
        self.acs_radio_btn.grid(row=4, column=2, sticky='ew')
        self.ant_count_label.grid(row=5, column=0, sticky='w', padx=5)
        self.ant_count_entry.grid(row=5, column=0, padx=70)
        self.generations_label.grid(row=5, column=1, sticky='w')
        self.generations.grid(row=5, column=1, padx=60)
        self.alpha_label.grid(row=5, column=2, sticky='w')
        self.alpha.grid(row=5, column=2)
        self.beta_label.grid(row=6, column=0, sticky='w', padx=5)
        self.beta.grid(row=6, column=0, padx=60)
        self.rho_label.grid(row=6, column=1, sticky='w')
        self.rho.grid(row=6, column=1)
        self.q_label.grid(row=6, column=2, sticky='w')
        self.q.grid(row=6, column=2)
        self.phi_label.grid(row=7, column=0, sticky='w', padx=5)
        self.phi.grid(row=7, column=0, padx=60)
        self.q_zero_label.grid(row=7, column=1, sticky='w')
        self.q_zero.grid(row=7, column=1)
        self.sigma_label.grid(row=7, column=2, sticky='w')
        self.sigma.grid(row=7, column=2)
        self.start_btn.grid(row=8, column=0)
        self.exit_btn.grid(row=8, column=2)

        self.ant_count_entry.insert(END, 10)
        self.generations.insert(END, 10)
        self.alpha.insert(END, 1.0)
        self.beta.insert(END, 2.0)
        self.rho.insert(END, 0.3)
        self.q.insert(END, 1)
        self.split_entry.insert(END, 4)
        self.track_length_entry.insert(END, 1)
        self.phi.insert(END, 0.2)
        self.q_zero.insert(END, 0.5)
        self.sigma.insert(END, 10.0)

        ant_count_entry_tip = Balloon(master)
        generations_tip = Balloon(master)
        analpha_tip = Balloon(master)
        beta_tip = Balloon(master)
        rho_tip = Balloon(master)
        q_tip = Balloon(master)
        split_tip = Balloon(master)
        phi_tip = Balloon(master)
        q_zero_tip = Balloon(master)
        sigma_tip = Balloon(master)

        ant_count_entry_tip.bind_widget(self.ant_count_entry, balloonmsg="liczba mrówek")
        generations_tip.bind_widget(self.generations, balloonmsg="liczba iteracji")
        analpha_tip.bind_widget(self.alpha, balloonmsg="ważność feromonu")
        beta_tip.bind_widget(self.beta, balloonmsg="ważność informacji heurystycznej")
        rho_tip.bind_widget(self.rho, balloonmsg="współczynnik odparowania śladu feromonowego")
        q_tip.bind_widget(self.q, balloonmsg="intensywność feromonu")
        split_tip.bind_widget(self.split_entry, balloonmsg="Liczba części")
        phi_tip.bind_widget(self.phi, balloonmsg="Współczynnik odparowania śladu feromonowego (lokalnie, po każdym przejściu)")
        q_zero_tip.bind_widget(self.q_zero, balloonmsg="Współczynnik chciwości")
        sigma_tip.bind_widget(self.sigma, balloonmsg="feromon inicjalny")

        self.mix_phrases_checkbox["state"] = "disabled"
        self.start_btn["state"] = "disabled"
        self.phi["state"] = "disabled"
        self.q_zero["state"] = "disabled"

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
                        {'name': msg.name, 'id': i})  # nazwa instrumentu i index ścieżki
                    break
        # print(self.instruments)
        self.start_btn["state"] = "normal"
        for j in range(len(self.instruments)):  # utworzenie nowych checkboxów
            var = IntVar()
            c = Checkbutton(self.master, text=self.instruments[j]['name'], variable=var)
            self.paths_checkbox_dict[self.instruments[j]['id']] = var
            c.grid(row=1, column=j)

    def algorithm_change(self):
        print(str(self.algorithm_var.get()))
        if self.algorithm_var.get() == 0:
            self.phi["state"] = "disabled"
            self.q_zero["state"] = "disabled"
        else:
            self.phi["state"] = "normal"
            self.q_zero["state"] = "normal"

    def split_tracks_change(self):
        if self.split_tracks.get():
            self.mix_phrases_checkbox["state"] = "normal"
        else:
            self.mix_phrases_checkbox["state"] = "disabled"

    def start_ants_band(self):
        selected_paths = []
        not_selected_paths = []
        for track_number, check in self.paths_checkbox_dict.items():
            if check.get() == 1:
                selected_paths.append(track_number)
            else:
                not_selected_paths.append(track_number)
        if len(selected_paths) < 1:
            messagebox.showerror('Nieprawidłowa wartość', 'Wybierz przynajmniej jedną ścieżkę')
            return 0
        # ants_band = AntsBand(MidiFile('./data/theRockingAnt.mid', clip=True), [2, 3])
        ants_band = AntsBand(midi_file=copy.deepcopy(self.midi_input), tracks_numbers=selected_paths, keep_old_timing=self.keep_old_timing.get(),
                             result_track_length=self.track_length_entry.get(), algorithm_type=self.algorithm_var.get(),
                             ant_count=int(self.ant_count_entry.get()), generations=int(self.generations.get()), alpha=float(self.alpha.get()),
                             beta=float(self.beta.get()), rho=float(self.rho.get()), q=int(self.q.get()), phi=float(self.phi.get()),
                             q_zero=float(self.q_zero.get()), sigma=float(self.sigma.get()))
        try:
            start_time = time.time()
            if self.split_tracks.get():
                if int(self.track_length_entry.get()) > 1:
                        midi_result, tracks_data = ants_band.start_divide_and_extend(int(self.split_entry.get()), int(self.track_length_entry.get()), not_selected_paths, bool(self.mix_phrases.get()))
                else:
                    midi_result, tracks_data, cost = ants_band.start_and_divide(int(self.split_entry.get()), bool(self.mix_phrases.get()))
            else:
                if int(self.track_length_entry.get()) > 1:
                    midi_result, tracks_data = ants_band.start_and_extend(int(self.track_length_entry.get()), not_selected_paths)
                else:
                    midi_result, tracks_data, cost = ants_band.start()
            execution_time = time.time() - start_time
            self.openNext(midi_result, tracks_data, execution_time)
        except Exception as e:
            messagebox.showerror('Błąd', 'Wystąpił błąd: ' + str(e))
            raise  # pluje błędem do konsoli

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

    def openNext(self, midi_result, tracks_data, execution_time):
        self.newWindow = Toplevel(self.master)
        self.app = ResultWindow(self.newWindow, midi_result, tracks_data, self.midi_input, execution_time)


root = tix.Tk()
app = MainWindow(root)
root.mainloop()
