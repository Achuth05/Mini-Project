import os
from dotenv import load_dotenv

load_dotenv()

os.environ["OPENAI_MODEL_NAME"] = "gpt-4"

from crewai import Agent, Task, Crew, Process, LLM

from .tools import (
    get_faculty_tool,
    get_subjects_tool,
    get_allotments_tool,
    get_rooms_tool,
    get_timeslots_tool,
    get_batches_tool,
    get_availability_tool,
    check_conflict_tool,
    save_timetable_tool
)

generation_status = {}


def _build_llm():
    return LLM(
        model=f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT')}",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version="2024-02-01"
    )
def _run_crew_for_semester(generation_id: str, semester: int):
    llm = _build_llm()

    # ── AGENTS ───────────────────────────────────────────────────────────────
    data_collector = Agent(
        role="University Data Specialist",
        goal=f"Extract every single subject allotment and all 30 time slots for semester {semester}.",
        backstory="You are precise. You ensure that no allotment or time slot is left behind.",
        tools=[get_faculty_tool, get_subjects_tool, get_allotments_tool, get_rooms_tool, 
               get_timeslots_tool, get_batches_tool, get_availability_tool],
        llm=llm,
        verbose=True
    )

    scheduler = Agent(
        role="Weekly Scheduling Engine",
        goal=f"Assign all 35+ semester {semester} allotments to the 30-slot weekly grid.",
        backstory="A high-performance logic engine. You view the week as a matrix of 5 days x 6 slots. "
                  "You prioritize completing the schedule for Batch A, then Batch B, then C, then CB.",
        tools=[check_conflict_tool],
        llm=llm,
        verbose=True,
        max_iter=40, # High iteration count to allow for the full list
        memory=True
    )

    reporter = Agent(
        role="Final Auditor",
        goal="Format the complete multi-batch schedule into a single JSON array.",
        backstory="You double-check that every entry has a valid UUID for subject and faculty.",
        llm=llm,
        verbose=True
    )

    # ── TASKS ─────────────────────────────────────────────────────────────────
    collect_task = Task(
        description=(
            "1. Fetch the full list of allotments.\n"
            "2. Fetch all 30 time slots (Period 1-6 for Mon-Fri).\n"
            "3. Identify all distinct batches (e.g., A, B, C, CB)."
        ),
        expected_output="A structured dataset containing the entire scheduling requirement.",
        agent=data_collector
    )

    schedule_task = Task(
        description=(
            f"Generate a MASSIVE weekly schedule for Generation ID: {generation_id}.\n\n"
            "INSTRUCTIONS:\n"
            "- You have 30 slots available (Monday-Friday, Slots 1-6).\n"
            "- You must attempt to schedule EVERY allotment provided in the data.\n"
            "- FOR EACH BATCH (A, B, C, CB): Assign their specific subjects to empty slots in the week.\n"
            "- Practical/Lab classes should take priority for 'LAB' rooms.\n"
            "- If a slot is taken for a room or faculty, move to the next available slot.\n"
            "- DO NOT provide a sample. Provide the COMPLETE list of 30+ scheduled items."
        ),
        expected_output="A complete list of ALL scheduled entries across all days and batches.",
        agent=scheduler,
        context=[collect_task]
    )

    report_task = Task(
        description=(
            "Compile every single entry into one 'schedule' list in JSON.\n"
            "Verify that total_scheduled is approximately 30-40 entries.\n"
            "The JSON must be the only output."
        ),
        expected_output="A raw JSON object with 'schedule' and 'summary' keys.",
        agent=reporter,
        context=[schedule_task]
    )

    crew = Crew(
        agents=[data_collector, scheduler, reporter],
        tasks=[collect_task, schedule_task, report_task],
        process=Process.sequential,
        verbose=True
    )

    return crew.kickoff()
def run_scheduling_crew(generation_id: str, semester: int = 6):
    generation_status[generation_id] = "running"
    try:
        result = _run_crew_for_semester(generation_id, semester=semester)
        generation_status[generation_id] = "completed"
        print(f"\n[Orchestrator] ✅ Crew completed for generation {generation_id}")
        print(f"[Orchestrator] Result: {result}")
        return {"status": "completed", "generation_id": generation_id}

    except Exception as e:
        generation_status[generation_id] = f"failed: {str(e)}"
        print(f"\n[Orchestrator] ❌ Failed: {str(e)}")
        raise e