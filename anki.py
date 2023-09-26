import tkinter as tk
from PIL import Image, ImageTk
import random
import re

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

class StartScreen(tk.Frame):
    def __init__(self, window):
        super().__init__(window)

        self.window = window

        background_image = Image.open("figs/kanji.png")
        self.background_photo = ImageTk.PhotoImage(background_image)

        self.backgroundLabel = tk.Label(window)
        self.backgroundLabel.place(relwidth=1,relheight=1)
        
        self.kanjiButton = tk.Button(window, text='漢字', command=self.kanji_loop, font=("Helvetica",60))
        self.kanjiButton.pack(expand=True, fill='both', anchor='ne')

        self.wordButton = tk.Button(window, text="Words", command=self.words_loop, font=("Helvetica",60))
        self.wordButton.pack(expand=True, fill='both', anchor='se')

        self.kanjiButtonR = tk.Button(window, text='漢字 <-', command=self.kanji_loop_R, font=("Helvetica",60))
        self.kanjiButtonR.pack(expand=True, fill='both', anchor='nw')

        self.wordButtonR = tk.Button(window, text="Words <-", command=self.words_loop_R, font=("Helvetica",60))
        self.wordButtonR.pack(expand=True, fill='both', anchor='sw')

    def kanji_loop(self):
        self.__destroy_buttons()
        self.text_looper("word_files/漢字")

    def words_loop(self):
        self.__destroy_buttons()
        self.text_looper("word_files/言葉")

    def kanji_loop_R(self):
        self.__destroy_buttons()
        self.text_looper("word_files/漢字", True)

    def words_loop_R(self):
        self.__destroy_buttons()
        self.text_looper("word_files/言葉", True)

    def text_looper(self, file, rev=False):
        jap, trs = word_lists(file)
        trs = newline_split_translation(trs)
        if rev:
            looper = TextLooper(self.window, trs, jap, file)
        else:
            looper = TextLooper(self.window, jap, trs, file)

    def __destroy_buttons(self):
        self.kanjiButton.destroy()
        self.kanjiButtonR.destroy()
        self.wordButton.destroy()
        self.wordButtonR.destroy()

class TextLooper(tk.Frame):
    def __init__(self, window, text_list_1, text_list_2, game_type):
        self.window = window
        self.window.title(f"Anki: {game_type.split('/')[1]}")
        self.n = self.check_consistency(text_list_1, text_list_2)
        self.text_list_1 = text_list_1
        self.text_list_2 = text_list_2
        self.current_text_index = 0

        self.indices = random.sample(range(self.n), self.n)

        w_width = window.winfo_width()
        w_height = window.winfo_height()

        background_image = Image.open("figs/kanji.png")
        background_image.putalpha(50)
        self.background_photo = ImageTk.PhotoImage(background_image)

        self.window.geometry(f"{background_image.width}x{background_image.height}")

        self.label = tk.Label(
            window, 
            compound='center',
            text=f"{self.text_list_1[self.indices[self.current_text_index]]}", 
            font=("Helvetica", 60),
            image=self.background_photo,
        )
        self.label.pack(expand=True, fill='both', anchor='center')
        self.current_text_index += 1
        self.change_text()
        self.change_text()

        self.bind_events()

    def check_consistency(self,list1,list2):
        n1 = len(list1)
        n2 = len(list2)
        if n1 == n2:
            return n1
        else:
            raise(f"Lists not the same length.\n{n1}!={n2}")

    def change_text(self):
        if self.current_text_index % 2 == 0:
            text = self.text_list_1[self.indices[self.current_text_index // 2 % len(self.text_list_1)]]
        else:
            text = self.text_list_2[self.indices[self.current_text_index // 2 % len(self.text_list_2)]]

        text_width = max(map(lambda x: len(x), text.split("\n")))

        # Adjust the width threshold based on your window size and layout
        width_threshold = 300

        if text_width > 12 or (contains_japanese(text) and text_width > 6) or contains_both(text):
            if " " in text:
                text = "\n".join(text.split())
            else:
                midpoint = len(text)//2
                text = "\n".join([text[:midpoint],text[midpoint:]])
            if "/" in text:
                text = "/\n".join(text.split("/"))

        self.label.config(text=text)
        self.current_text_index += 1

    def on_window_click(self, event):
        self.change_text()

    def bind_events(self):
        self.window.bind("<Button-1>", self.on_window_click)
        self.window.bind("<space>", self.on_window_click)
        self.window.bind("<Control-w>", self.close_window)
        self.window.bind("<BackSpace>", self.change_back)

    def close_window(self, event):
        self.window.destroy()

    def change_back(self, event):
        self.label.destroy()
        self.window.destroy()
        create_window_with_looping_text()
        # start = StartScreen(self.window)

def create_window_with_looping_text():
    window = tk.Tk()
    window.title("Anki")

    # Make the window square and a bit bigger
    window.geometry("523x523")

    start = StartScreen(window)

    window.mainloop()

def sort_word_files():
    for file in ["言葉","漢字"]:
        with open(f"word_files/{file}") as f:
            lines = f.readlines()
        lines.sort()
        with open(f"word_files/{file}", "w") as f:
            f.write("".join(lines))

def main():
    create_window_with_looping_text()

if __name__ == '__main__':
    main()
