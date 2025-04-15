import sqlite3

from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import os
from models.database import init_db, add_task, get_tasks_for_today, complete_task, delete_task, \
    save_questionnaire, save_day_summary, get_all_summaries, get_average_score, get_average_personal_score, \
    get_questionnaire_questions, DB_PATH, add_study_session, get_study_sessions_for_today,  get_study_sessions_by_date, delete_tasks_for_today, get_questionnaire_answers_for_today
from llm_utils import generate_summary_and_score

app = Flask(__name__)
init_db()

@app.route('/')
def index():
    today = datetime.now().strftime('%Y-%m-%d')
    tasks = get_tasks_for_today()
    questions = get_questionnaire_questions()
    risposte = get_questionnaire_answers_for_today()

    # Recupera valutazione personale
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT personal_score FROM summaries WHERE date = ?", (today,))
    row = c.fetchone()
    personal_score = row[0] if row else ""
    for q in questions:
        q["risposta"] = risposte.get(f'{q["ID"]}')  # 'True', 'False', oppure None
    return render_template("index.html", tasks=tasks, today=today,
                           questions=questions, risposte=risposte,
                           personal_score=personal_score)

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

    tasks = get_tasks_for_today()
    summary, score = generate_summary_and_score(today, tasks)

    # Salva riepilogo
    save_day_summary(today, summary, score)

    # Solo reset delle task, non toccare questionario né studio
    delete_tasks_for_today()

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
    delete_tasks_for_today()
    return redirect(url_for('history'))


@app.route('/studio', methods=['GET', 'POST'])
def studio():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        duration = int(request.form['duration'])
        add_study_session(title, description, duration)
        return redirect(url_for('studio'))

    sessions = get_study_sessions_for_today()
    return render_template("study.html", sessions=sessions)



@app.route('/history/<selected_date>')
def history_by_date(selected_date):
    summaries = get_all_summaries()
    selected = next((s for s in summaries if s["date"] == selected_date), None)
    sessions = get_study_sessions_by_date(selected_date)
    return render_template("history.html", summaries=summaries,
                           average=get_average_score(),
                           average_personal=get_average_personal_score(),
                           selected_summary=selected,
                           selected_sessions=sessions,
                           selected_date=selected_date)


if __name__ == '__main__':
    app.run(debug=True)
