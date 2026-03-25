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
    """Saves S6 timetable entries. Handles truncated/partial JSON."""
    import re
    try:
        raw = entries.strip()

        # Step 1: Try direct parse
        data = None
        try:
            data = json.loads(raw)
        except Exception:
            pass

        # Step 2: If failed, extract all complete {...} objects using regex
        if data is None:
            objects_raw = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}', raw)
            data = []
            for obj_str in objects_raw:
                try:
                    obj = json.loads(obj_str)
                    # Only keep objects that look like timetable entries
                    if obj.get("batch") and obj.get("day") and obj.get("period"):
                        data.append(obj)
                except Exception:
                    continue

        # Step 3: If data is dict with schedule key, extract array
        if isinstance(data, dict):
            data = data.get("schedule", data.get("entries", []))

        if not data or not isinstance(data, list):
            return json.dumps({"saved": 0, "error": "No valid entries found"})

        # Step 4: Clean and normalize each entry
        cleaned = []
        for row in data:
            if not isinstance(row, dict):
                continue
            if not row.get("batch") or not row.get("day") or not row.get("period"):
                continue
            cleaned.append({
                "generation_id": str(row.get("generation_id", "")),
                "batch":         str(row.get("batch", "")),
                "day":           str(row.get("day", "")),
                "period":        int(row.get("period", 0)),
                "subject":       str(row.get("subject", "")),
                "type":          str(row.get("type") or row.get("entry_type", "lecture")),
                "faculty":       row.get("faculty", []),
                "room":          str(row.get("room", "")),
                "subject_id":    row.get("subject_id"),
                "faculty_ids":   row.get("faculty_ids", []),
                "batch_id":      row.get("batch_id"),
                "time_slot_id":  row.get("time_slot_id"),
                "status":        "draft"
            })

        if not cleaned:
            return json.dumps({"saved": 0, "error": "No valid entries after cleaning"})

        # Step 5: Save in chunks
        saved = 0
        errors = []
        for i in range(0, len(cleaned), 50):
            chunk = cleaned[i:i+50]
            try:
                result = sb.table("s6_timetable").insert(chunk).execute()
                saved += len(result.data)
            except Exception as e:
                errors.append(str(e))
                print(f"❌ Save Error: {e}")

        print(f"✅ Saved {saved}/{len(cleaned)} entries to s6_timetable")
        return json.dumps({"saved": saved, "total": len(cleaned), "error": errors if errors else None})

    except Exception as e:
        print(f"❌ Save Error: {e}")
        return json.dumps({"saved": 0, "error": str(e)})