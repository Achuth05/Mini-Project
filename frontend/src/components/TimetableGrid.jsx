import React from "react";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const TIMES = [
  "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", 
  "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM"
];

export default function TimetableGrid({ data = [], readOnly = true }) {
  // Helper to find a class for a specific slot
  const getEntry = (day, time) => {
    return data.find(item => item.day === day && item.time_slot === time);
  };

  return (
    <div className="timetable-container">
      <style>{`
        .timetable-container {
          width: 100%;
          overflow-x: auto;
          background: #fff;
          border-radius: 20px;
          border: 1px solid #eef2f5;
        }
        .grid-wrapper {
          display: grid;
          grid-template-columns: 100px repeat(5, 1fr);
          min-width: 800px;
        }
        .grid-header, .time-col {
          background: #fafafa;
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 0.8rem;
          color: #888;
          text-transform: uppercase;
          letter-spacing: 1px;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
          border-bottom: 1px solid #eee;
          border-right: 1px solid #eee;
        }
        .slot {
          height: 100px;
          padding: 12px;
          border-bottom: 1px solid #eee;
          border-right: 1px solid #eee;
          transition: background 0.2s;
          position: relative;
        }
        .slot:hover { background: #fcfdfe; }
        
        .entry-card {
          height: 100%;
          background: #7EC8E3;
          color: #111;
          border-radius: 12px;
          padding: 10px;
          font-family: 'DM Sans', sans-serif;
          animation: popIn 0.4s ease-out;
        }
        @keyframes popIn {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        .subject-name { font-weight: 700; font-size: 0.85rem; margin-bottom: 4px; display: block; }
        .room-tag { 
          font-size: 0.7rem; 
          background: rgba(255,255,255,0.4); 
          padding: 2px 6px; 
          border-radius: 4px; 
          font-weight: 600;
        }
        .faculty-name { 
          display: block; 
          font-size: 0.75rem; 
          margin-top: 4px; 
          opacity: 0.8;
        }
      `}</style>

      <div className="grid-wrapper">
        {/* Top-Left Empty Corner */}
        <div className="grid-header">Time</div>
        
        {/* Day Headers */}
        {DAYS.map(day => (
          <div key={day} className="grid-header">{day}</div>
        ))}

        {/* Rows */}
        {TIMES.map(time => (
          <React.Fragment key={time}>
            <div className="time-col">{time}</div>
            {DAYS.map(day => {
              const entry = getEntry(day, time);
              return (
                <div key={`${day}-${time}`} className="slot">
                  {entry && (
                    <div className="entry-card">
                      <span className="subject-name">{entry.subject_name}</span>
                      <span className="room-tag">Room {entry.room_number}</span>
                      {!readOnly && <span className="faculty-name">{entry.faculty_name}</span>}
                    </div>
                  )}
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}