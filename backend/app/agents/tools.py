import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from crewai.tools import tool

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb: Client = create_client(url, key)


@tool("Get Faculty Tool")
def get_faculty_tool(query: str = "") -> str:
    """Fetches all active faculty members from the database with their codes and hour limits."""
    try:
        result = sb.table("faculty") \
            .select("id, faculty_code, full_name, faculty_type, max_hours_per_week") \
            .eq("is_active", True) \
            .execute()
        return json.dumps(result.data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Get Subjects Tool")
def get_subjects_tool(query: str = "") -> str:
    """Fetches all subjects with their scheme details including L, T, P values."""
    try:
        result = sb.table("subjects") \
            .select("id, subject_code, subject_name, scheme_raw, lecture_hours, tutorial_hours, practical_hours, total_required_hours, semester, program") \
            .execute()
        return json.dumps(result.data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Get Allotments Tool")
def get_allotments_tool(query: str = "") -> str:
    """Fetches all 190 subject allotments with faculty, subject, batch details and roles."""
    try:
        result = sb.table("subject_allotments") \
            .select("""
                id,
                role,
                assigned_hours,
                faculty:faculty_id (id, faculty_code, max_hours_per_week),
                subject:subject_id (id, subject_name, scheme_raw, lecture_hours, tutorial_hours, practical_hours),
                batch:batch_id (id, batch_name, semester, program)
            """) \
            .execute()
        return json.dumps(result.data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Get Rooms Tool")
def get_rooms_tool(query: str = "") -> str:
    """Fetches all available rooms with their capacity and type (classroom or lab)."""
    try:
        result = sb.table("rooms") \
            .select("id, room_code, room_name, capacity, room_type") \
            .execute()
        return json.dumps(result.data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Get Time Slots Tool")
def get_timeslots_tool(query: str = "") -> str:
    """Fetches all 30 time slots (6 periods x 5 days) ordered by day and period number."""
    try:
        result = sb.table("time_slots") \
            .select("id, day, slot_number, slot_label") \
            .order("day") \
            .order("slot_number") \
            .execute()
        return json.dumps(result.data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Get Batches Tool")
def get_batches_tool(query: str = "") -> str:
    """Fetches all 19 batches with their semester and program details."""
    try:
        result = sb.table("batches") \
            .select("id, batch_name, semester, program, academic_year") \
            .execute()
        return json.dumps(result.data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Get Availability Tool")
def get_availability_tool(query: str = "") -> str:
    """Fetches faculty unavailability slots. Returns empty list if none set."""
    try:
        result = sb.table("faculty_availability") \
            .select("faculty_id, time_slot_id, reason") \
            .execute()
        return json.dumps(result.data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Check Conflict Tool")
def check_conflict_tool(assignment: str) -> str:
    """
    Checks if a proposed timetable assignment has any conflicts.
    Input must be a JSON string with keys:
    faculty_id, room_id, time_slot_id, batch_id, generation_id
    Returns {"conflict": false} or {"conflict": true, "reason": "..."}
    """
    try:
        data = json.loads(assignment)
        faculty_id    = data.get("faculty_id")
        room_id       = data.get("room_id")
        time_slot_id  = data.get("time_slot_id")
        batch_id      = data.get("batch_id")
        generation_id = data.get("generation_id")

        # Check faculty conflict
        faculty_conflict = sb.table("timetable_entries") \
            .select("id") \
            .eq("faculty_id", faculty_id) \
            .eq("time_slot_id", time_slot_id) \
            .eq("generation_id", generation_id) \
            .execute()

        if faculty_conflict.data:
            return json.dumps({
                "conflict": True,
                "reason": "Faculty already assigned in this time slot"
            })

        # Check room conflict
        room_conflict = sb.table("timetable_entries") \
            .select("id") \
            .eq("room_id", room_id) \
            .eq("time_slot_id", time_slot_id) \
            .eq("generation_id", generation_id) \
            .execute()

        if room_conflict.data:
            return json.dumps({
                "conflict": True,
                "reason": "Room already booked in this time slot"
            })

        # Check batch conflict
        batch_conflict = sb.table("timetable_entries") \
            .select("id") \
            .eq("batch_id", batch_id) \
            .eq("time_slot_id", time_slot_id) \
            .eq("generation_id", generation_id) \
            .execute()

        if batch_conflict.data:
            return json.dumps({
                "conflict": True,
                "reason": "Batch already scheduled in this time slot"
            })

        return json.dumps({"conflict": False})

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Save Timetable Tool")
def save_timetable_tool(entries: str) -> str:
    """
    Saves validated timetable entries to the database.
    Input must be a JSON string containing a list of timetable entry objects.
    Each entry needs: subject_id, faculty_id, room_id, time_slot_id, batch_id,
    generation_id, role, status
    """
    try:
        data    = json.loads(entries)
        saved   = 0
        failed  = 0
        errors  = []

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

        return json.dumps({
            "saved":  saved,
            "failed": failed,
            "errors": errors
        })

    except Exception as e:
        return json.dumps({"error": str(e)})