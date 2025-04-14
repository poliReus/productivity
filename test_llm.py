from llm_utils import generate_summary_and_score

# Task simulate
sample_tasks = [
    {"task": "Allenamento mattutino", "completed": True},
    {"task": "Studio individuale", "completed": True},
    {"task": "Pulizie di casa", "completed": False}
]

# Domanda: stiamo ignorando il DB per test, quindi mockiamo anche il questionario
from models.database import get_questionnaire_questions

def mock_questionnaire():
    return {
        "Hai fatto attività fisica?": "True",
        "Hai mangiato sano oggi?": "False",
        "Ti sei sentito motivato?": "True",
        "Hai dormito bene ieri notte?": "False"
    }

# Override temporaneo della funzione originale (monkey patch)
import models.database
models.database.get_questionnaire_answers_for_today = mock_questionnaire

# Esegui il test
if __name__ == "__main__":
    summary, score = generate_summary_and_score("2025-04-14", sample_tasks)
    print("\n📝 Riepilogo generato:")
    print(summary)
    print("\n📊 Punteggio:", score, "/10")
