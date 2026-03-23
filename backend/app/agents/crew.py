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

    # ── AGENTS (ultra-short backstories to save tokens) ──────────────────────

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

    # ── TASKS (minimal descriptions to save tokens) ───────────────────────────

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
            f"Using the collected data, schedule all allotments for semester {semester}.\n"
            f"Generation ID: {generation_id}\n\n"
            f"Rules:\n"
            f"- Labs (P>0, L=0): assign 2 consecutive slots same day in a LAB room\n"
            f"- Lectures (L>0): assign slots in classroom rooms\n"
            f"- Before each assignment call check_conflict_tool with JSON: "
            f'{{\"faculty_id\":\"X\",\"room_id\":\"Y\",\"time_slot_id\":\"Z\",\"batch_id\":\"B\",\"generation_id\":\"{generation_id}\"}}\n'
            f"- If conflict=true try next slot\n"
            f"- Return all scheduled entries as a JSON list"
        ),
        expected_output=(
            "JSON object with:\n"
            "- scheduled: list of {subject_id, faculty_id, room_id, time_slot_id, batch_id, generation_id, role}\n"
            "- unscheduled: list of failed allotment ids\n"
            "- total_scheduled: int"
        ),
        agent=scheduler,
        context=[collect_task]
    )

    report_task = Task(
        description=(
            f"Take the scheduled list from previous task.\n"
            f"Call save_timetable_tool with the entries as a JSON string.\n"
            f"Each entry needs: subject_id, faculty_id, room_id, time_slot_id, batch_id, generation_id, role.\n"
            f"Return save summary."
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

    crew.kickoff()


def run_scheduling_crew(generation_id: str):
    generation_status[generation_id] = "running"
    try:
        _run_crew_for_semester(generation_id, semester=2)
        generation_status[generation_id] = "completed"
    except Exception as e:
        generation_status[generation_id] = f"failed: {str(e)}"
        raise e