import sqlite3

from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import os
from models.database import init_db, add_task, get_tasks_for_today, complete_task, delete_task, \
    save_questionnaire, save_day_summary, get_all_summaries, get_average_score, get_average_personal_score, \
    get_questionnaire_questions, DB_PATH
from llm_utils import generate_summary_and_score

app = Flask(__name__)
init_db()

@app.route('/')
def index():
    today = datetime.now().strftime('%Y-%m-%d')
    tasks = get_tasks_for_today()
    questions = get_questionnaire_questions()
    return render_template("index.html", tasks=tasks, today=today, questions=questions)

@app.route('/add_task', methods=['POST'])
def add_task_route():
    data = request.get_json()
    task_text = data.get("task")
    if task_text:
        add_task(task_text)
    return jsonify(success=True)

@app.route('/complete_task/<int:task_id>', methods=['POST'])
def complete_task_route(task_id):
    complete_task(task_id)
    return jsonify(success=True)

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task_route(task_id):
    delete_task(task_id)
    return jsonify(success=True)

@app.route('/submit_questionnaire', methods=['POST'])
def submit_questionnaire():
    data = request.form
    answers = {key: data[key] for key in data}
    save_questionnaire(answers)
    return redirect(url_for('index'))

@app.route('/history')
def history():
    summaries = get_all_summaries()
    avg_llm = get_average_score()
    avg_personal = get_average_personal_score()
    return render_template("history.html", summaries=summaries,
                           average=avg_llm, average_personal=avg_personal)

# ✅ API chiamata dallo script notturno (daily_reset.py)
@app.route('/run_daily_reset')
def run_daily_reset():
    today = datetime.now().strftime('%Y-%m-%d')
    # Prende tutte le task + questionario
    tasks = get_tasks_for_today()
    summary, score = generate_summary_and_score(today, tasks)
    save_day_summary(today, summary, score)
    return jsonify({"summary": summary, "score": score})
@app.route('/submit_personal_score', methods=['POST'])
def submit_personal_score():
    score = int(request.form.get("personal_score"))
    today = datetime.now().strftime('%Y-%m-%d')
    save_day_summary(today, f"data/riepilogo_{today}.txt", None, score)
    return redirect(url_for('index'))
@app.route('/genera_analisi_ora', methods=['POST'])
def genera_analisi_ora():
    today = datetime.now().strftime('%Y-%m-%d')
    tasks = get_tasks_for_today()
    filepath, score = generate_summary_and_score(today, tasks)

    # Recupera eventuale punteggio personale già inserito
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT personal_score FROM summaries WHERE date = ?", (today,))
    row = c.fetchone()
    personal_score = row[0] if row else None
    conn.close()

    save_day_summary(today, filepath, score, personal_score)
    return redirect(url_for('history'))


if __name__ == '__main__':
    app.run(debug=True)
