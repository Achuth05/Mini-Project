import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from crewai.tools import tool
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
    """Get active faculty. Returns id, code, max_hours."""
    rows = sb.table("faculty").select("id,faculty_code,max_hours_per_week").eq("is_active", True).execute()
    return json.dumps(rows.data)


@tool("Get Subjects Tool")
def get_subjects_tool(query: str = "") -> str:
    """Get subjects. Returns id, code, L, T, P values."""
    rows = sb.table("subjects").select("id,subject_code,lecture_hours,tutorial_hours,practical_hours").execute()
    return json.dumps(rows.data)


@tool("Get Allotments Tool")
def get_allotments_tool(semester: str = "2") -> str:
    """Get allotments for semester. Returns subject_id, faculty_id, batch_id."""
    batches = sb.table("batches").select("id").eq("semester", int(semester)).execute()
    batch_ids = [b["id"] for b in batches.data]
    if not batch_ids:
        return json.dumps([])
    rows = sb.table("subject_allotments").select("id,subject_id,faculty_id,batch_id,role").in_("batch_id", batch_ids).execute()
    return json.dumps(rows.data)


@tool("Get Rooms Tool")
def get_rooms_tool(query: str = "") -> str:
    """Get all rooms. Returns id, name, type."""
    rows = sb.table("rooms").select("id,room_name,room_type").execute()
    return json.dumps(rows.data)


@tool("Get Time Slots Tool")
def get_timeslots_tool(query: str = "") -> str:
    """Get all 30 time slots. Returns id and all fields."""
    # Use select * to avoid column name issues
    rows = sb.table("time_slots").select("*").execute()
    return json.dumps(rows.data)


@tool("Get Batches Tool")
def get_batches_tool(semester: str = "2") -> str:
    """Get batches for semester. Returns id, name."""
    rows = sb.table("batches").select("id,batch_name,semester").eq("semester", int(semester)).execute()
    return json.dumps(rows.data)


@tool("Get Availability Tool")
def get_availability_tool(query: str = "") -> str:
    """Get faculty unavailability. Returns faculty_id, time_slot_id."""
    rows = sb.table("faculty_availability").select("faculty_id,time_slot_id").execute()
    return json.dumps(rows.data)


@tool("Check Conflict Tool")
def check_conflict_tool(assignment: str) -> str:
    """Check conflicts. Input JSON: {faculty_id, room_id, time_slot_id, batch_id, generation_id}. Returns {conflict: bool, reason: str}"""
    try:
        a = json.loads(assignment)
        faculty_id = a.get("faculty_id")
        room_id = a.get("room_id")
        time_slot_id = a.get("time_slot_id")
        batch_id = a.get("batch_id")
        generation_id = a.get("generation_id")

        # Check faculty conflict
        fc = sb.table("timetable_entries").select("id").eq("time_slot_id", time_slot_id).eq("generation_id", generation_id).eq("faculty_id", faculty_id).execute()
        if fc.data:
            return json.dumps({"conflict": True, "reason": "faculty_busy"})

        # Check room conflict
        rc = sb.table("timetable_entries").select("id").eq("time_slot_id", time_slot_id).eq("generation_id", generation_id).eq("room_id", room_id).execute()
        if rc.data:
            return json.dumps({"conflict": True, "reason": "room_busy"})

        # Check batch conflict
        bc = sb.table("timetable_entries").select("id").eq("time_slot_id", time_slot_id).eq("generation_id", generation_id).eq("batch_id", batch_id).execute()
        if bc.data:
            return json.dumps({"conflict": True, "reason": "batch_busy"})

        return json.dumps({"conflict": False, "reason": "ok"})
    except Exception as e:
        return json.dumps({"conflict": True, "reason": str(e)})


@tool("Save Timetable Tool")
def save_timetable_tool(entries: str) -> str:
    """Save timetable entries. Input: JSON list of {subject_id, faculty_id, room_id, time_slot_id, batch_id, generation_id, role}"""
    try:
        data = json.loads(entries)
        if not isinstance(data, list):
            return json.dumps({"saved": 0, "error": "Input must be a list"})
        if not data:
            return json.dumps({"saved": 0, "error": "Empty list"})
        # Insert in batches of 50
        saved = 0
        for i in range(0, len(data), 50):
            chunk = data[i:i+50]
            result = sb.table("timetable_entries").insert(chunk).execute()
            saved += len(result.data)
        return json.dumps({"saved": saved, "error": None})
    except Exception as e:
        return json.dumps({"saved": 0, "error": str(e)})