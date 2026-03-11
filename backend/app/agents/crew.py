import os
from dotenv import load_dotenv

# MUST be first before anything else
load_dotenv()

# Disable OpenAI requirement
os.environ["OPENAI_API_KEY"] = "dummy-not-used"
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
        model="groq/llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY")
    )

def _run_crew_for_semester(generation_id: str, semester: int):
    """Runs the full crew pipeline for one semester only to stay within token limits."""

    llm = _build_llm()

    data_collector = Agent(
        role="Data Collection Specialist",
        goal=f"Fetch scheduling data for semester {semester} only",
        backstory=f"""You are an expert at gathering scheduling data. 
        You fetch faculty, subjects, allotments, rooms, time slots and batches 
        for semester {semester} and return them as clean structured JSON.""",
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
        allow_delegation=False
    )

    constraint_analyzer = Agent(
        role="Scheduling Constraint Analyst",
        goal=f"Analyze constraints for semester {semester} data only",
        backstory=f"""You are an expert in academic scheduling rules for semester {semester}. 
        You identify hard and soft constraints from the data provided.""",
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    scheduler = Agent(
        role="Timetable Scheduling Expert",
        goal=f"Schedule all subjects for semester {semester} without conflicts",
        backstory=f"""You are an expert in constraint satisfaction and academic timetabling 
        for semester {semester}. You assign subjects to time slots and rooms 
        following all constraints.""",
        tools=[check_conflict_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    validator = Agent(
        role="Timetable Validation Expert",
        goal=f"Validate the generated timetable for semester {semester}",
        backstory=f"""You are an expert at detecting scheduling conflicts for semester {semester}. 
        You independently verify every timetable entry.""",
        tools=[check_conflict_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    reporter = Agent(
        role="Timetable Report Generator",
        goal=f"Save semester {semester} timetable to database and generate summary",
        backstory=f"""You save validated timetable entries for semester {semester} 
        to the database and produce a clear summary for the admin.""",
        tools=[save_timetable_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    collect_data_task = Task(
        description=f"""Fetch data for semester {semester} ONLY.
        Call each tool:
        - get_faculty_tool: fetch all active faculty
        - get_subjects_tool: fetch subjects for semester {semester}
        - get_allotments_tool: fetch allotments for semester {semester} batches only
        - get_rooms_tool: fetch all rooms
        - get_timeslots_tool: fetch all time slots
        - get_batches_tool: fetch batches for semester {semester} only
        - get_availability_tool: fetch faculty unavailability
        Return only data relevant to semester {semester}.""",
        expected_output=f"""A JSON object with keys: faculty, subjects, allotments, 
        rooms, time_slots, batches, availability. 
        All filtered to semester {semester} where applicable.""",
        agent=data_collector
    )

    analyze_constraints_task = Task(
        description=f"""Analyze constraints for semester {semester} data only.
        
        Hard constraints:
        - No faculty double booking in same time slot
        - No room double booking in same time slot
        - No batch double scheduling in same time slot
        - Faculty hours must not exceed max_hours_per_week
        - Lab subjects (P>0, L=0) need two consecutive slots same day
        - Practical subjects (L>0, P>0) need practical on two different days
        - Tutorial slots must be different day from lecture

        Soft constraints:
        - Respect faculty unavailability
        - No faculty teaching all 6 periods in one day
        - Avoid back to back classes for same batch
        - Labs in lab rooms, lectures in classrooms

        Categorize subjects:
        - pure_labs: scheme 0+0+P
        - lecture_with_practical: scheme L+0+P
        - lecture_with_tutorial: scheme L+T+0
        - pure_lectures: scheme L+0+0
        - projects: PROJECT, MPROJ""",
        expected_output="""JSON with hard_constraints, soft_constraints, 
        faculty_hour_limits, special_subjects, room_preferences.""",
        agent=constraint_analyzer,
        context=[collect_data_task]
    )

    schedule_task = Task(
        description=f"""Schedule all allotments for semester {semester}.
        Generation ID: {generation_id}

        Priority order:
        1. Pure labs first (need consecutive slots + lab room)
        2. Lecture with practical subjects
        3. Lecture with tutorial subjects
        4. Pure lectures
        5. Projects last (most flexible)

        For each allotment:
        1. Determine subject type from scheme values
        2. Pick room type (lab for practicals, classroom for lectures)
        3. Try each available time slot
        4. Call check_conflict_tool with:
           {{"faculty_id": "...", "room_id": "...", "time_slot_id": "...", 
           "batch_id": "...", "generation_id": "{generation_id}"}}
        5. If no conflict - assign this slot
        6. If conflict - try next slot
        7. If no slot found - add to unscheduled list

        Special rules:
        - Pure labs: two CONSECUTIVE periods same day, on TWO different days per week
        - Lecture+Practical: lecture in classroom, practicals on two different days in lab
        - Lecture+Tutorial: lecture one day, tutorials on different days
        - Projects: any available slot
        - Never exceed faculty max_hours_per_week

        Use check_conflict_tool before EVERY single assignment.""",
        expected_output="""JSON with keys: scheduled (list with subject_id, faculty_id, 
        room_id, time_slot_id, batch_id, role, generation_id for each entry), 
        unscheduled (list), total_scheduled (int), total_unscheduled (int).""",
        agent=scheduler,
        context=[collect_data_task, analyze_constraints_task]
    )

    validate_task = Task(
        description=f"""Validate the timetable for semester {semester}.

        Check every entry for:
        1. Faculty conflicts - check_conflict_tool for each entry
        2. Room conflicts - check_conflict_tool for each entry
        3. Batch conflicts - check_conflict_tool for each entry
        4. Faculty hour totals within limits
        5. Lab sessions are consecutive
        6. Practicals on two different days
        7. No batch has more than 6 classes per day

        Return PASSED if all good, FAILED with details if any violation found.""",
        expected_output="""JSON with status (PASSED or FAILED), 
        total_entries_checked, conflicts_found, conflicts list.""",
        agent=validator,
        context=[schedule_task]
    )

    report_task = Task(
        description=f"""Save semester {semester} timetable to database.

        Steps:
        1. Only proceed if validation status is PASSED
        2. Take all entries from scheduled list
        3. Call save_timetable_tool with entries as JSON string
        4. Each entry must have: subject_id, faculty_id, room_id,
           time_slot_id, batch_id, generation_id ({generation_id}), role
        5. Generate summary with total saved, unscheduled list

        If validation FAILED - do not save, return error summary.""",
        expected_output="""JSON with saved (int), failed (int), 
        generation_id, status (draft), summary.""",
        agent=reporter,
        context=[validate_task, schedule_task]
    )

    crew = Crew(
        agents=[
            data_collector,
            constraint_analyzer,
            scheduler,
            validator,
            reporter
        ],
        tasks=[
            collect_data_task,
            analyze_constraints_task,
            schedule_task,
            validate_task,
            report_task
        ],
        process=Process.sequential,
        verbose=True
    )

    crew.kickoff()


def run_scheduling_crew(generation_id: str):
    generation_status[generation_id] = "running"
    try:
        # Only schedule semester 2 for now
        _run_crew_for_semester(generation_id, semester=2)
        generation_status[generation_id] = "completed"
    except Exception as e:
        generation_status[generation_id] = f"failed: {str(e)}"
        raise e

