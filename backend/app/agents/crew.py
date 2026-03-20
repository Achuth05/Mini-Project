import os
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()
os.environ["OPENAI_API_KEY"] = "dummy-not-used"

# ─────────────────────────────────────────────────────────────
#  Shared status dict — imported by timetable.py
# ─────────────────────────────────────────────────────────────

generation_status = {}


# ─────────────────────────────────────────────────────────────
#  AGENT 1 — Data Agent
#  Responsibility: Fetch all raw data from Supabase
# ─────────────────────────────────────────────────────────────

class DataAgent:
    def __init__(self, sb):
        self.sb   = sb
        self.name = "DataAgent"

    def run(self, semester: int = 2) -> dict:
        print(f"\n[{self.name}] Fetching data for semester {semester} BTech...")

        batches = self.sb.table("batches") \
            .select("id, batch_name, semester, program") \
            .eq("semester", semester) \
            .eq("program", "BTech") \
            .execute().data

        batch_ids = [b["id"] for b in batches]
        if not batch_ids:
            raise ValueError(f"No BTech batches for semester {semester}")

        allotments = self.sb.table("subject_allotments") \
            .select("""
                id, role, assigned_hours,
                faculty:faculty_id (id, faculty_code, max_hours_per_week),
                subject:subject_id (id, subject_name, scheme_raw,
                                    lecture_hours, tutorial_hours, practical_hours),
                batch:batch_id (id, batch_name, semester, program)
            """) \
            .in_("batch_id", batch_ids) \
            .execute().data

        rooms = self.sb.table("rooms").select("*").execute().data

        slots = self.sb.table("time_slots").select("*") \
            .order("day").order("slot_number").execute().data

        availability = self.sb.table("faculty_availability") \
            .select("faculty_id, time_slot_id").execute().data

        data = {
            "batches":      batches,
            "batch_ids":    batch_ids,
            "allotments":   allotments,
            "rooms":        rooms,
            "slots":        slots,
            "availability": availability,
            "semester":     semester
        }

        print(f"[{self.name}] Loaded: {len(allotments)} allotments, "
              f"{len(rooms)} rooms, {len(slots)} slots, "
              f"{len(batches)} batches")
        return data


# ─────────────────────────────────────────────────────────────
#  AGENT 2 — Constraint Agent
#  Responsibility: Analyze data, group sessions, build constraints
# ─────────────────────────────────────────────────────────────

class ConstraintAgent:
    def __init__(self):
        self.name = "ConstraintAgent"

    def run(self, data: dict) -> dict:
        print(f"\n[{self.name}] Analyzing constraints...")

        rooms      = data["rooms"]
        slots      = data["slots"]
        allotments = data["allotments"]
        availability = data["availability"]

        # Room pools
        classrooms = [r for r in rooms if r["room_type"] == "classroom"]
        labs       = [r for r in rooms if r["room_type"] == "lab"]
        if not classrooms:
            classrooms = rooms
        if not labs:
            labs = rooms

        # Faculty unavailability set
        unavailable = set(
            (a["faculty_id"], a["time_slot_id"]) for a in availability
        )

        # Slot helpers
        slot_ids = [s["id"] for s in slots]

        def _day(slot):
            return slot.get("day") or slot.get("day_of_week") or ""

        def _period(slot):
            return slot.get("slot_number") or slot.get("period") or 0

        # Group allotments into practical sessions and lectures
        practical_sessions = []
        lecture_allotments = []

        prac_groups = defaultdict(list)
        for allot in allotments:
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

        # Subject type analysis
        subject_analysis = []
        for allot in allotments:
            subj = allot["subject"]
            L = subj.get("lecture_hours")   or 0
            T = subj.get("tutorial_hours")  or 0
            P = subj.get("practical_hours") or 0
            subject_analysis.append({
                "subject":  subj["subject_name"],
                "batch":    allot["batch"]["batch_name"],
                "role":     allot["role"],
                "L": L, "T": T, "P": P
            })

        constraints = {
            "classrooms":          classrooms,
            "labs":                labs,
            "all_rooms":           rooms,
            "unavailable":         unavailable,
            "slot_ids":            slot_ids,
            "slots":               slots,
            "practical_sessions":  practical_sessions,
            "lecture_allotments":  lecture_allotments,
            "subject_analysis":    subject_analysis,
            "_day":                _day,
            "_period":             _period
        }

        print(f"[{self.name}] Practical sessions: {len(practical_sessions)}, "
              f"Lecture allotments: {len(lecture_allotments)}")
        print(f"[{self.name}] Classrooms: {len(classrooms)}, "
              f"Labs: {len(labs)}, "
              f"Unavailable slots: {len(unavailable)}")
        print(f"[{self.name}] Hard constraints identified:")
        print(f"  → No faculty double-booking")
        print(f"  → No room double-booking")
        print(f"  → No batch double-booking")
        print(f"  → Practicals = 2 consecutive slots, same room, same day")
        print(f"  → Max 1 lecture per day per allotment")

        return constraints


