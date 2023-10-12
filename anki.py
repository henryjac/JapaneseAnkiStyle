import tkinter as tk
import time, random, re, multiprocessing
from PIL import Image, ImageTk
import db_handler

def word_lists(file):
    with open(file) as f:
        lines = f.readlines()

    n = len(lines)
    lines = list(map(lambda x: x.split(), lines))
    japanese = [""]*n
    translation = [""]*n
    for i in range(n):
        japanese[i] = lines[i][0]
        translation[i] = " ".join(lines[i][1:])
    return japanese, translation

def newline_split_translation(trs):
    new_trs = [""]*len(trs)
    for i in range(len(trs)):
        new_trs[i] = "\n".join(re.split(r'(\([^)]*\))', trs[i])).replace("(","").replace(")","")
    return new_trs

def contains_japanese(text):
    # Define a regular expression for kanji, hiragana, and katakana
    japanese_pattern = re.compile(r'[\u4e00-\u9faf\u3040-\u309f\u30a0-\u30ff]')

    # Check if the text contains any Japanese characters
    has_japanese = bool(re.search(japanese_pattern, text))

    return has_japanese

def contains_both(text):
    jap = contains_japanese(text)
    latin_pattern = re.compile(r'[A-Za-z]')
    if jap and re.search(latin_pattern, text):
        return True
    else:
        return False

def setup_database():
    files = ["漢字", "言葉", "verbs", "言葉 <-", "漢字 <-"]
    for game in files:
        file = re.sub(r' <-', '', game)
        jap, trs = word_lists(f"word_files/{file}")

        if '<-' in game:
            trs,jap=jap,trs
        conn, cursor = db_handler.get_db()
        db_handler.create_familiarities(conn, cursor, jap, trs, game)

class StartScreen(tk.Frame):
    def __init__(self, window, mp_counter, mp_trigger, mp_game_type):
        super().__init__(window)

        self.window = window

        background_image = Image.open("figs/kanji.png")
        self.background_photo = ImageTk.PhotoImage(background_image)

        self.backgroundLabel = tk.Label(window)
        self.backgroundLabel.place(relwidth=1,relheight=1)
        
        self.buttons = [
            tk.Button(window, text='漢字', command=lambda: self.words_loop("漢字"), font=("Helvetica",60)),
            tk.Button(window, text="Words", command=lambda: self.words_loop("言葉"), font=("Helvetica",60)),
            tk.Button(window, text='漢字 <-', command=lambda: self.words_loop("漢字", True), font=("Helvetica",60)),
            tk.Button(window, text="Words <-", command=lambda: self.words_loop("言葉", True), font=("Helvetica",60)),
            tk.Button(window, text="Verbs", command=lambda: self.words_loop("verbs"), font=("Helvetica",60))
        ]

        for i,button in enumerate(self.buttons):
            button.pack(expand=True, fill='both', anchor='ne' if i==0 else 'sw')
            button.bind("<Enter>", lambda event, index=i: self.highlight_button(index))
            button.bind("<Leave>", self.clear_highlight)

        self.selected_button = 0
        self.highlight_button(0)

        self.mp_counter = mp_counter
        self.mp_trigger = mp_trigger
        self.mp_game_type = mp_game_type

        self.bind_events()

    def words_loop(self, file_name, rev=False):
        self.__destroy_buttons()
        self.text_looper(f"word_files/{file_name}", rev)

    def text_looper(self, file, rev=False):
        if rev:
            looper = TextLooper(self.window, file+" <-", self.mp_counter, self.mp_trigger, self.mp_game_type)
        else:
            looper = TextLooper(self.window, file, self.mp_counter, self.mp_trigger, self.mp_game_type)

    def __destroy_buttons(self):
        for button in self.buttons:
            button.destroy()

    def bind_events(self):
        self.window.bind("<Control-w>", self.close_window)
        self.window.bind("<Return>", self.choose_button)
        self.window.bind("<Up>", self.move_up)
        self.window.bind("<Down>", self.move_down)

    def highlight_button(self, index):
        self.clear_highlight()
        self.buttons[index].config(bg="yellow")
        self.selected_button = index

    def clear_highlight(self, event=None):
        for button in self.buttons:
            button.config(bg="white")

    def choose_button(self, event):
        # Perform action based on the selected button, e.g., call its associated function.
        self.buttons[self.selected_button].invoke()

    def move_up(self, event):
        self.selected_button = (self.selected_button - 1) % len(self.buttons)
        self.highlight_button(self.selected_button)

    def move_down(self, event):
        self.selected_button = (self.selected_button + 1) % len(self.buttons)
        self.highlight_button(self.selected_button)

    def close_window(self, event):
        self.window.destroy()

