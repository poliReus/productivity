from llama_cpp import Llama
from models.database import get_questionnaire_answers_for_today
from datetime import datetime
import os
import re

def estrai_punteggio(text):
    # Cerca un numero tra 1 e 10 vicino a "valutazione", "punteggio", ecc.
    patterns = [
        r"valutazione[:\s]*([1-9]|10)",
        r"punteggio[:\s]*([1-9]|10)",
        r"\b([1-9]|10)[/ su]{1,3}10\b",     # es. 8/10, 8 su 10
        r"ti do un[:\s]*([1-9]|10)",
        r"\bmeriti un[:\s]*([1-9]|10)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None  # Se non trova nulla

# Configura percorso modello e tokenizer (modifica se necessario)
MODEL_PATH = "/Users/reus3111/Desktop/productivity/llm_models/Nous-Hermes-2-Mistral-7B-DPO.Q5_K_M.gguf"

# Inizializza il modello (solo una volta, fuori dalla funzione)
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=1024,
    verbose=True
)

def generate_summary_and_score(date, tasks):
    # Prepara sezioni del prompt
    completed = [t["task"] for t in tasks if t["completed"]]
    not_completed = [t["task"] for t in tasks if not t["completed"]]

    questionnaire = get_questionnaire_answers_for_today()
    q_section = "\n".join([f"- {q}: {'Sì' if a == 'True' else 'No'}" for q, a in questionnaire.items()])

    # Prompt da inviare al modello
    prompt = f"""
Oggi è il giorno {date}.

 Task completate:
{chr(10).join(f"- {t}" for t in completed) if completed else "Nessuna"}

 Task non completate:
{chr(10).join(f"- {t}" for t in not_completed) if not_completed else "Nessuna"}

📋 Risposte al questionario (sì/no):
{q_section if q_section else "Nessuna risposta"}

🔎 Obiettivo:
Scrivi un riepilogo motivazionale della giornata, tenendo conto delle task e delle risposte al questionario.
Le risposte al questionario sono importanti tanto quanto le task.
Includi anche una valutazione da 1 a 10 della giornata, come commento discorsivo e infine scrivendo un punteggio nel formato Punteggio:x/10
Rispondi in modo naturale, empatico e ispirante.
""".strip()

    try:
        print(prompt)
        print("🧠 Invio prompt al modello...\n")
        output = llm(prompt, max_tokens=512)
        response_text = output["choices"][0]["text"].strip()

        # Salva il testo generato in un file
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