# ─────────────────────────────────────────────────────────────
#  AGENT 3 — Scheduler Agent
#  Responsibility: Build OR-Tools model and solve
# ─────────────────────────────────────────────────────────────

class SchedulerAgent:
    def __init__(self):
        self.name = "SchedulerAgent"

    def run(self, data: dict, constraints: dict, generation_id: str) -> dict:
        from ortools.sat.python import cp_model

        print(f"\n[{self.name}] Building OR-Tools CP-SAT model...")

        classrooms         = constraints["classrooms"]
        labs               = constraints["labs"]
        all_rooms          = constraints["all_rooms"]
        unavailable        = constraints["unavailable"]
        slot_ids           = constraints["slot_ids"]
        slots              = constraints["slots"]
        practical_sessions = constraints["practical_sessions"]
        lecture_allotments = constraints["lecture_allotments"]
        _day               = constraints["_day"]
        _period            = constraints["_period"]
        num_slots          = len(slot_ids)

        model = cp_model.CpModel()

        prac_slot_vars = defaultdict(list)
        lec_slot_vars  = defaultdict(list)

        # Build vars for practical sessions
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

        # Build vars for lectures
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

        print(f"[{self.name}] Adding constraints...")

        # Precompute valid consecutive pairs per practical session
        prac_valid_pairs = {}

        # C1a: Practicals = exactly 2 consecutive slots
        for sess_idx, sess in enumerate(practical_sessions):
            vars_list  = prac_slot_vars[sess_idx]
            batch_name = sess["batch"]["batch_name"]
            subj_name  = sess["subject"]["subject_name"]

            if not vars_list:
                prac_valid_pairs[sess_idx] = []
                continue

            var_map     = {(si, ri): var for (si, ri, var) in vars_list}
            valid_pairs = []

            for (si1, ri1, v1) in vars_list:
                si2 = si1 + 1
                if si2 >= num_slots:
                    continue
                if (si2, ri1) not in var_map:
                    continue
                if _day(slots[si1]) != _day(slots[si2]):
                    continue
                if _period(slots[si2]) - _period(slots[si1]) != 1:
                    continue
                v2 = var_map[(si2, ri1)]
                valid_pairs.append((si1, ri1, v1, si2, ri1, v2))

            prac_valid_pairs[sess_idx] = valid_pairs

            if not valid_pairs:
                print(f"[{self.name}] WARNING: No pairs for "
                      f"{batch_name}/{subj_name}")
                continue

            print(f"[{self.name}] {batch_name}/{subj_name}: "
                  f"{len(valid_pairs)} pairs")

            indicators = []
            for idx, (si1, ri1, v1, si2, ri2, v2) in enumerate(valid_pairs):
                b = model.NewBoolVar(f"cp_ps{sess_idx}_{idx}")
                model.AddImplication(b, v1)
                model.AddImplication(b, v2)
                indicators.append(b)

            model.AddExactlyOne(indicators)

            valid_vs = set()
            for (si1, ri1, v1, si2, ri2, v2) in valid_pairs:
                valid_vs.add(v1)
                valid_vs.add(v2)
            for (si, ri, var) in vars_list:
                if var not in valid_vs:
                    model.Add(var == 0)

            model.Add(sum(var for (si, ri, var) in vars_list) == 2)

        # C1b: Lectures get correct number of slots
        for allot in lecture_allotments:
            aid  = allot["id"]
            subj = allot["subject"]
            L    = subj.get("lecture_hours")  or 0
            T    = subj.get("tutorial_hours") or 0
            slots_needed = max(L + T, 1)

            if not lec_slot_vars[aid]:
                continue

            model.Add(
                sum(v for _, _, v in lec_slot_vars[aid]) == slots_needed
            )

        # C1c: Max 1 lecture per day per allotment
        for allot in lecture_allotments:
            aid = allot["id"]
            vars_by_day = defaultdict(list)
            for (si, ri, var) in lec_slot_vars[aid]:
                vars_by_day[_day(slots[si])].append(var)
            for day_vars in vars_by_day.values():
                model.Add(sum(day_vars) <= 1)

        # C2: Faculty not double-booked (both slots of practical blocked)
        faculty_slot = defaultdict(list)
        for sess_idx, sess in enumerate(practical_sessions):
            for (si1, ri1, v1, si2, ri2, v2) in prac_valid_pairs.get(sess_idx, []):
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

        # C3: Room not double-booked
        room_slot = defaultdict(list)
        for sess_idx in range(len(practical_sessions)):
            for (si1, ri1, v1, si2, ri2, v2) in prac_valid_pairs.get(sess_idx, []):
                room_slot[(ri1, si1)].append(v1)
                room_slot[(ri1, si2)].append(v1)
        for allot in lecture_allotments:
            aid = allot["id"]
            for (si, ri, var) in lec_slot_vars[aid]:
                room_slot[(ri, si)].append(var)
        for vlist in room_slot.values():
            model.Add(sum(vlist) <= 1)

        # C4: Batch not double-booked
        batch_slot = defaultdict(list)
        for sess_idx, sess in enumerate(practical_sessions):
            bid = sess["batch_id"]
            for (si1, ri1, v1, si2, ri2, v2) in prac_valid_pairs.get(sess_idx, []):
                batch_slot[(bid, si1)].append(v1)
                batch_slot[(bid, si2)].append(v1)
        for allot in lecture_allotments:
            aid = allot["id"]
            bid = allot["batch"]["id"]
            for (si, ri, var) in lec_slot_vars[aid]:
                batch_slot[(bid, si)].append(var)
        for vlist in batch_slot.values():
            model.Add(sum(vlist) <= 1)

        # Solve
        print(f"[{self.name}] Solving...")
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 120.0
        solver.parameters.num_search_workers  = 4

        status     = solver.Solve(model)
        status_name = solver.StatusName(status)
        print(f"[{self.name}] Status: {status_name}")

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise RuntimeError(
                f"OR-Tools could not find feasible schedule. "
                f"Status: {status_name}"
            )

        # Extract solution
        entries = []
        for sess_idx, sess in enumerate(practical_sessions):
            for (si, ri, var) in prac_slot_vars[sess_idx]:
                if solver.Value(var) == 1:
                    slot = slots[si]
                    room = all_rooms[ri]
                    for f_allot in sess["faculty_list"]:
                        entries.append({
                            "subject_id":  sess["subject_id"],
                            "faculty_id":  f_allot["faculty"]["id"],
                            "room_id":     room["id"],
                            "time_slot_id": slot_ids[si],
                            "batch_id":    sess["batch_id"],
                            "subject":     sess["subject"]["subject_name"],
                            "faculty":     f_allot["faculty"]["faculty_code"],
                            "room":        room["room_code"],
                            "day":         _day(slot),
                            "slot":        _period(slot),
                            "batch":       sess["batch"]["batch_name"],
                            "role":        "practical"
                        })

        for allot in lecture_allotments:
            aid = allot["id"]
            for (si, ri, var) in lec_slot_vars[aid]:
                if solver.Value(var) == 1:
                    slot = slots[si]
                    room = all_rooms[ri]
                    entries.append({
                        "subject_id":   allot["subject"]["id"],
                        "faculty_id":   allot["faculty"]["id"],
                        "room_id":      room["id"],
                        "time_slot_id": slot_ids[si],
                        "batch_id":     allot["batch"]["id"],
                        "subject":      allot["subject"]["subject_name"],
                        "faculty":      allot["faculty"]["faculty_code"],
                        "room":         room["room_code"],
                        "day":          _day(slot),
                        "slot":         _period(slot),
                        "batch":        allot["batch"]["batch_name"],
                        "role":         allot.get("role", "lecture")
                    })

        entries.sort(key=lambda x: (x["batch"], x["day"], x["slot"]))

        print(f"[{self.name}] Solution found: {len(entries)} entries")

        return {
            "entries":       entries,
            "solver_status": status_name,
            "generation_id": generation_id
        }


