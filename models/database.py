import sqlite3
import os
from datetime import datetime
import pandas as pd

DB_PATH = 'data/daily_data.db'
QUESTIONARIO_PATH = 'data/questionario.xlsx'


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Tasks giornaliere
    c.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                date TEXT NOT NULL
            )
        ''')

    # Risposte questionario
    c.execute('''
        CREATE TABLE IF NOT EXISTS questionnaire (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT,
            date TEXT NOT NULL
        )
    ''')

    # Riepilogo giornaliero + valutazione
    c.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                summary TEXT,
                score INTEGER,          -- Valutazione dell’LLM
                personal_score INTEGER  -- Valutazione personale
            )
        ''')

    conn.commit()
    conn.close()


def get_today():
    return datetime.now().strftime('%Y-%m-%d')


def add_task(task):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (task, date) VALUES (?, ?)", (task, get_today()))
    conn.commit()
    conn.close()


def get_tasks_for_today():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, task, completed FROM tasks WHERE date = ?", (get_today(),))
    tasks = c.fetchall()
    conn.close()
    return [{"id": t[0], "task": t[1], "completed": bool(t[2])} for t in tasks]


def complete_task(task_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def save_questionnaire(answers):
    df = pd.read_excel(QUESTIONARIO_PATH)
    id_to_domanda = dict(zip(df["ID"], df["Promessa"]))
    today = get_today()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for qid, val in answers.items():
        domanda = id_to_domanda.get(qid, qid)
        c.execute("INSERT INTO questionnaire (question, answer, date) VALUES (?, ?, ?)",
                  (domanda, val, today))

    conn.commit()
    conn.close()



def get_questionnaire_questions():
    df = pd.read_excel(QUESTIONARIO_PATH)
    df = df.dropna(subset=["Promessa"])
    return df.to_dict(orient="records")



def save_day_summary(date, filepath, score, personal_score=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO summaries (date, summary, score, personal_score)
        VALUES (?, ?, ?, ?)
    ''', (date, filepath, score, personal_score))
    conn.commit()
    conn.close()



def get_all_summaries():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT date, summary, score, personal_score FROM summaries ORDER BY date DESC")
    results = c.fetchall()
    conn.close()

    formatted = []
    for date, filepath, score, personal_score in results:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except:
            content = "[Errore nel caricamento del file]"
        formatted.append({
            "date": date,
            "summary": content,
            "score": score,
            "personal_score": personal_score
        })
    return formatted

def get_average_personal_score():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT AVG(personal_score) FROM summaries WHERE personal_score IS NOT NULL")
    avg = c.fetchone()[0]
    conn.close()
    return round(avg, 2) if avg is not None else 0


def get_average_score():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT AVG(score) FROM summaries")
    avg = c.fetchone()[0]
    conn.close()
    return round(avg, 2) if avg is not None else 0

def get_questionnaire_answers_for_today():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT question, answer FROM questionnaire WHERE date = ?", (get_today(),))
    results = c.fetchall()
    conn.close()
    return {q: a for q, a in results}

