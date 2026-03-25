import os
import json
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from .tools import (
    get_faculty_tool,
    get_subjects_tool,
    get_allotments_tool,
    get_timeslots_tool,
    get_batches_tool,
    get_availability_tool,
    check_conflict_tool
)

load_dotenv()
os.environ["OPENAI_MODEL_NAME"] = "gpt-4"
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
        goal=f"Extract every subject allotment and all 30 time slots for semester {semester}.",
        backstory="You retrieve accurate UUIDs for faculty, subjects, batches and time slots. You return clean structured data.",
        tools=[
            get_faculty_tool,
            get_subjects_tool,
            get_allotments_tool,
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
        role="Weekly Scheduling Engine",
        goal="Assign all S6 subjects to a conflict-free 5-day 6-slot weekly grid for 3 batches.",
        backstory=(
            "You are an expert academic timetable scheduler. "
            "You strictly follow all lab, faculty, and room constraints. "
            "You never double-book a faculty member or a room. "
            "You always use real UUIDs from the collected data."
        ),
        tools=[check_conflict_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=50
    )

    reporter = Agent(
        role="Final JSON Auditor",
        goal="Compile the final schedule into a valid, complete JSON object for API response.",
        backstory=(
            "You verify the schedule is complete — 30 slots per batch, "
            "no missing entries, correct JSON format. "
            "You do NOT call any save tools. You only return the final JSON."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5
    )

    # ── TASKS ─────────────────────────────────────────────────────────────────

    collect_task = Task(
        description=(
            f"Fetch all scheduling data for semester {semester}:\n"
            "1. get_faculty_tool — all active faculty\n"
            "2. get_subjects_tool — all subjects\n"
            "3. get_allotments_tool(semester='6') — S6 allotments only\n"
            "4. get_timeslots_tool — all 30 time slots\n"
            "5. get_batches_tool(semester='6') — S6 batches only (A, B, C)\n"
            "6. get_availability_tool — faculty unavailability\n"
            "Return all data as a single JSON object."
        ),
        expected_output=(
            "JSON with keys: faculty, subjects, allotments, time_slots, batches, availability. "
            "Each key contains the full list from the database."
        ),
        agent=data_collector
    )

    schedule_task = Task(
        description=(
            f"Generate the COMPLETE S6 Weekly Timetable. Generation ID: {generation_id}\n\n"

            "═══ BATCHES ═══\n"
            "Schedule 3 batches: A, B, C.\n"
            "Each batch gets exactly 30 slots (5 days × 6 periods). NO EMPTY SLOTS.\n\n"

            "═══ SUBJECTS & WEEKLY HOURS (same for all 3 batches) ═══\n"
            "- CD   : 3 Lectures + 1 Tutorial = 4 slots. Faculty pool: APR, AFM\n"
            "- CGIP : 3 Lectures + 1 Tutorial = 4 slots. Faculty pool: ELZ, LMS\n"
            "- AAD  : 3 Lectures + 1 Tutorial = 4 slots. Faculty pool: RHM, VBP\n"
            "- ELE  : 2 Lectures + 1 Tutorial = 3 slots. Faculty pool: JTM, BVP\n"
            "- IE   : 3 Lectures + 1 Tutorial = 4 slots. Faculty: TBD\n"
            "- CCW  : 1 Lecture = 1 slot. Faculty: TBD\n"
            "- MPROJ/NWlab: 2 blocks × 3 consecutive periods = 6 slots.\n\n"
            "Total per batch: 4+4+4+3+4+1+6 = 26 slots\n"
            "Fill remaining 4 slots per batch with: Revision / Mentoring / Honors-Minor\n\n"

            "═══ MPROJ/NWlab RULES (CRITICAL) ═══\n"
            "Each batch has exactly TWO 3-hour blocks per week for MPROJ/NWlab.\n"
            "Blocks must be consecutive periods WITHIN the same half-day:\n"
            "  Morning block = P1+P2+P3 | Afternoon block = P4+P5+P6\n\n"
            "STAGGERED BATCH ASSIGNMENT:\n"
            "  Batch A → Block 1: Monday P4-P6   | Block 2: Wednesday P4-P6\n"
            "  Batch B → Block 1: Tuesday P4-P6  | Block 2: Thursday P4-P6\n"
            "  Batch C → Block 1: Friday P4-P6   | Block 2: Monday P1-P3\n\n"
            "HOW IT WORKS IN EACH BLOCK:\n"
            "  Half the batch goes to NWlab (Lab1). Other half goes to MPROJ (Lab2).\n"
            "  On Block 2, the halves SWAP (NWlab↔MPROJ).\n"
            "  In timetable just write 'MPROJ/NWlab' for both periods — class decides which half goes where.\n\n"
            "LAB CAPACITY SHARING RULE:\n"
            "  Lab1 capacity = 60. Lab2 capacity = 60. Half batch = ~30 students.\n"
            "  Therefore: TWO different batch halves CAN share the same lab simultaneously.\n"
            "  Example: If Batch A has Block 1 on Mon P4-P6 AND Batch C has Block 2 on Mon P1-P3,\n"
            "  they are at different times so no conflict.\n"
            "  If any two batches have lab blocks at the SAME time:\n"
            "    → Half of Batch X + Half of Batch Y can share Lab1 (NWlab)\n"
            "    → Half of Batch X + Half of Batch Y can share Lab2 (MPROJ)\n"
            "    → This is ALLOWED since total = 60 students per lab.\n\n"
            "NWlab FACULTY (assign exactly 2 per session):\n"
            "  Pool: MDL, RKR, AKJ, STS, ELZ, GTB\n"
            "  Pick any 2. Rotate across batches/days to spread workload.\n"
            "  If two batches share lab at same time → need 4 NWlab faculty total (2 per batch-half).\n\n"
            "MPROJ FACULTY (assign exactly 2 per session):\n"
            "  Pool: BVP, MRM, AFM, SKJ, DVP, SNL\n"
            "  Pick any 2. Rotate across batches/days to spread workload.\n"
            "  If two batches share lab at same time → need 4 MPROJ faculty total (2 per batch-half).\n\n"

            "═══ LECTURE FACULTY ASSIGNMENT ═══\n"
            "Any teacher from a subject's pool can teach ANY batch for that subject.\n"
            "Example: APR teaches CD for Batch A, AFM teaches CD for Batch B and C — all valid.\n"
            "Distribute evenly across faculty in each pool.\n"
            "Assign ONE faculty per lecture/tutorial slot.\n\n"

            "═══ ROOMS ═══\n"
            "Classrooms: CR101, CR102, CR103, CR104\n"
            "Labs: Lab1 (NWlab, capacity 60), Lab2 (MPROJ, capacity 60)\n"
            "Rules:\n"
            "  - Lectures and tutorials → assign one of CR101-CR104\n"
            "  - NWlab sessions → Lab1\n"
            "  - MPROJ sessions → Lab2\n"
            "  - No two batches can use the same classroom at the same time\n"
            "  - Lab1/Lab2 can hold two batch-halves at same time (capacity allows it)\n\n"

            "═══ HARD CONSTRAINTS ═══\n"
            "1. No faculty in two places at the same time\n"
            "2. No batch scheduled in two places at the same time\n"
            "3. No classroom used by two batches at the same time\n"
            "4. MPROJ/NWlab blocks MUST be exactly P1-P3 or P4-P6 (never split across half-days)\n"
            "5. IE faculty must always show as 'TBD'\n"
            "6. CCW faculty must always show as 'TBD'\n"
            "7. Use ONLY real UUIDs from the data collector output — NEVER invent IDs\n\n"

            "═══ OUTPUT FORMAT ═══\n"
            "Return a JSON array. Each entry:\n"
            "{\n"
            '  "batch": "A",\n'
            '  "day": "Monday",\n'
            '  "period": 1,\n'
            '  "subject": "CD",\n'
            '  "type": "lecture",\n'
            '  "faculty": ["APR"],\n'
            '  "room": "CR101",\n'
            '  "subject_id": "<uuid>",\n'
            '  "faculty_ids": ["<uuid>"],\n'
            '  "batch_id": "<uuid>",\n'
            '  "time_slot_id": "<uuid>"\n'
            "}\n"
            "For MPROJ/NWlab entries use faculty list with 2 names and both Lab1/Lab2 noted.\n"
        ),
        expected_output=(
            "A complete JSON array of 90 entries (30 per batch × 3 batches). "
            "Every slot filled. All constraints satisfied. Real UUIDs used throughout."
        ),
        agent=scheduler,
        context=[collect_task]
    )

    report_task = Task(
        description=(
            "Review the schedule from the Scheduler agent and produce the final output.\n\n"
            "Checks to perform:\n"
            "1. Exactly 30 slots per batch (A, B, C) = 90 total\n"
            "2. Each batch has exactly 6 MPROJ/NWlab slots (2 blocks × 3 periods)\n"
            "3. MPROJ/NWlab blocks are on correct days per batch:\n"
            "   A: Mon P4-P6 + Wed P4-P6\n"
            "   B: Tue P4-P6 + Thu P4-P6\n"
            "   C: Fri P4-P6 + Mon P1-P3\n"
            "4. Subject counts match requirements (CD=4, CGIP=4, AAD=4, ELE=3, IE=4, CCW=1)\n"
            "5. No faculty double-booked in any slot\n"
            "6. No classroom used by two batches simultaneously\n\n"
            "Do NOT call any tools. Do NOT save to database.\n"
            "Return ONLY the final JSON object with keys: 'schedule' (array) and 'summary' (object).\n"
            "Summary should include: total_entries, entries_per_batch, lab_blocks_verified, conflicts_found."
        ),
        expected_output=(
            "A raw JSON object with 'schedule' (90-entry array) and "
            "'summary' (verification results). No markdown, no extra text."
        ),
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
        
        generation_status[generation_id] = {
            "status": "completed",
            "result": result.raw
        }
        print(f"\n[Orchestrator] ✅ Generation {generation_id} completed.")
        return generation_status[generation_id]
    except Exception as e:
        generation_status[generation_id] = f"failed: {str(e)}"
        print(f"\n[Orchestrator] ❌ Failed: {str(e)}")
        raise e