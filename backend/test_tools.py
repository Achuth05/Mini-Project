from app.agents.tools import (
    get_faculty_tool,
    get_subjects_tool,
    get_allotments_tool,
    get_rooms_tool,
    get_timeslots_tool,
    get_batches_tool
)

# Test each tool by calling .run() method
#print("Faculty:", get_faculty_tool.run(""))
#print("Subjects:", get_subjects_tool.run(""))
#print("Allotments:", get_allotments_tool.run(""))
#print("Rooms:", get_rooms_tool.run(""))
#print("Time Slots:", get_timeslots_tool.run(""))
print("Batches:", get_batches_tool.run(""))