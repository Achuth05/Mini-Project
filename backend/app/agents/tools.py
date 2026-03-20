import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from crewai.tools import tool
from ortools.sat.python import cp_model
from collections import defaultdict

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb: Client = create_client(url, key)


# ─────────────────────────────────────────────
#  DB FETCH TOOLS
# ─────────────────────────────────────────────

@tool("Get Faculty Tool")
def get_faculty_tool(query: str = "") -> str:
    """Fetches all active faculty members from the database."""
    try:
        result = sb.table("faculty") \
            .select("id, faculty_code, full_name, faculty_type, max_hours_per_week") \
            .eq("is_active", True).execute()
        return json.dumps(result.data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Get Subjects Tool")
def get_subjects_tool(query: str = "") -> str:
    """Fetches all subjects with scheme details."""
    try:
        result = sb.table("subjects") \
            .select("id, subject_code, subject_name, scheme_raw, lecture_hours, tutorial_hours, practical_hours, total_required_hours, semester, program") \
            .execute()
        return json.dumps(result.data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Get Allotments Tool")
def get_allotments_tool(semester: str = "2") -> str:
    """Fetches subject allotments filtered by semester."""
    try:
        batches = sb.table("batches").select("id") \
            .eq("semester", int(semester)) \
            .eq("program", "BTech").execute()
        batch_ids = [b["id"] for b in batches.data]
        if not batch_ids:
            return json.dumps([])
        result = sb.table("subject_allotments") \
            .select("""
                id, role, assigned_hours,
                faculty:faculty_id (id, faculty_code, max_hours_per_week),
                subject:subject_id (id, subject_name, scheme_raw, lecture_hours, tutorial_hours, practical_hours),
                batch:batch_id (id, batch_name, semester, program)
            """).in_("batch_id", batch_ids).execute()
        return json.dumps(result.data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Get Rooms Tool")
def get_rooms_tool(query: str = "") -> str:
    """Fetches all rooms."""
    try:
        result = sb.table("rooms") \
            .select("id, room_code, room_name, capacity, room_type").execute()
        return json.dumps(result.data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Get Time Slots Tool")
def get_timeslots_tool(query: str = "") -> str:
    """Fetches all 30 time slots ordered by day and period."""
    try:
        result = sb.table("time_slots").select("*") \
            .order("day").order("slot_number").execute()
        return json.dumps(result.data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Get Batches Tool")
def get_batches_tool(semester: str = "2") -> str:
    """Fetches BTech batches filtered by semester."""
    try:
        result = sb.table("batches") \
            .select("id, batch_name, semester, program, academic_year") \
            .eq("semester", int(semester)) \
            .eq("program", "BTech").execute()
        return json.dumps(result.data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Get Availability Tool")
def get_availability_tool(query: str = "") -> str:
    """Fetches faculty unavailability slots."""
    try:
        result = sb.table("faculty_availability") \
            .select("faculty_id, time_slot_id, reason").execute()
        return json.dumps(result.data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Save Timetable Tool")
def save_timetable_tool(entries: str) -> str:
    """Saves timetable entries to the database."""
    try:
        data   = json.loads(entries)
        saved  = 0
        failed = 0
        errors = []
        for entry in data:
            try:
                sb.table("timetable_entries").insert({
                    "subject_id":    entry["subject_id"],
                    "faculty_id":    entry["faculty_id"],
                    "room_id":       entry["room_id"],
                    "time_slot_id":  entry["time_slot_id"],
                    "batch_id":      entry["batch_id"],
                    "generation_id": entry["generation_id"],
                    "role":          entry.get("role", "lecture"),
                    "status":        "draft"
                }).execute()
                saved += 1
            except Exception as e:
                failed += 1
                errors.append(str(e))
        return json.dumps({"saved": saved, "failed": failed, "errors": errors})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _slot_day(slot):
    return slot.get("day") or slot.get("day_of_week") or ""

def _slot_number(slot):
    return slot.get("slot_number") or slot.get("period") or 0


# ─────────────────────────────────────────────
#  OR-TOOLS SCHEDULER
# ─────────────────────────────────────────────

def _run_scheduler(generation_id: str, semester: int = 2):
    print(f"[Scheduler] Starting for semester {semester} BTech only")

    # ── 1. Fetch data ──────────────────────────────────────────────

    batches_raw = sb.table("batches") \
        .select("id, batch_name, semester, program") \
        .eq("semester", semester) \
        .eq("program", "BTech") \
        .execute().data

    batch_ids = [b["id"] for b in batches_raw]
    if not batch_ids:
        raise ValueError(f"No BTech batches found for semester {semester}")

    allotments_raw = sb.table("subject_allotments") \
        .select("""
            id, role, assigned_hours,
            faculty:faculty_id (id, faculty_code, max_hours_per_week),
            subject:subject_id (id, subject_name, scheme_raw,
                                lecture_hours, tutorial_hours, practical_hours),
            batch:batch_id (id, batch_name, semester, program)
        """) \
        .in_("batch_id", batch_ids) \
        .execute().data

    rooms_raw    = sb.table("rooms").select("*").execute().data
    slots_raw    = sb.table("time_slots").select("*") \
                     .order("day").order("slot_number").execute().data
    availability = sb.table("faculty_availability") \
                     .select("faculty_id, time_slot_id").execute().data

    print(f"[Scheduler] Loaded: {len(allotments_raw)} allotments, "
          f"{len(rooms_raw)} rooms, {len(slots_raw)} slots, "
          f"{len(batches_raw)} batches")

    # ── 2. Room pools ──────────────────────────────────────────────

    classrooms = [r for r in rooms_raw if r["room_type"] == "classroom"]
    labs       = [r for r in rooms_raw if r["room_type"] == "lab"]
    all_rooms  = rooms_raw

    if not classrooms:
        classrooms = all_rooms
    if not labs:
        labs = all_rooms

    print(f"[Scheduler] Classrooms: {len(classrooms)}, Labs: {len(labs)}")

    # ── 3. Helpers ─────────────────────────────────────────────────

    unavailable = set(
        (a["faculty_id"], a["time_slot_id"]) for a in availability
    )

    slot_ids  = [s["id"] for s in slots_raw]
    num_slots = len(slot_ids)

    def _day(slot):
        return slot.get("day") or slot.get("day_of_week") or ""

    def _period(slot):
        return slot.get("slot_number") or slot.get("period") or 0

    # ── 4. Group allotments ────────────────────────────────────────

    practical_sessions = []
    lecture_allotments = []

    prac_groups = defaultdict(list)
    for allot in allotments_raw:
        if allot["role"] == "practical":
            bid = allot["batch"]["id"]
            sid = allot["subject"]["id"]
            prac_groups[(bid, sid)].append(allot)
        else:
            lecture_allotments.append(allot)

    for (bid, sid), group in prac_groups.items():
        practical_sessions.append({
            "batch_id":     bid,
            "subject_id":   sid,
            "batch":        group[0]["batch"],
            "subject":      group[0]["subject"],
            "faculty_list": group,
            "role":         "practical"
        })

    print(f"[Scheduler] Practical sessions: {len(practical_sessions)}, "
          f"Lecture allotments: {len(lecture_allotments)}")

    # ── 5. Build CP-SAT model ──────────────────────────────────────

    model = cp_model.CpModel()

    prac_slot_vars = defaultdict(list)  # sess_idx → [(si, ri, var)]
    lec_slot_vars  = defaultdict(list)  # aid      → [(si, ri, var)]

    print(f"[Scheduler] Building vars...")

    # Practical session vars — one var per (slot, room) combo
    # Only created if ALL faculty in session are free at that slot
    for sess_idx, sess in enumerate(practical_sessions):
        faculty_list = sess["faculty_list"]
        for ri, room in enumerate(all_rooms):
            if room not in labs:
                continue
            for si in range(num_slots):
                slot_id = slot_ids[si]
                if any((f["faculty"]["id"], slot_id) in unavailable
                       for f in faculty_list):
                    continue
                var = model.NewBoolVar(f"ps{sess_idx}_s{si}_r{ri}")
                prac_slot_vars[sess_idx].append((si, ri, var))

    # Lecture vars
    for allot in lecture_allotments:
        aid        = allot["id"]
        faculty_id = allot["faculty"]["id"]
        for ri, room in enumerate(all_rooms):
            if room not in classrooms:
                continue
            for si in range(num_slots):
                slot_id = slot_ids[si]
                if (faculty_id, slot_id) in unavailable:
                    continue
                var = model.NewBoolVar(f"lec{aid}_s{si}_r{ri}")
                lec_slot_vars[aid].append((si, ri, var))

    # ── 6. Constraints ─────────────────────────────────────────────

    print(f"[Scheduler] Adding constraints...")

    # ── C1a: Each practical = exactly one consecutive pair ──────────
    # Also precompute valid pairs for use in C2/C3/C4
    prac_valid_pairs = {}  # sess_idx → [(si1, ri1, v1, si2, ri2, v2)]

    for sess_idx, sess in enumerate(practical_sessions):
        vars_list  = prac_slot_vars[sess_idx]
        batch_name = sess["batch"]["batch_name"]
        subj_name  = sess["subject"]["subject_name"]

        if not vars_list:
            print(f"[Scheduler] WARNING: No vars for practical "
                  f"{batch_name}/{subj_name}")
            prac_valid_pairs[sess_idx] = []
            continue

        # Build (si,ri) → var map for fast lookup
        var_map = {(si, ri): var for (si, ri, var) in vars_list}

        valid_pairs = []
        for (si1, ri1, v1) in vars_list:
            si2 = si1 + 1
            ri2 = ri1
            if (si2, ri2) not in var_map:
                continue
            if si2 >= num_slots:
                continue
            if _day(slots_raw[si1]) != _day(slots_raw[si2]):
                continue
            if _period(slots_raw[si2]) - _period(slots_raw[si1]) != 1:
                continue
            v2 = var_map[(si2, ri2)]
            valid_pairs.append((si1, ri1, v1, si2, ri2, v2))

        prac_valid_pairs[sess_idx] = valid_pairs

        if not valid_pairs:
            print(f"[Scheduler] WARNING: No consecutive pairs for "
                  f"{batch_name}/{subj_name}")
            continue

        print(f"[Scheduler] {batch_name}/{subj_name}: "
              f"{len(valid_pairs)} consecutive pairs")

        # Exactly one consecutive pair chosen
        indicators = []
        for idx, (si1, ri1, v1, si2, ri2, v2) in enumerate(valid_pairs):
            b = model.NewBoolVar(f"cp_ps{sess_idx}_{idx}")
            model.AddImplication(b, v1)
            model.AddImplication(b, v2)
            indicators.append(b)

        model.AddExactlyOne(indicators)

        # All vars not in any valid pair must be 0
        valid_vs = set()
        for (si1, ri1, v1, si2, ri2, v2) in valid_pairs:
            valid_vs.add(v1)
            valid_vs.add(v2)
        for (si, ri, var) in vars_list:
            if var not in valid_vs:
                model.Add(var == 0)

        # Exactly 2 slots total
        model.Add(sum(var for (si, ri, var) in vars_list) == 2)

    # ── C1b: Each lecture = correct number of slots ─────────────────
    for allot in lecture_allotments:
        aid  = allot["id"]
        subj = allot["subject"]
        L    = subj.get("lecture_hours")  or 0
        T    = subj.get("tutorial_hours") or 0
        slots_needed = max(L + T, 1)

        if not lec_slot_vars[aid]:
            print(f"[Scheduler] WARNING: No vars for lecture {aid}")
            continue

        model.Add(
            sum(v for _, _, v in lec_slot_vars[aid]) == slots_needed
        )

    # ── C1c: Max 1 lecture per day per allotment ────────────────────
    for allot in lecture_allotments:
        aid = allot["id"]
        vars_by_day = defaultdict(list)
        for (si, ri, var) in lec_slot_vars[aid]:
            vars_by_day[_day(slots_raw[si])].append(var)
        for day_vars in vars_by_day.values():
            model.Add(sum(day_vars) <= 1)

    # ── C2: Faculty not double-booked ───────────────────────────────
    # Practicals: faculty occupies BOTH slots of the chosen pair
    # So we use the first slot var (v1) as indicator for both si1 and si2
    faculty_slot = defaultdict(list)

    for sess_idx, sess in enumerate(practical_sessions):
        valid_pairs = prac_valid_pairs.get(sess_idx, [])
        for (si1, ri1, v1, si2, ri2, v2) in valid_pairs:
            for f_allot in sess["faculty_list"]:
                fid = f_allot["faculty"]["id"]
                faculty_slot[(fid, si1)].append(v1)
                faculty_slot[(fid, si2)].append(v1)

    for allot in lecture_allotments:
        aid = allot["id"]
        fid = allot["faculty"]["id"]
        for (si, ri, var) in lec_slot_vars[aid]:
            faculty_slot[(fid, si)].append(var)

    for vlist in faculty_slot.values():
        model.Add(sum(vlist) <= 1)

    # ── C3: Room not double-booked ──────────────────────────────────
    room_slot = defaultdict(list)

    for sess_idx in range(len(practical_sessions)):
        valid_pairs = prac_valid_pairs.get(sess_idx, [])
        for (si1, ri1, v1, si2, ri2, v2) in valid_pairs:
            room_slot[(ri1, si1)].append(v1)
            room_slot[(ri1, si2)].append(v1)

    for allot in lecture_allotments:
        aid = allot["id"]
        for (si, ri, var) in lec_slot_vars[aid]:
            room_slot[(ri, si)].append(var)

    for vlist in room_slot.values():
        model.Add(sum(vlist) <= 1)

    # ── C4: Batch not double-booked ─────────────────────────────────
    batch_slot = defaultdict(list)

    for sess_idx, sess in enumerate(practical_sessions):
        bid         = sess["batch_id"]
        valid_pairs = prac_valid_pairs.get(sess_idx, [])
        for (si1, ri1, v1, si2, ri2, v2) in valid_pairs:
            batch_slot[(bid, si1)].append(v1)
            batch_slot[(bid, si2)].append(v1)

    for allot in lecture_allotments:
        aid = allot["id"]
        bid = allot["batch"]["id"]
        for (si, ri, var) in lec_slot_vars[aid]:
            batch_slot[(bid, si)].append(var)

    for vlist in batch_slot.values():
        model.Add(sum(vlist) <= 1)

    # ── 7. Solve ───────────────────────────────────────────────────

    print(f"[Scheduler] Solving...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 120.0
    solver.parameters.num_search_workers  = 4

    status = solver.Solve(model)
    print(f"[Scheduler] Status: {solver.StatusName(status)}")

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(
            f"OR-Tools could not find feasible schedule. "
            f"Status: {solver.StatusName(status)}"
        )

    # ── 8. Extract solution ────────────────────────────────────────

    print(f"[Scheduler] Extracting solution...")
    entries = []

    for sess_idx, sess in enumerate(practical_sessions):
        for (si, ri, var) in prac_slot_vars[sess_idx]:
            if solver.Value(var) == 1:
                slot = slots_raw[si]
                room = all_rooms[ri]
                for f_allot in sess["faculty_list"]:
                    entries.append({
                        "subject": sess["subject"]["subject_name"],
                        "faculty": f_allot["faculty"]["faculty_code"],
                        "room":    room["room_code"],
                        "day":     _day(slot),
                        "slot":    _period(slot),
                        "batch":   sess["batch"]["batch_name"],
                        "role":    "practical"
                    })

    for allot in lecture_allotments:
        aid = allot["id"]
        for (si, ri, var) in lec_slot_vars[aid]:
            if solver.Value(var) == 1:
                slot = slots_raw[si]
                room = all_rooms[ri]
                entries.append({
                    "subject": allot["subject"]["subject_name"],
                    "faculty": allot["faculty"]["faculty_code"],
                    "room":    room["room_code"],
                    "day":     _day(slot),
                    "slot":    _period(slot),
                    "batch":   allot["batch"]["batch_name"],
                    "role":    allot.get("role", "lecture")
                })

    entries.sort(key=lambda x: (x["batch"], x["day"], x["slot"]))

    print(f"[Scheduler] Total entries: {len(entries)}")

    # ── 9. Pretty print ────────────────────────────────────────────

    print("\n" + "="*60)
    print(f"TIMETABLE — Semester {semester} BTech")
    print(f"Solver: {solver.StatusName(status)}")
    print(f"Total entries: {len(entries)}")
    print("="*60)

    current_batch = None
    for e in entries:
        if e["batch"] != current_batch:
            current_batch = e["batch"]
            print(f"\n--- Batch {current_batch} ---")
        print(f"  {e['day']:<12} Slot{e['slot']} | "
              f"{e['subject']:<8} | {e['role']:<10} | "
              f"{e['faculty']:<6} | {e['room']}")

    print("="*60 + "\n")

    return {
        "total_entries": len(entries),
        "generation_id": generation_id,
        "solver_status": solver.StatusName(status),
        "timetable":     entries
    }