import db_handler
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

def format_text(text):
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
    return text

def sort_word_files():
    for file in ["言葉","漢字"]:
        with open(f"word_files/{file}") as f:
            lines = f.readlines()
        lines.sort()
        with open(f"word_files/{file}", "w") as f:
            f.write("".join(lines))
