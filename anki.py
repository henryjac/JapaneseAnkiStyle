import tkinter as tk
import time, random, re, multiprocessing
from PIL import Image, ImageTk
import db_handler, word_handler
import settings

class StartScreen(tk.Frame):
    def __init__(self, window, mp_counter, mp_trigger, mp_game_type):
        super().__init__(window)

        self.window = window
        # Calculate window position for centering
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = 523  # Replace with your desired window width
        window_height = 523  # Replace with your desired window height
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.resizable(False, False)

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
        self.current_word = db_handler.select_random_with_probability(self.conn, self.cursor, settings.Global.table, self.game_type)

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

        text = word_handler.format_text(self.current_word)
        self.label = tk.Label(
            window, 
            compound='center',
            text=f"{text}", 
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
        self.on_pronounciation = False

    def db_setup(self):
        self.conn, self.cursor = db_handler.get_db()

    def update_familiarity(self, i):
        if not self.on_question:
            db_handler.add_to_table(
                self.conn,
                self.cursor,
                self.previous_word,
                i,
                settings.Global.table,
                self.game_type,
            )

    def change_text(self):
        self.previous_word = self.current_word

        if self.on_question:
            self.current_word = db_handler.select_random_with_probability(self.conn, self.cursor, settings.Global.table, self.game_type)
        else:
            self.current_word = db_handler.get_translation(self.conn, self.cursor, self.previous_word, settings.Global.table)
        text = self.current_word

        text = word_handler.format_text(text)

        self.label.config(text=text, fg="black")

    def on_window_click(self, event, i):
        if not self.on_question:
            self.mp_counter.value += 1
            if self.mp_counter.value % 5 == 0 and not self.mp_trigger.value:
                self.mp_trigger.value = True
        self.update_familiarity(i)
        self.on_question = not self.on_question
        self.change_text()

    def bind_events(self):
        for cmd in ["<Button-1>","<Return>"]:
            self.window.bind(cmd, lambda x: self.on_window_click(x,10))
        self.window.bind("<space>", self.show_pronounciation)
        self.window.bind("<Control-w>", self.close_window)
        self.window.bind("<BackSpace>", self.change_back)
        self.window.bind("<Up>", lambda x: None)
        self.window.bind("<Down>", lambda x: None)
        d = {"1":-5,"2":5,"3":10,"0":0}
        for k,v in d.items():
            self.window.bind(k, lambda x, i=v: self.on_window_click(x,i))

    def show_pronounciation(self, event):
        if self.on_pronounciation:
            text = word_handler.format_text(self.current_word)
            self.label.config(text=text, fg="black")
            self.on_pronounciation = False
            return

        if self.on_question:
            word = self.current_word
        else:
            word = self.previous_word
        pronounciation = db_handler.get_pronounciation(self.conn, self.cursor, word, settings.Global.table)
        if pronounciation:
            pronounciation = word_handler.format_text(pronounciation)
            self.label.config(text=pronounciation, fg="red")
            self.on_pronounciation = True

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

def background_process(mp_counter, mp_trigger, game_type, mp_exit_event):
    word_handler.sort_word_files()
    word_handler.setup_database()
    conn, cursor = db_handler.get_db()
    while not mp_exit_event.is_set():
        time.sleep(2)
        if mp_trigger.value:
            mp_trigger.value = False
            db_handler.update_probabilities(conn, cursor, settings.Global.table, game_type.value)

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
