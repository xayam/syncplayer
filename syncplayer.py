import json
import os
import pickle
import tkinter as tk
from datetime import datetime
from tkinter import colorchooser
from tkinter import scrolledtext
import tkinter.font as font
from PIL import ImageTk, Image
import pygame
import threading


def findnth(string, substring, n):
    parts = string.split(substring, n + 1)
    if len(parts) <= n + 1:
        return -1
    return len(string) - len(parts[-1]) - len(substring)


def change_slider(_):
    return False


class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SyncPlayer v2.6")
        self.root.resizable(True, True)
        self.root.geometry("800x600+0+0")
        self.root.state('zoomed')
        if os.path.exists("favicon.ico"):
            self.root.iconbitmap("favicon.ico")
        self.root.columnconfigure(index=0, weight=1)
        self.root.columnconfigure(index=1, weight=200)
        self.root.rowconfigure(index=0, weight=1)
        self.root.rowconfigure(index=1, weight=200)
        self.pause_len = 0
        self.pos_end = 0
        self.start = 0
        self.start_index = 0
        self.flag_pause = True
        self.options = {}

        self.frame_top = tk.Frame(master=self.root)
        self.frame_top.grid(column=0, columnspan=2, row=0, sticky=tk.NSEW)

        self.frame_top_button_bg = tk.Button(master=self.frame_top,
                                             text="Цвет фона",
                                             relief=tk.FLAT,
                                             command=self.select_color_bg)
        self.frame_top_button_bg.pack(fill=tk.BOTH, side="left", expand=True, padx=1, pady=1)
        self.frame_top_button_fg = tk.Button(master=self.frame_top,
                                             text="Цвет текста",
                                             relief=tk.FLAT,
                                             command=self.select_color_fg)
        self.frame_top_button_fg.pack(fill=tk.BOTH, side="left", expand=True, padx=1, pady=1)
        self.frame_top_label = tk.Label(master=self.frame_top,
                                        text="Размер текста",
                                        relief=tk.FLAT)
        self.frame_top_label.pack(fill=tk.BOTH, side="left", expand=False, padx=1, pady=1)
        self.frame_top_slider_size = tk.Scale(self.frame_top,
                                              from_=10, to=70,
                                              showvalue=True,
                                              orient=tk.HORIZONTAL, relief=tk.FLAT,
                                              command=self.change_size)
        self.frame_top_slider_size.pack(fill=tk.BOTH, side="left", expand=True, padx=1, pady=1)

        self.frame_left_list = None
        self.frame_content = None
        self.frame_right_navigator = None
        self.right_cover_label = None
        self.frame_right_label = None
        self.frame_right_slider = None
        self.annotation_text_area = None
        self.current_select = None
        self.timer = None
        self.frame_left = tk.Frame(master=self.root)
        self.frame_left.grid(column=0, row=1, sticky=tk.NSEW)
        self.frame_left.columnconfigure(index=0, weight=1)
        self.frame_left.rowconfigure(index=0, weight=200)
        self.frame_left.rowconfigure(index=1, weight=1)

        self.frame_right = tk.Frame(master=self.root)
        self.frame_right.grid(column=1, row=1, sticky=tk.NSEW)
        self.frame_right_label = tk.Label(master=self.frame_right, text="Не выделено ни одной книги")
        self.frame_right_label.pack(fill=tk.X, side="right", expand=True, padx=5, pady=5)

        self.recreate_left_list()

        # self.frame_left_list.select_set(0)
        # self.frame_left_list.event_generate("<<ListboxSelect>>")

        self.root.mainloop()

    def recreate_left_list(self):
        self.books = []
        msg = "Папка ./data не найдена"
        if os.path.exists("data/"):
            msg = "Книги в папке ./data не найдены"
            dir1 = os.scandir("data/")
            for surname in dir1:
                dir2 = os.scandir("data/" + surname.name)
                for book in dir2:
                    if surname.is_dir() and book.is_dir():
                        self.books.append({"surname": surname.name, "book": book.name})
            if not (self.frame_left_list is None):
                self.frame_left_list.delete(0, tk.END)
            self.frame_left_container = tk.Frame(master=self.frame_left)
            self.frame_left_container.grid(column=0, row=0, sticky=tk.N + tk.W + tk.E)
            self.frame_left_list = tk.Listbox(master=self.frame_left_container, height=60, relief="flat")
        if self.books:
            if os.path.exists("options.pkl"):
                with open("options.pkl", mode="rb") as pkl:
                    self.options = pickle.load(pkl)
            else:
                self.options = {"fg": "black", "bg": "white", "fontsize": 20,
                                "positions": ["" for _ in range(len(self.books))]}
            self.frame_top_slider_size.set(self.options["fontsize"])

            self.scrollbar = tk.Scrollbar(self.frame_left_container)
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)
            for book in self.books:
                self.frame_left_list.insert(tk.END, book["surname"] + "_-_" + book["book"])
            self.frame_left_list.pack(fill=tk.BOTH, side="left", expand=True, padx=5, pady=5)
            self.frame_left_list.config(yscrollcommand=self.scrollbar.set)
            self.scrollbar.config(command=self.frame_left_list.yview)
            self.frame_left_list.bind('<<ListboxSelect>>', self.left_listbox_onselect)
            self.frame_left_list.select_set(0)
            self.frame_left_list.event_generate("<<ListboxSelect>>")
            self.frame_left_list.bind("<Button-3>", self.left_popup)
        else:
            self.frame_empty_list = tk.Label(master=self.frame_left, text=msg)
            self.frame_empty_list.grid(column=0, row=0, sticky=tk.NSEW)

    def left_popup(self, event):
        index = self.frame_left_list.curselection()[0]
        popup_menu = tk.Menu(master=self.frame_left_container, tearoff=0)
        dir1 = self.frame_left_list.get(index).split("_-_")[0]
        dir2 = self.frame_left_list.get(index).split("_-_")[1]
        cwd = os.getcwd()
        popup_menu.add_command(label=f"Открыть книгу {dir1} - {dir2}.txt...",
                               command=lambda: os.startfile(f"{cwd}/data/{dir1}/{dir2}/book.txt"))
        popup_menu.add_command(label=f"Открыть книгу {self.frame_left_list.get(index)}.fb2...",
                               command=lambda: os.startfile(f"{cwd}/data/{dir1}/{dir2}/book.fb2"))
        popup_menu.add_command(label=f"Открыть аудиокнигу {self.frame_left_list.get(index)}.flac...",
                               command=lambda: os.startfile(f"{cwd}/data/{dir1}/{dir2}/all.flac"))
        popup_menu.post(event.x_root, event.y_root)

    def left_listbox_onselect(self, evt):
        self.pause_len = 0
        self.pos_end = 0
        self.start = 0
        self.start_index = 0
        self.current_time = 0
        self.line_count = None
        self.pause()
        w = evt.widget
        index = int(w.curselection()[0])
        self.current_select = index

        value = w.get(index)
        self.current_dir = "data/" + value.split("_-_")[0] + "/" + value.split("_-_")[1] + "/"
        annot = open(self.current_dir + "annotation.txt", mode="r", encoding="UTF-8")
        self.annotation = annot.read()
        annot.close()
        with open(self.current_dir + "sync.json", encoding="UTF-8", mode="r") as f:
            self.sync = json.load(f)
        if not (self.frame_right_label is None):
            self.frame_right_label.destroy()
        if not (self.frame_content is None):
            self.frame_content.destroy()
        if not (self.frame_right_navigator is None):
            self.frame_right_navigator.destroy()
        if not (self.right_cover_label is None):
            self.right_cover_label.destroy()
        if not (self.frame_right_slider is None):
            self.frame_right_slider.destroy()
        if not (self.annotation_text_area is None):
            self.annotation_text_area.destroy()

        self.frame_right_navigator = tk.Frame(self.frame_right)
        self.frame_right_navigator.pack(fill=tk.X, side=tk.TOP, expand=False)
        self.empty = tk.Label(master=self.frame_right_navigator, text="", font=("Aerial", 30), width=1)
        self.empty.pack(fill=tk.BOTH, side=tk.LEFT, expand=False)
        self.backward_button = tk.Button(master=self.frame_right_navigator,
                                         text=u"\u23ee",
                                         font=("Aerial", 30),
                                         command=self.backward)
        self.backward_button.pack(fill=tk.BOTH, side=tk.LEFT, expand=False)
        self.play_button = tk.Button(master=self.frame_right_navigator,
                                     text=u"\u23f5",
                                     font=("Aerial", 30),
                                     command=self.tkplay)
        self.play_button.pack(fill=tk.BOTH, side=tk.LEFT, expand=False)
        self.pause_button = tk.Button(master=self.frame_right_navigator,
                                      text=u"\u23f8",
                                      font=("Aerial", 30),
                                      command=self.pause)
        self.pause_button.pack(fill=tk.BOTH, side=tk.LEFT, expand=False)
        self.stop_button = tk.Button(master=self.frame_right_navigator,
                                     text=u"\u23f9",
                                     font=("Aerial", 30),
                                     command=self.stop)
        self.stop_button.pack(fill=tk.BOTH, side=tk.LEFT, expand=False)
        self.forward_button = tk.Button(master=self.frame_right_navigator,
                                        text=u"\u23ed",
                                        font=("Aerial", 30),
                                        command=self.forward)
        self.forward_button.pack(fill=tk.BOTH, side=tk.LEFT, expand=False)
        self.frame_right_slider_value = tk.DoubleVar()
        self.frame_right_slider = tk.Scale(self.frame_right,
                                           from_=0,
                                           to=int(self.sync[-1]["time_end"]) + 60,
                                           showvalue=False,
                                           orient=tk.HORIZONTAL,
                                           command=change_slider,
                                           variable=self.frame_right_slider_value)
        # self.frame_right_slider.pack(fill=tk.X, side=tk.TOP, expand=True, pady=0)

        self.frame_content = tk.Frame(master=self.frame_right)
        self.frame_content.pack(fill=tk.BOTH, side=tk.TOP, expand=True, pady=0)

        self.cover = ImageTk.PhotoImage(Image.open(self.current_dir + "cover.jpg").resize((300, 300)))
        self.right_cover_label = tk.Label(master=self.frame_left, image=self.cover)
        self.right_cover_label.grid(column=0, row=1, sticky=tk.S + tk.W + tk.E)

        self.frame_right_annotation = tk.Frame(self.frame_content)
        self.frame_right_annotation.pack(fill=tk.BOTH, side=tk.TOP, expand=True, pady=0)
        self.annotation_text_area = scrolledtext.ScrolledText(self.frame_right_annotation,
                                                              wrap=tk.WORD,
                                                              font=("Arial", self.options["fontsize"]),
                                                              bg=self.options["bg"],
                                                              fg=self.options["fg"])
        self.annotation_text_area.pack(fill=tk.BOTH, side=tk.RIGHT, expand=True, pady=5)
        self.annotation_text_area.insert(tk.END, self.annotation)
        self.annotation_text_area.bind('<Button-1>', self.annotation_click)
        self.annotation_text_area.delete(1.0, tk.END)
        self.annotation_text_area.bind("<Button-3>", self.left_popup)
        txt = open(self.current_dir + "book.txt", mode="r", encoding="UTF-8")
        self.book = txt.read()
        self.annotation_text_area.insert(tk.END, self.book)
        txt.close()
        self.annotation_text_area.mark_set("insert", "1.0")
        pygame.mixer.music.load(self.current_dir + "all.flac")
        self.annotation_text_area.after_idle(self.annotation_text_area.focus_set)
        opt = self.options["positions"][self.current_select].split("\n")
        if len(opt) == 3:
            self.pause_len = float(opt[0])
            self.annotation_text_area.mark_set("insert", str(opt[1]))
            self.annotation_text_area.see("insert")
            self.frame_right_slider_value.set(float(opt[2]))


    def backward(self):
        if self.books:
            self.frame_left_list.selection_clear(0, 'end')
            index = self.current_select - 1
            if index < 0:
                index = len(self.books) - 1
            self.frame_left_list.select_set(index)
            self.frame_left_list.event_generate("<<ListboxSelect>>")

    def tkplay(self):

        pygame.mixer.music.play(loops=0, start=self.pause_len / 1000.0)
        # pygame.mixer.music.set_pos(self.start)
        self.flag_pause = False
        self.play_timer()

    def pause(self):
        pygame.mixer.music.pause()
        if not (self.timer is None):
            self.timer.cancel()
        self.pause_len += pygame.mixer.music.get_pos()
        self.flag_pause = True

    def stop(self):
        pygame.mixer.music.stop()
        self.flag_pause = True
        self.pause_len = 0
        self.pos_end = 0
        self.start = 0

    def forward(self):
        if self.books:
            self.frame_left_list.selection_clear(0, 'end')
            index = self.current_select + 1
            if index > len(self.books) - 1:
                index = 0
            self.frame_left_list.select_set(index)
            self.frame_left_list.event_generate("<<ListboxSelect>>")

    def play_timer(self):
        for i in range(len(self.sync) - 1):
            if self.sync[i]["time_start"] * 1000.0 > self.pause_len + pygame.mixer.music.get_pos():
                txt = self.book[:self.sync[i]["pos_start"]]
                split1 = txt.split("\n")
                words = split1[-1].split(" ")
                count_chars = 0
                for j in range(len(words) - 1):
                    count_chars += len(words[j]) + 1
                    if (self.sync[i]["word"].lower() == words[j].lower()) and (len(words[j]) > 2) and \
                            (self.sync[i + 1]["word"].lower() == words[j + 1].lower()) and (len(words[j + 1]) > 2):
                        break
                count_lines = len(split1)
                # self.annotation_text_area.mark_set("insert", f"{count_lines}.{5} lineend")
                self.annotation_text_area.mark_set("insert", f"{count_lines}.{count_chars}")
                if self.flag_pause:
                    self.annotation_text_area.see("insert")
                self.centered_insert()
                self.pos_end = self.sync[i]["pos_start"]
                self.start = self.sync[i]["time_start"]
                self.frame_right_slider_value.set(self.start)
                with open("options.pkl", mode="wb") as pkl:
                    self.options["positions"][self.current_select] = \
                        str(self.pause_len + pygame.mixer.music.get_pos()) + \
                        "\n" + f"{count_lines}.{count_chars}" + \
                        "\n" + str(self.start)
                    pickle.dump(self.options, pkl)
                break
        self.timer = threading.Timer(0.5, self.play_timer)
        self.timer.start()
        if self.flag_pause:
            self.timer.cancel()

    def annotation_click(self, _):
        index = self.annotation_text_area.index("current")
        ind = index.split(".")
        txt = self.book
        position = findnth(txt, "\n", int(ind[0]) - 2)
        for data in self.sync:
            if data["pos_start"] >= position:
                count_lines = int(ind[0]) - 2
                count_chars = 0  # int(ind[1])
                self.annotation_text_area.mark_set("insert", f"{count_lines}.{count_chars}")
                # self.annotation_text_area.see("insert")
                self.centered_insert()
                self.pos_end = data["pos_start"]
                self.start = data["time_start"]
                self.pause_len = self.start * 1000
                self.frame_right_slider_value.set(self.start)
                break
        self.tkplay()

    def select_color_bg(self):
        color = str(colorchooser.askcolor(title="Выберите цвет фона")[1])
        if color != "None":
            self.options["bg"] = color
        self.frame_left_list.select_set(self.current_select)
        self.frame_left_list.event_generate("<<ListboxSelect>>")

    def select_color_fg(self):
        color = str(colorchooser.askcolor(title="Выберите цвет текста")[1])
        if color != "None":
            self.options["fg"] = color
        self.frame_left_list.select_set(self.current_select)
        self.frame_left_list.event_generate("<<ListboxSelect>>")

    def change_size(self, _):
        self.options["fontsize"] = int(self.frame_top_slider_size.get())
        self.frame_left_list.select_set(self.current_select)
        self.frame_left_list.event_generate("<<ListboxSelect>>")

    def centered_insert(self):
        if self.line_count is None:
            self.text_area_line_count()
        self.annotation_text_area.see("insert")
        height = int(self.annotation_text_area['height'])
        w_height = self.annotation_text_area.winfo_height()
        height_1 = w_height / height
        top_y, _ = self.annotation_text_area.yview()

        if top_y:
            if self.annotation_text_area.bbox("insert") is not None:
                cursor_y = self.annotation_text_area.bbox("insert")[1] / height_1
                center_y = top_y
                if cursor_y > height / 2:
                    center_y = top_y + (cursor_y - height / 2) / self.line_count
                self.annotation_text_area.yview_moveto(center_y)

    def text_area_line_count(self):
        # self.line_count = self.annotation_text_area.tk.call((self.annotation_text_area._w,
        #                                                      "count", "-update", "-displaylines", "1.0", "end"))
        font1 = font.Font(font=self.annotation_text_area['font'])
        widget_width = self.annotation_text_area.winfo_width()
        max_chars_per_line = int(widget_width / font1.measure(" "))
        lines = self.book.split("\n\n")
        count = -2
        for l in lines:
            count += 3 + len(l) // max_chars_per_line
        self.line_count = count


pygame.mixer.pre_init()
pygame.mixer.init()
pygame.init()

app = Application()
