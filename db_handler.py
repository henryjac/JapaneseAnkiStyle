import random
import re
import mysql.connector
import os
import settings

def get_db():
    conn = mysql.connector.connect(
        host="localhost",
        user=os.environ.get("JAP_ANKI_USR"),
        password=os.environ.get("JAP_ANKI_PWD"),
        database="familiarity",
    )

    cursor = conn.cursor()
    return conn, cursor

def create_table(conn, cursor, table):
    query = f"""
    CREATE TABLE IF NOT EXISTS {table} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        word VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci UNIQUE,
        translation VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci UNIQUE,
        familiarity INT,
        probability DECIMAL(6,5),
        game VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
        UNIQUE KEY (word, game)
    );
    """
    cursor.execute(query)

def add_to_table(conn, cursor, word, familiarity_update, table, game_type):
    familiarity = max(1,familiarity_update + old_familiarity(conn, cursor, word, table))
    query = f"""
        UPDATE {table}
        SET familiarity = GREATEST(1,%s + familiarity)
        WHERE word = %s
    """
    data = (familiarity_update, word)
    cursor.execute(query, data)
    conn.commit()

def initial_add_to_table(conn, cursor, word, translation, familiarity_update, game_type, table):
    familiarity = max(1,familiarity_update + old_familiarity(conn, cursor, word, table))
    if "<-" in game_type:
        word = re.sub(r' \(.*\)', '', word)
    query = f"""
        INSERT INTO {table} (word, translation, familiarity, game)
        VALUES (%s, %s, 1, %s)
        ON DUPLICATE KEY UPDATE familiarity = {familiarity};
    """
    data = (word, translation, game_type)
    cursor.execute(query, data)
    conn.commit()

def calculate_probabilities(frequency_list):
    total_frequency = sum(frequency_list)
    rev_probs = [total_frequency / freq for freq in frequency_list]
    sum_probs = sum(rev_probs)
    probs = [prob / sum_probs for prob in rev_probs]

    return probs

def update_probabilities(conn, cursor, table, game):
    query = f"""
        SELECT familiarity, word
        FROM {table}
        WHERE game = %s AND familiarity <= 15
    """
    cursor.execute(query, (game,))
    res = cursor.fetchall()

    probs = calculate_probabilities(list(map(lambda x: x[0], res)))

    for prob,word in zip(probs, map(lambda x: x[1], res)):
        query = f"""
            UPDATE {table}
            SET probability = %s
            WHERE game = %s AND word = %s
        """
        cursor.execute(query, (prob, game, word))
        conn.commit()

def old_familiarity(conn, cursor, word, table):
    query = f"""
        SELECT familiarity FROM {table} WHERE word = %s
    """
    cursor.execute(query, (word,))
    try:
        return cursor.fetchone()[0]
    except TypeError:
        return 0

def remove_changed(conn, cursor, og_table, check_table, game):
    """
    Remove from og_table for where check_table doesnt have it
    """
    query = f"""
        DELETE FROM {og_table}
        WHERE word NOT IN
        (SELECT word FROM {check_table})
        AND game = (%s)
    """
    cursor.execute(query, (game,))
    conn.commit()
    query = f"""
        DROP TABLE {check_table}
    """
    cursor.execute(query)
    conn.commit()

def sum_familiarities(conn, cursor, table):
    query = f"SELECT SUM(familiarity) FROM {table}"
    cursor.execute(query)
    tot = cursor.fetchone()[0]
    return tot

def create_familiarities(conn, cursor, text_list_1, text_list_2, game_type):
    table = settings.Global.table
    temp_table = "tmp"
    create_table(conn, cursor, table)
    create_table(conn, cursor, temp_table)
    for text1,text2 in zip(text_list_1, text_list_2):
        initial_add_to_table(conn, cursor, text1, text2, 0, game_type, table)
        initial_add_to_table(conn, cursor, text1, text2, 0, game_type, temp_table)
    remove_changed(conn, cursor, table, temp_table, game_type)
    update_probabilities(conn, cursor, table, game_type)

def get_translation(conn, cursor, word, table):
    query = f"""
        SELECT translation
        FROM {table}
        WHERE word = %s
    """
    data = (word,)
    cursor.execute(query, data)
    try:
        return cursor.fetchone()[0]
    except TypeError:
        return "No more words left to learn."

def select_random_with_probability(conn, cursor, table, game_type):
    # Generate a random number between 0 and 1
    random_value = random.random()

    query = f"""
        SELECT word, probability
        FROM {table}
        WHERE game = %s AND familiarity <= 15
    """
    data = (game_type,)
    cursor.execute(query, data)
    result = cursor.fetchall()
    words = list(map(lambda x: x[0], result))
    probabilities = list(map(lambda x: float(x[1]), result))
    
    try:
        choice = random.choices(words, weights=probabilities)[0]
    except:
        return "No more words left to learn."
    return choice

def main():
    conn, cursor = get_db()
    table = "test"
    create_table(conn, cursor, table)
    add_to_table(conn, cursor, "漢字", "かんじ", 2, "my_file", table)

if __name__ == '__main__':
    main()