# ─────────────────────────────────────────────────────────────
#  AGENT 4 — Validator Agent
#  Responsibility: Verify solution is conflict-free
# ─────────────────────────────────────────────────────────────

class ValidatorAgent:
    def __init__(self):
        self.name = "ValidatorAgent"

    def run(self, solution: dict) -> dict:
        print(f"\n[{self.name}] Validating timetable...")

        entries   = solution["entries"]
        conflicts = []

        # Check faculty double-booking
        faculty_slots = defaultdict(list)
        for e in entries:
            key = (e["faculty_id"], e["day"], e["slot"])
            faculty_slots[key].append(e)

        for key, entries_at_slot in faculty_slots.items():
            if len(entries_at_slot) > 1:
                conflicts.append({
                    "type":    "faculty_conflict",
                    "faculty": entries_at_slot[0]["faculty"],
                    "day":     key[1],
                    "slot":    key[2],
                    "entries": [f"{e['batch']}/{e['subject']}"
                                for e in entries_at_slot]
                })

        # Check room double-booking
        room_slots = defaultdict(list)
        for e in entries:
            key = (e["room_id"], e["day"], e["slot"])
            room_slots[key].append(e)

        for key, entries_at_slot in room_slots.items():
        # Same room same slot is OK if it's the same batch same subject
        # (two faculty for same practical session)
            unique_batch_subject = set(
                (e["batch_id"], e["subject_id"]) for e in entries_at_slot
            )
            if len(unique_batch_subject) > 1:
                conflicts.append({
                "type":  "room_conflict",
                "room":  entries_at_slot[0]["room"],
                "day":   key[1],
                "slot":  key[2],
                "entries": [f"{e['batch']}/{e['subject']}/{e['faculty']}"
                            for e in entries_at_slot]
            })

        # Check batch double-booking
        batch_slots = defaultdict(list)
        for e in entries:
            key = (e["batch_id"], e["day"], e["slot"])
            batch_slots[key].append(e)

        for key, entries_at_slot in batch_slots.items():
            # Practical can have 2 faculty same slot — that's fine
            unique_subjects = set(e["subject_id"] for e in entries_at_slot)
            if len(unique_subjects) > 1:
                conflicts.append({
                    "type":  "batch_conflict",
                    "batch": entries_at_slot[0]["batch"],
                    "day":   key[1],
                    "slot":  key[2],
                    "entries": [f"{e['subject']}/{e['role']}"
                                for e in entries_at_slot]
                })

        status = "PASSED" if not conflicts else "FAILED"

        print(f"[{self.name}] Validation: {status}")
        print(f"[{self.name}] Entries checked: {len(entries)}")
        print(f"[{self.name}] Conflicts found: {len(conflicts)}")

        if conflicts:
            for c in conflicts:
                print(f"  ❌ {c['type']}: {c}")
        else:
            print(f"  ✅ No conflicts found!")

        return {
            "status":    status,
            "conflicts": conflicts,
            "total":     len(entries)
        }


