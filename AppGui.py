# import tkinter as tk
from tkinter import *
from tkinter.filedialog import askopenfile
import os

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

        canvas = Canvas(master, width=500, height=300)
        canvas.grid(columnspan=3, rowspan=3)

        #  self.makeform(master)
        self.file_label = Label(master, text="Wybierz pik midi", font="Raleway")
        self.paths_label = Label(master, text="Ścieżki: ", font="Raleway")
        self.browse_btn = Button(root, text="Wybierz", command=lambda: self.open_file(), font="Raleway", bg="#41075e", fg="white", height=2, width=15)
        # vcmd = self.master.register(self.validate)  # we have to wrap the command
        self.paths_entry = Entry(master)
        self.start_btn = Button(master, text='Komponuj', command=lambda: self.start_ants_band(), font="Raleway", bg="#41075e", fg="white", height=2, width=15)
        self.play_btn = Button(master, text='Graj', command=lambda: self.play(), font="Raleway", bg="#41075e", fg="white", height=2, width=15)
        self.exit_btn = Button(root, text='Zakończ', command=self.master.destroy, font="Raleway", bg="#41075e", fg="white", height=2, width=15)

        self.file_label.grid(row=0, column=0)
        self.browse_btn.grid(row=0, column=1)
        self.paths_label.grid(row=1, column=0)
        self.paths_entry.grid(row=1, column=1)
        self.start_btn.grid(row=2, column=0)
        self.play_btn.grid(row=2, column=1)
        self.exit_btn.grid(row=2, column=2)
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
        ants_band = AntsBand(MidiFile(self.midi_file_name, clip=True), self.selected_paths)
        ants_band.start()

    def play(selfself):
        prepare_and_play("data/result.mid")

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
root = Tk()
app = MainWindow(root)
root.mainloop()
