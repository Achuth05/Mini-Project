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
    """Get active faculty. Returns id, faculty_code."""
    rows = sb.table("faculty").select("id,faculty_code").eq("is_active", True).execute()
    return json.dumps(rows.data)

@tool("Get Subjects Tool")
def get_subjects_tool(query: str = "") -> str:
    """Get subjects. Returns id, subject_code, lecture_hours, tutorial_hours, practical_hours."""
    rows = sb.table("subjects").select("id,subject_code,lecture_hours,tutorial_hours,practical_hours").execute()
    return json.dumps(rows.data)

@tool("Get Allotments Tool")
def get_allotments_tool(semester: str = "6") -> str:
    """Get subject allotments for the specified semester."""
    batches = sb.table("batches").select("id").eq("semester", int(semester)).execute()
    batch_ids = [b["id"] for b in batches.data]
    if not batch_ids: return json.dumps([])
    rows = sb.table("subject_allotments").select("id,subject_id,faculty_id,batch_id,role").in_("batch_id", batch_ids).execute()
    return json.dumps(rows.data)

@tool("Get Time Slots Tool")
def get_timeslots_tool(query: str = "") -> str:
    """Get all 30 time slots (Mon-Fri, 6 slots each)."""
    rows = sb.table("time_slots").select("*").order("day", desc=False).order("slot_number", desc=False).execute()
    return json.dumps(rows.data)

@tool("Get Batches Tool")
def get_batches_tool(semester: str = "6") -> str:
    """Get batches for semester. Returns id, batch_name."""
    rows = sb.table("batches").select("id,batch_name,semester").eq("semester", int(semester)).execute()
    return json.dumps(rows.data)

@tool("Get Availability Tool")
def get_availability_tool(query: str = "") -> str:
    """Get faculty unavailability. Returns faculty_id, time_slot_id."""
    rows = sb.table("faculty_availability").select("faculty_id,time_slot_id").execute()
    return json.dumps(rows.data)

@tool("Check Conflict Tool")
def check_conflict_tool(assignment: str) -> str:
    """
    Check for conflicts. Input JSON: {"faculty_id", "time_slot_id", "batch_id", "generation_id"}
    """
    try:
        a = json.loads(assignment)
        ts_id = a.get("time_slot_id")
        gen_id = a.get("generation_id")
        
        # Check Faculty Conflict
        f_check = sb.table("timetable_entries").select("id").eq("time_slot_id", ts_id).eq("generation_id", gen_id).eq("faculty_id", a.get("faculty_id")).execute()
        if f_check.data: return json.dumps({"conflict": True, "reason": "Faculty busy"})

        # Check Batch Conflict
        b_check = sb.table("timetable_entries").select("id").eq("time_slot_id", ts_id).eq("generation_id", gen_id).eq("batch_id", a.get("batch_id")).execute()
        if b_check.data: return json.dumps({"conflict": True, "reason": "Batch busy"})

        return json.dumps({"conflict": False, "reason": "ok"})
    except Exception as e:
        return json.dumps({"conflict": True, "reason": str(e)})

@tool("Save Timetable Tool")
def save_timetable_tool(entries: str) -> str:
    """Saves final list of entries to DB."""
    try:
        data = json.loads(entries)
        if not data: return json.dumps({"saved": 0, "error": "No data"})
        result = sb.table("timetable_entries").insert(data).execute()
        return json.dumps({"saved": len(result.data), "error": None})
    except Exception as e:
        return json.dumps({"saved": 0, "error": str(e)})