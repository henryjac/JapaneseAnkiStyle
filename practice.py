import random
import inspect

alphabet_length = 104
hiragana = 'ひらがな'
katakana = 'カタカナ'
kanji = '漢字'
mix = f'{hiragana} / {katakana} / {kanji}'
opposite_alphabet = {hiragana:katakana,katakana:hiragana,kanji:hiragana}

def get_jap_and_lat(alphabet):
    with open(alphabet) as f:
        lines = f.readlines()
    jap = [""]*len(lines)
    lat = [""]*len(lines)
    for i in range(len(lines)):
        jap[i], lat[i] = lines[i].split()
    return jap, lat

def alphabet_dict(alphabet, choice):
    hiragana_alphabet_jap, hiragana_alphabet_lat = get_jap_and_lat(hiragana)
    katakana_alphabet_jap, katakana_alphabet_lat = get_jap_and_lat(katakana)
    kanji_alphabet_jap, kanji_alphabet_lat = get_jap_and_lat(kanji)
    
    if choice == "r":
        hiragana_alphabet = dict(map(lambda i,j: (i,j), hiragana_alphabet_jap, hiragana_alphabet_lat))
        katakana_alphabet = dict(map(lambda i,j: (i,j), katakana_alphabet_jap, katakana_alphabet_lat))

        new_kanji_alphabet_lat = [""]*len(kanji_alphabet_lat)
        for i,hiraganas in enumerate(kanji_alphabet_lat):
            romaji = []
            j = 0
            while j < len(hiraganas): 
                hiragana_letter = hiraganas[j]
                try:
                    romaji.append(hiragana_alphabet[hiragana_letter])
                except KeyError:
                    hiragana_letter = hiraganas[j-1:j+1]
                    romaji.pop()
                    romaji.append(hiragana_alphabet[hiragana_letter])
                j += 1
            new_kanji_alphabet_lat[i] = "".join(romaji)
        kanji_alphabet_lat = new_kanji_alphabet_lat
        kanji_alphabet = dict(map(lambda i,j: (i,j), kanji_alphabet_jap, kanji_alphabet_lat))
    else:
        hiragana_alphabet = dict(map(lambda i,j: (i,j), hiragana_alphabet_jap, katakana_alphabet_jap))
        katakana_alphabet = dict(map(lambda i,j: (i,j), katakana_alphabet_jap, hiragana_alphabet_jap))
        kanji_alphabet = dict(map(lambda i,j: (i,j), kanji_alphabet_jap, kanji_alphabet_lat))

    if alphabet == mix:
        hiragana_alphabet.update(katakana_alphabet)
        hiragana_alphabet.update(kanji_alphabet)
        dict_alphabet = hiragana_alphabet
    elif alphabet == hiragana:
        dict_alphabet = hiragana_alphabet
    elif alphabet == katakana:
        dict_alphabet = katakana_alphabet
    elif alphabet == kanji:
        dict_alphabet = kanji_alphabet
    return dict_alphabet

def finish_game(score, total, alphabet):
    add_score(score, total, alphabet)
    print(f"Well done!\nScore: {score}/{total}")
    exit()

def add_score(score, total, alphabet):
    if total <= 2:
        return
    with open("scoring", "a") as f:
        f.write(f"{score} {total} {''.join(alphabet.split())}")
        f.write("\n")

def choose_type(alphabet):
    if alphabet == mix:
        print(" -> romaji (r) or -> japanese (j)")
    else:
        print(
            f"{alphabet} -> romaji (r)\nor\n"
            f"{alphabet} -> {opposite_alphabet[alphabet]} (j)"
        )
    choice = input()
    if choice not in ["r","j"]:
        print("Not a valid choice, going with j")
        return "j"
    return choice

def jap_chars_to_lat(jap_chars, jap2lat_dict):
    lat_chars = [""]*len(jap_chars)
    for i,char in enumerate(jap_chars):
        lat_chars[i] = jap2lat_dict[char]
    return lat_chars

def practice(alphabet):
    choice = choose_type(alphabet)
    print_practice(alphabet, choice)

    jap2lat = alphabet_dict(alphabet, choice)

    total_played = 0
    total_score = 0
    n_chars = len(jap2lat)
    for i in range(30):
        try:
            n = random.randrange(5,10)
            jap_chars = []
            lat_chars = []
            chars = random.sample(list(jap2lat.items()),n)
            jap = "".join(map(lambda x: x[0], chars))
            lat = "".join(map(lambda x: x[1], chars))
            print(jap)
            lat_guess = input()
            if lat_guess != lat:
                if lat_guess == "":
                    finish_game(total_score,total_played,alphabet)
                print(f"Wrong! \n\tYou wrote:  '{lat_guess}'\n\tCorrect is: '{lat}'")
            else:
                print("Correct!")
                total_score += 1
            total_played += 1
        except UnicodeDecodeError:
            print("Input error, continuing.")
            continue
        except KeyboardInterrupt:
            finish_game(total_score,total_played,alphabet)
    finish_game(total_score,total_played,alphabet)

def print_practice(fnc, choice):
    if choice == "j" and fnc != mix:
        print(f"Starting {fnc} -> {opposite_alphabet[fnc]} practice!")
    elif choice == "j":
        print(f"Starting {fnc} -> {hiragana} practice!")
    else:
        print(f"Starting {fnc} -> romaji practice!")

def get_practice(first=True):
    print(f"What do you want to practice?\n1: {hiragana}\n2: {katakana}\n3: {kanji}\n4: {mix}")
    choice = input()
    if choice == "1":
        practice(hiragana)
    elif choice == "2":
        practice(katakana)
    elif choice == "3":
        practice(kanji)
    elif choice == "4":
        practice(mix)
    elif first:
        print("Choose a valid number (1,2,3,4)")
        get_practice(False)
    else:
        print("Nothing chosen, Exiting...")

def main():
    get_practice()

if __name__ == '__main__':
    main()
