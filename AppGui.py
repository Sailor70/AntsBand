# import tkinter as tk
from tkinter import *
from tkinter import tix
from tkinter.filedialog import askopenfile
import os
from tkinter.tix import Balloon

from mido import MidiFile
from midiPlayer import prepare_and_play

from AntsBandMain import AntsBand


class NextWindow:
    def __init__(self, master):
        self.master = master
        master.title("Next")
        self.button = Button(master, text='Close',  command=master.destroy)
        self.button.pack()


class MainWindow:  # (Frame)

    def __init__(self, master):
        # super().__init__(master)
        self.master = master
        master.title("AntsBand 1.0")
        master.geometry("500x300")
        # master.resizable(False, False)
        self.midi_file_name = ''
        self.selected_paths = []
        self.keep_old_timing = BooleanVar()
        self.keep_old_timing.set(True)

        canvas = Canvas(master, width=500, height=300)
        canvas.grid(columnspan=3, rowspan=5)

        """
        :param ant_count: liczba mrówek
        :param generations: liczba iteracji
        :param alpha: ważność feromonu
        :param beta: ważność informacji heurystycznej
        :param rho: współczynnik odparowania śladu feromonowego
        :param q: intensywność feromonu
        :param strategy: strategia aktualizacji śladu feromonowego. 0 - ant-cycle, 1 - ant-quality, 2 - ant-density
        """

        #  self.makeform(master)
        self.file_label = Label(master, text="Wybierz pik midi", font="Raleway")
        self.paths_label = Label(master, text="Ścieżki: ", font="Raleway")
        self.browse_btn = Button(master, text="Wybierz", command=lambda: self.open_file(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        # vcmd = self.master.register(self.validate)  # we have to wrap the command
        self.paths_entry = Entry(master)
        self.keep_timing_checkbox = Checkbutton(master, text='Zachowaj timing', variable=self.keep_old_timing)
        vcmdInt = (master.register(self.validateInt), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        vcmdFloat = (master.register(self.validateFloat), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.ant_count_entry = Entry(master, text='liczba mrówek', validate="key", validatecommand=vcmdInt)
        self.generations = Entry(master, text='liczba iteracji', validate="key", validatecommand=vcmdInt)
        self.alpha = Entry(master, text='alpha', validate="key", validatecommand=vcmdFloat)
        self.beta = Entry(master, text='beta', validate="key", validatecommand=vcmdFloat)
        self.rho = Entry(master, text='rho', validate="key", validatecommand=vcmdFloat)
        self.q = Entry(master, text='intensywność feromonu', validate="key", validatecommand=vcmdInt)
        self.start_btn = Button(master, text='Komponuj', command=lambda: self.start_ants_band(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.play_btn = Button(master, text='Graj', command=lambda: self.play(), font="Raleway", bg="#41075e", fg="white", height=1, width=15)
        self.exit_btn = Button(master, text='Zakończ', command=self.master.destroy, font="Raleway", bg="#41075e", fg="white", height=1, width=15)

        self.file_label.grid(row=0, column=0)
        self.browse_btn.grid(row=0, column=1)
        self.paths_label.grid(row=1, column=0)
        self.paths_entry.grid(row=1, column=1)
        self.keep_timing_checkbox.grid(row=1, column=2)
        self.ant_count_entry.grid(row=2, column=0)
        self.generations.grid(row=2, column=1)
        self.alpha.grid(row=2, column=2)
        self.beta.grid(row=3, column=0)
        self.rho.grid(row=3, column=1)
        self.q.grid(row=3, column=2)
        self.start_btn.grid(row=4, column=0)
        self.play_btn.grid(row=4, column=1)
        self.exit_btn.grid(row=4, column=2)

        self.ant_count_entry.insert(END, 10)
        self.generations.insert(END, 10)
        self.alpha.insert(END, 1.0)
        self.beta.insert(END, 5)
        self.rho.insert(END, 0.1)
        self.q.insert(END, 1)

        ant_count_entry_tip = Balloon(master)
        generations_tip = Balloon(master)
        analpha_tip = Balloon(master)
        beta_tip = Balloon(master)
        rho_tip = Balloon(master)
        q_tip = Balloon(master)

        ant_count_entry_tip.bind_widget(self.ant_count_entry, balloonmsg="liczba mrówek")
        generations_tip.bind_widget(self.generations, balloonmsg="liczba iteracji")
        analpha_tip.bind_widget(self.alpha, balloonmsg="ważność feromonu")
        beta_tip.bind_widget(self.beta, balloonmsg="ważność informacji heurystycznej")
        rho_tip.bind_widget(self.rho, balloonmsg="współczynnik odparowania śladu feromonowego")
        q_tip.bind_widget(self.q, balloonmsg="intensywność feromonu")


        # self.button = Button(master, text='Open', command=self.openNext)
        # self.button.pack()

    def open_file(self):
        file = askopenfile(parent=self.master, mode='rb', title="Wybierz plik midi", filetypes=[("Midi file", "*.mid")])
        if file:
            # text_box = Text(self.master, height=10, width=50, padx=15, pady=15)
            # text_box.insert(1.0, file.name)
            # text_box.grid(column=2, row=0)
            self.file_label.config(text=os.path.basename(file.name))
            self.midi_file_name = file.name

    def start_ants_band(self):
        # period rate:
        self.selected_paths = [int(numeric_string) for numeric_string in str(self.paths_entry.get()).split(",")]  # walidacje ogarnąć
        print(self.selected_paths)
        # ants_band = AntsBand(MidiFile('data/theRockingAnt.mid', clip=True), [2, 3])
        ants_band = AntsBand(MidiFile(self.midi_file_name, clip=True), self.selected_paths, self.keep_old_timing.get(),
                             int(self.ant_count_entry.get()), int(self.generations.get()), float(self.alpha.get()),
                             float(self.beta.get()), float(self.rho.get()), int(self.q.get()))
        ants_band.start()

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

    # def validate(self, new_text):
    #     if not new_text:  # the field is being cleared
    #         self.selected_paths = []
    #         return True
    #     try:
    #         self.selected_paths = [int(numeric_string) for numeric_string in str(new_text).split(",")]
    #         print(self.selected_paths)
    #         return True
    #     except ValueError:
    #         return False

    # open next window
    # def openNext(self):
    #     self.newWindow = Toplevel(self.master)
    #     self.app = NextWindow(self.newWindow)


# main program #
root = tix.Tk()
app = MainWindow(root)
root.mainloop()
