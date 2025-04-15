from llama_cpp import Llama
from models.database import get_questionnaire_answers_for_today, get_study_sessions_by_date, get_questionnaire_questions

import pandas
import os
import re



def estrai_punteggio(text):
    patterns = [
        r"valutazione[:\s]*([1-9]|10)",
        r"punteggio[:\s]*([1-9]|10)",
        r"\b([1-9]|10)[/ su]{1,3}10\b",
        r"ti do un[:\s]*([1-9]|10)",
        r"\bmeriti un[:\s]*([1-9]|10)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


MODEL_PATH = "/Users/reus3111/Desktop/productivity/llm_models/Nous-Hermes-2-Mistral-7B-DPO.Q5_K_M.gguf"

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=1024,
    verbose=True
)


def format_questionnaire_with_questions():
    raw_answers = get_questionnaire_answers_for_today()  # {ID: risposta}
    all_questions = get_questionnaire_questions()        # [{'ID': '1', 'Promessa': '...'}, ...]

    if not raw_answers:
        return "Nessuna risposta al questionario."

    id_to_question = {str(q["ID"]): q["Promessa"] for q in all_questions}

    formatted = "\n".join([
        f"- {id_to_question.get(str(qid), f'Domanda {qid}')}:" +
        f" {'✅ Sì' if val == 'True' else '❌ No'}"
        for qid, val in raw_answers.items()
    ])
    return formatted


def format_study_sessions(date):
    sessions = get_study_sessions_by_date(date)
    if not sessions:
        return "Nessuna sessione registrata."

    formatted = "\n".join([
        f"- {title} ({duration} min): {description}"
        for title, description, duration in sessions
    ])
    return formatted


def generate_summary_and_score(date, tasks):
    completed = [t["task"] for t in tasks if t["completed"]]
    not_completed = [t["task"] for t in tasks if not t["completed"]]

    q_section = format_questionnaire_with_questions()
    studio_section = format_study_sessions(date)

    prompt = f"""
📅 Oggi è il giorno {date}.

✅ Task completate:
{chr(10).join(f"- {t}" for t in completed) if completed else "Nessuna"}

❌ Task non completate:
{chr(10).join(f"- {t}" for t in not_completed) if not_completed else "Nessuna"}

📋 Questionario (Domanda + Risposta):
{q_section}

📚 Sessioni di studio:
{studio_section}

🔎 Obiettivo:
Scrivi un riepilogo motivazionale della giornata, tenendo conto di tutte le informazioni: task, risposte al questionario, sessioni di studio.
Le risposte al questionario e lo studio sono importanti tanto quanto le task.
Includi anche una valutazione da 1 a 10 della giornata, come commento discorsivo e infine scrivendo un punteggio nel formato Punteggio:x/10.
Rispondi in modo naturale, empatico e ispirante.
""".strip()

    try:
        print(prompt)
        print("🧠 Invio prompt al modello...\n")
        output = llm(prompt, max_tokens=512)
        response_text = output["choices"][0]["text"].strip()

        os.makedirs("data", exist_ok=True)
        filename = f"data/riepilogo_{date}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response_text)

        print("✅ Riepilogo salvato in:", filename)
        score = estrai_punteggio(response_text)
        return filename, score

    except Exception as e:
        print("❌ Errore durante la generazione:", e)
        return "Errore durante la generazione", None