class TextLooper(tk.Frame):
    def __init__(self, window, game_type, mp_counter, mp_trigger, mp_game_type):
        self.window = window
        self.window.title(f"Anki: {game_type.split('/')[1]}")

        self.game_type = re.sub(r'.*/', "", game_type)

        self.conn, self.cursor = db_handler.get_db()
        self.current_word = db_handler.select_random_with_probability(self.conn, self.cursor, "fam", self.game_type)

        self.mp_counter = mp_counter
        self.mp_trigger = mp_trigger
        self.mp_game_type = mp_game_type

        match = re.search(r'(.*?) <-', self.game_type)
        if match:
            self.file_base = match.group(1)
        else:
            self.file_base = self.game_type
        self.mp_game_type.value = self.file_base

        w_width = window.winfo_width()
        w_height = window.winfo_height()

        background_image = Image.open("figs/kanji.png")
        background_image.putalpha(50)
        self.background_photo = ImageTk.PhotoImage(background_image)

        self.window.geometry(f"{background_image.width}x{background_image.height}")

        self.label = tk.Label(
            window, 
            compound='center',
            text=f"{self.current_word}", 
            font=("Helvetica", 60),
            image=self.background_photo,
        )
        self.label.pack(expand=True, fill='both', anchor='center')

        # Create labels for familiarity
        self.dont_know = tk.Label(window, text="1. Don't know", font=("Helvetica", 20))
        self.familiar = tk.Label(window, text="2. Familiar", font=("Helvetica", 20))
        self.know = tk.Label(window, text="3. Know", font=("Helvetica", 20))

        # Arrange labels horizontally at the bottom
        self.dont_know.place(x=20, y=background_image.height - 30)
        self.familiar.place(x=200, y=background_image.height - 30)
        self.know.place(x=350, y=background_image.height - 30)

        self.bind_events()

        self.on_question = True

    def db_setup(self):
        self.conn, self.cursor = db_handler.get_db()

    def update_familiarity(self, i):
        if not self.on_question:
            db_handler.add_to_table(
                self.conn,
                self.cursor,
                self.previous_word,
                i,
                "fam",
                self.game_type,
            )

    def change_text(self):
        self.previous_word = self.current_word

        if self.on_question:
            self.current_word = db_handler.select_random_with_probability(self.conn, self.cursor, "fam", self.game_type)
        else:
            self.current_word = db_handler.get_translation(self.conn, self.cursor, self.previous_word, "fam")
        text = self.current_word

        text_width = max(map(lambda x: len(x), text.split("\n")))

        # Adjust the width threshold based on your window size and layout

        if text_width > 12 or (contains_japanese(text) and text_width > 5) or contains_both(text):
            if " " in text:
                text = "\n".join(text.split())
            else:
                midpoint = len(text)//2
                text = "\n".join([text[:midpoint],text[midpoint:]])
            if "/" in text:
                text = "/\n".join(text.split("/"))

        self.label.config(text=text)

    def on_window_click(self, event, i):
        if not self.on_question:
            self.mp_counter.value += 1
            if self.mp_counter.value % 5 == 0 and not self.mp_trigger.value:
                self.mp_trigger.value = True
        self.update_familiarity(i)
        self.on_question = not self.on_question
        self.change_text()

    def bind_events(self):
        self.window.bind("<Button-1>", lambda x: self.on_window_click(x,3))
        self.window.bind("<space>", lambda x: self.on_window_click(x,3))
        self.window.bind("<Return>", lambda x: self.on_window_click(x,3))
        self.window.bind("<Control-w>", self.close_window)
        self.window.bind("<BackSpace>", self.change_back)
        self.window.bind("<Up>", lambda x: None)
        self.window.bind("<Down>", lambda x: None)
        d = {"1":-3,"2":1,"3":3,"0":0}
        for k,v in d.items():
            self.window.bind(k, lambda x, i=v: self.on_window_click(x,i))

    def close_window(self, event):
        self.window.destroy()

    def change_back(self, event):
        self.label.destroy()
        self.window.destroy()
        create_window_with_looping_text(self.mp_counter, self.mp_trigger, self.mp_game_type)

def mp_anki_event(mp_counter, mp_trigger, mp_game_type, mp_exit_event):
    try:
        create_window_with_looping_text(mp_counter, mp_trigger, mp_game_type)
    finally:
        mp_exit_event.set()

def create_window_with_looping_text(mp_counter, mp_trigger, mp_game_type):
    window = tk.Tk()
    window.title("Anki")

    # Make the window square and a bit bigger
    window.geometry("523x523")

    start = StartScreen(window, mp_counter, mp_trigger, mp_game_type)

    window.mainloop()

def sort_word_files():
    for file in ["言葉","漢字"]:
        with open(f"word_files/{file}") as f:
            lines = f.readlines()
        lines.sort()
        with open(f"word_files/{file}", "w") as f:
            f.write("".join(lines))

def background_process(mp_counter, mp_trigger, game_type, mp_exit_event):
    sort_word_files()
    setup_database()
    conn, cursor = db_handler.get_db()
    while not mp_exit_event.is_set():
        time.sleep(2)
        if mp_trigger.value:
            mp_trigger.value = False
            db_handler.update_probabilities(conn, cursor, "fam", game_type.value)

def main():
    counter = multiprocessing.Value("i", 1)
    trigger = multiprocessing.Value("i", False)
    exit_event = multiprocessing.Event()

    manager = multiprocessing.Manager()
    game_type = manager.Value("c", "")

    p1 = multiprocessing.Process(target=background_process, args=(counter,trigger,game_type,exit_event))
    p2 = multiprocessing.Process(target=mp_anki_event, args=(counter,trigger,game_type,exit_event))

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    exit_event.set()

if __name__ == '__main__':
    main()
