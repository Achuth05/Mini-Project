import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process

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

load_dotenv()

# This dict is shared with timetable.py route
# Import it from routes when needed
generation_status = {}


def run_scheduling_crew(generation_id: str):
    """
    Main entry point called from Flask timetable route.
    Runs all 5 agents sequentially and updates generation_status.
    """

    generation_status[generation_id] = "running"

    try:
        # ── Agent 1 — Data Collector ──────────────────────────────────
        data_collector = Agent(
            role="Data Collection Specialist",
            goal="Fetch all data required for timetable scheduling from the database",
            backstory="""You are an expert at gathering and organizing scheduling data. 
            You fetch faculty, subjects, allotments, rooms, time slots and batches 
            and return them as clean structured JSON.""",
            tools=[
                get_faculty_tool,
                get_subjects_tool,
                get_allotments_tool,
                get_rooms_tool,
                get_timeslots_tool,
                get_batches_tool,
                get_availability_tool
            ],
            verbose=True,
            allow_delegation=False
        )

        # ── Agent 2 — Constraint Analyzer ────────────────────────────
        constraint_analyzer = Agent(
            role="Scheduling Constraint Analyst",
            goal="Analyze all scheduling data and identify every hard and soft constraint",
            backstory="""You are an expert in academic scheduling rules. You understand 
            faculty workload limits, room capacities, batch requirements, and special 
            subject types like labs, practicals and tutorials.""",
            tools=[],
            verbose=True,
            allow_delegation=False
        )

        # ── Agent 3 — Scheduler ───────────────────────────────────────
        scheduler = Agent(
            role="Timetable Scheduling Expert",
            goal="Assign every subject allotment to a specific time slot and room without any conflicts",
            backstory="""You are an expert in constraint satisfaction and academic timetabling. 
            You handle complex scheduling rules for labs, practicals, tutorials and lectures. 
            You always check for conflicts before making assignments and use backtracking 
            when needed.""",
            tools=[check_conflict_tool],
            verbose=True,
            allow_delegation=False
        )

        # ── Agent 4 — Validator ───────────────────────────────────────
        validator = Agent(
            role="Timetable Validation Expert",
            goal="Verify the generated timetable has zero hard constraint violations",
            backstory="""You are an expert at detecting scheduling conflicts. You 
            independently check every timetable entry for faculty conflicts, room 
            conflicts, batch conflicts and hour limit violations.""",
            tools=[check_conflict_tool],
            verbose=True,
            allow_delegation=False
        )

        # ── Agent 5 — Reporter ────────────────────────────────────────
        reporter = Agent(
            role="Timetable Report Generator",
            goal="Save the validated timetable to the database and generate a summary report",
            backstory="""You are expert at data persistence and report generation. 
            You save the final timetable entries to the database and produce 
            a clear summary for the admin to review.""",
            tools=[save_timetable_tool],
            verbose=True,
            allow_delegation=False
        )

        # ── Task 1 — Collect Data ─────────────────────────────────────
        collect_data_task = Task(
            description="""Fetch all data needed for timetable scheduling by calling 
            each tool. Call get_faculty_tool, get_subjects_tool, get_allotments_tool, 
            get_rooms_tool, get_timeslots_tool, get_batches_tool, and get_availability_tool. 
            Combine all results into one structured JSON object.""",
            expected_output="""A JSON object with keys: faculty, subjects, allotments, 
            rooms, time_slots, batches, availability. Each containing the full list 
            of records from the database.""",
            agent=data_collector
        )

        # ── Task 2 — Analyze Constraints ─────────────────────────────
        analyze_constraints_task = Task(
            description="""Using the data collected, analyze and identify all scheduling 
            constraints. 
            
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
            
            Also categorize subjects by type:
            - pure_labs: scheme 0+0+P
            - lecture_with_practical: scheme L+0+P
            - lecture_with_tutorial: scheme L+T+0
            - pure_lectures: scheme L+0+0
            - projects: PROJECT, MPROJ subjects""",
            expected_output="""A JSON constraints report with keys: hard_constraints, 
            soft_constraints, faculty_hour_limits, special_subjects, room_preferences.""",
            agent=constraint_analyzer,
            context=[collect_data_task]
        )

        # ── Task 3 — Schedule ─────────────────────────────────────────
        schedule_task = Task(
            description=f"""Using the allotments data and constraints report, create a 
            complete timetable. The generation_id is: {generation_id}
            
            Follow this priority order:
            1. Schedule pure labs first (most constrained - need consecutive slots + lab room)
            2. Schedule lecture with practical subjects
            3. Schedule lecture with tutorial subjects  
            4. Schedule pure lectures
            5. Schedule projects last (most flexible)
            
            For each allotment:
            1. Determine subject type from scheme values
            2. Pick appropriate room type (lab for practicals, classroom for lectures)
            3. Try each available time slot
            4. Call check_conflict_tool with faculty_id, room_id, time_slot_id, 
               batch_id, generation_id
            5. If no conflict - assign this slot
            6. If conflict - try next available slot
            7. If no slot found - add to unscheduled list
            
            Special rules:
            - Pure labs: find two CONSECUTIVE periods same day, schedule on TWO different days
            - Lecture+Practical: lecture in classroom, practicals on two different days in lab
            - Lecture+Tutorial: lecture one day, tutorials on different days
            - Projects: any available slot, each faculty gets their own slot
            - Never exceed faculty max_hours_per_week
            
            Use check_conflict_tool before EVERY assignment.""",
            expected_output="""A JSON object with keys: scheduled (list of complete 
            timetable entries with subject_id, faculty_id, room_id, time_slot_id, 
            batch_id, role, generation_id), unscheduled (list), 
            total_scheduled (int), total_unscheduled (int).""",
            agent=scheduler,
            context=[collect_data_task, analyze_constraints_task]
        )

        # ── Task 4 — Validate ─────────────────────────────────────────
        validate_task = Task(
            description="""Independently verify the draft timetable from the Scheduler.
            
            Check every single entry for:
            1. Faculty conflicts - use check_conflict_tool for each entry
            2. Room conflicts - use check_conflict_tool for each entry
            3. Batch conflicts - use check_conflict_tool for each entry
            4. Faculty hour totals - sum hours per faculty, check against limits
            5. Lab sessions are consecutive
            6. Practical sessions appear on two different days per week
            7. No batch has more than 6 classes per day
            
            If ANY hard constraint is violated return FAILED with conflict details.
            If all checks pass return PASSED.""",
            expected_output="""A JSON object with keys: status (PASSED or FAILED), 
            total_entries_checked, conflicts_found, conflicts (list of conflict details), 
            faculty_hour_check (dict of faculty code to hours scheduled vs limit).""",
            agent=validator,
            context=[schedule_task]
        )

        # ── Task 5 — Report ───────────────────────────────────────────
        report_task = Task(
            description=f"""Save the validated timetable to the database and generate 
            a summary report.
            
            Steps:
            1. Check validation status - only proceed if PASSED
            2. Take all entries from the scheduled list
            3. Call save_timetable_tool with the complete list of entries as JSON
            4. Each entry must include: subject_id, faculty_id, room_id, 
               time_slot_id, batch_id, generation_id ({generation_id}), role, status (draft)
            5. Generate summary report with:
               - Total slots assigned
               - Total unscheduled subjects
               - Faculty utilization stats
               - Any soft constraint violations
            
            If validation FAILED - do not save, return error summary.""",
            expected_output="""A JSON object with keys: saved (int), failed (int), 
            generation_id, status (draft), summary (object with scheduling statistics).""",
            agent=reporter,
            context=[validate_task, schedule_task]
        )

        # ── Assemble and Run Crew ─────────────────────────────────────
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

        result = crew.kickoff()

        generation_status[generation_id] = "completed"
        return result

    except Exception as e:
        generation_status[generation_id] = f"failed: {str(e)}"
        raise e