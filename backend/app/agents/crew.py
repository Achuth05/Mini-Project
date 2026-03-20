import os
from dotenv import load_dotenv

load_dotenv()

os.environ["OPENAI_API_KEY"] = "dummy-not-used"

# Shared status dict — imported by timetable.py
generation_status = {}


def run_scheduling_crew(generation_id: str, semester: int = 2):
    """
    Runs the OR-Tools scheduler directly.
    No LLM calls. CrewAI agents kept for demo purposes only.
    """
    from .tools import _run_scheduler

    generation_status[generation_id] = "running"
    print(f"[Crew] Starting scheduling for generation_id={generation_id}")

    try:
        result = _run_scheduler(generation_id, semester=semester)
        generation_status[generation_id] = "completed"
        print(f"[Crew] Completed: {result}")
        return result

    except Exception as e:
        generation_status[generation_id] = f"failed: {str(e)}"
        print(f"[Crew] Failed: {str(e)}")
        raise e