# ─────────────────────────────────────────────────────────────
#  AGENT 5 — Reporter Agent
#  Responsibility: Print summary and return final result
# ─────────────────────────────────────────────────────────────

class ReporterAgent:
    def __init__(self):
        self.name = "ReporterAgent"

    def run(self, solution: dict, validation: dict) -> dict:
        print(f"\n[{self.name}] Generating report...")

        entries    = solution["entries"]
        generation_id = solution["generation_id"]

        if validation["status"] == "FAILED":
            print(f"[{self.name}] ❌ Validation failed — "
                  f"{len(validation['conflicts'])} conflicts found")
            return {
                "status":    "failed",
                "conflicts": validation["conflicts"],
                "generation_id": generation_id
            }

        # Print timetable
        print("\n" + "="*60)
        print(f"TIMETABLE — Semester 2 BTech")
        print(f"Solver: {solution['solver_status']}")
        print(f"Total entries: {len(entries)}")
        print(f"Validation: {validation['status']}")
        print("="*60)

        current_batch = None
        for e in entries:
            if e["batch"] != current_batch:
                current_batch = e["batch"]
                print(f"\n--- Batch {current_batch} ---")
            print(f"  {e['day']:<12} Slot{e['slot']} | "
                  f"{e['subject']:<8} | {e['role']:<10} | "
                  f"{e['faculty']:<6} | {e['room']}")

        print("="*60)

        # Summary per batch
        print(f"\n[{self.name}] Summary:")
        batch_counts = defaultdict(int)
        for e in entries:
            batch_counts[e["batch"]] += 1
        for batch, count in sorted(batch_counts.items()):
            print(f"  Batch {batch}: {count} entries")

        return {
            "total_entries": len(entries),
            "generation_id": generation_id,
            "solver_status": solution["solver_status"],
            "validation":    validation["status"],
            "timetable":     entries
        }


