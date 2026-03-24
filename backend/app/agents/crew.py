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
        role="Data Collector",
        goal=f"Fetch all scheduling data for semester {semester}.",
        backstory="You fetch university scheduling data from tools.",
        tools=[
            get_faculty_tool,
            get_subjects_tool,
            get_allotments_tool,
            get_rooms_tool,
            get_timeslots_tool,
            get_batches_tool,
            get_availability_tool
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5
    )

    scheduler = Agent(
        role="Scheduler",
        goal=f"Assign time slots and rooms to all allotments for semester {semester} without conflicts.",
        backstory="You build conflict-free timetables using available data.",
        tools=[check_conflict_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=20
    )

    reporter = Agent(
        role="Reporter",
        goal="Save timetable entries to database.",
        backstory="You save timetable entries to the database.",
        tools=[save_timetable_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5
    )

    # ── TASKS ─────────────────────────────────────────────────────────────────

    collect_task = Task(
        description=(
            f"Call these tools in order and return all results as one JSON object:\n"
            f"1. get_faculty_tool(query='')\n"
            f"2. get_subjects_tool(query='')\n"
            f"3. get_allotments_tool(semester='{semester}')\n"
            f"4. get_rooms_tool(query='')\n"
            f"5. get_timeslots_tool(query='')\n"
            f"6. get_batches_tool(semester='{semester}')\n"
            f"7. get_availability_tool(query='')"
        ),
        expected_output="JSON with keys: faculty, subjects, allotments, rooms, time_slots, batches, availability.",
        agent=data_collector
    )

    schedule_task = Task(
    description=(
        f"You must schedule EVERY SINGLE allotment in the list. There are 35 allotments total.\n"
        f"Generation ID: {generation_id}\n\n"
        f"For EACH allotment:\n"
        f"1. Get faculty_id, batch_id, subject_id from allotments list\n"
        f"2. Pick a room: LAB room if role=practical, classroom if role=lecture\n"
        f"3. Pick a time_slot_id from time_slots list\n"
        f"4. Call check_conflict_tool with real UUIDs\n"
        f"5. If conflict=false → add to scheduled list\n"
        f"6. If conflict=true → try next time_slot_id\n"
        f"7. Move to next allotment\n"
        f"Repeat until ALL 35 allotments are processed.\n"
        f"Do not stop after 1 entry. Schedule everything."


        f"IMPORTANT: Each allotment has these fields:\n"
        f"  - id: the allotment's own ID (DO NOT use this as subject_id)\n"
        f"  - subject_id: use THIS as subject_id in your output\n"
        f"  - faculty_id: use this as faculty_id\n"
        f"  - batch_id: use this as batch_id\n"
        f"  - role: use this as role\n"
    ),
    expected_output=(
        "JSON with scheduled list containing ALL 35 allotments, "
        "unscheduled list for any that failed, total_scheduled count."
    ),
    agent=scheduler,
    context=[collect_task]
)

    report_task = Task(
        description=(
            f"Take ALL entries from the scheduled list in the previous task.\n"
            f"Call save_timetable_tool with the complete entries as a JSON string.\n"
            f"Each entry needs: subject_id, faculty_id, room_id, time_slot_id, batch_id, generation_id, role.\n"
            f"DO NOT skip any entries. Save everything.\n"
            f"Return save summary with count of saved entries."
        ),
        expected_output="JSON with saved count, generation_id, status=draft.",
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