# ─────────────────────────────────────────────────────────────
#  ORCHESTRATOR — runs all 5 agents in sequence
# ─────────────────────────────────────────────────────────────

def run_scheduling_crew(generation_id: str, semester: int = 2):
    from .tools import sb

    generation_status[generation_id] = "running"

    print(f"\n{'='*60}")
    print(f"MULTI-AGENT TIMETABLE SCHEDULER")
    print(f"Generation ID: {generation_id}")
    print(f"Semester: {semester} BTech")
    print(f"{'='*60}")

    try:
        # Agent 1: Fetch data
        data = DataAgent(sb).run(semester)

        # Agent 2: Analyze constraints
        constraints = ConstraintAgent().run(data)

        # Agent 3: Schedule using OR-Tools
        solution = SchedulerAgent().run(data, constraints, generation_id)

        # Agent 4: Validate solution
        validation = ValidatorAgent().run(solution)

        # Agent 5: Generate report
        result = ReporterAgent().run(solution, validation)

        generation_status[generation_id] = "completed"

        print(f"\n[Orchestrator] ✅ All agents completed successfully")
        # FIX: check which keys exist
        if result.get("status") == "failed":
            print(f"[Orchestrator] ❌ Validation failed: "
                  f"{len(result.get('conflicts', []))} conflicts")
        else:
            print(f"[Orchestrator] Total entries: {result['total_entries']}")
            print(f"[Orchestrator] Validation: {result['validation']}")

        return result

    except Exception as e:
        generation_status[generation_id] = f"failed: {str(e)}"
        print(f"\n[Orchestrator] ❌ Failed: {str(e)}")
        raise e