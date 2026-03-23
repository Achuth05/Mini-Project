import React from "react";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const TIMES = [
  "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", 
  "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM"
];

export default function TimetableGrid({ data = [], readOnly = true }) {
  // Helper to find an entry. Supports both "09:00 AM" and "09:00" formats
  const getEntry = (day, time) => {
    return data.find(item => 
      item.day === day && 
      (item.time_slot === time || item.time_slot.startsWith(time.split(' ')[0]))
    );
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
          padding: 10px;
        }
        .grid-wrapper {
          display: grid;
          grid-template-columns: 100px repeat(5, 1fr);
          min-width: 900px;
        }
        .grid-header, .time-col {
          background: #fafafa;
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 0.75rem;
          color: #888;
          text-transform: uppercase;
          letter-spacing: 1px;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
          border-bottom: 1px solid #f0f0f0;
        }
        .slot {
          min-height: 110px;
          padding: 8px;
          border-bottom: 1px solid #f8f8f8;
          border-right: 1px solid #f8f8f8;
          transition: background 0.2s;
        }
        .slot-empty {
          border: 1px dashed #eee;
          border-radius: 12px;
          height: 100%;
          background: rgba(0,0,0,0.01);
        }
        .entry-card {
          height: 100%;
          background: #f8fcff;
          border: 1.5px solid #7EC8E3;
          border-radius: 14px;
          padding: 12px;
          font-family: 'DM Sans', sans-serif;
          animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
          display: flex;
          flex-direction: column;
          justify-content: space-between;
        }
        @keyframes popIn {
          from { opacity: 0; transform: translateY(10px) scale(0.95); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .subject-name { font-weight: 700; font-size: 0.9rem; color: #111; line-height: 1.2; }
        .faculty-name { font-size: 0.75rem; color: #666; margin-top: 4px; display: block; }
        .room-tag { 
          font-size: 0.65rem; 
          background: #7EC8E3; 
          color: #fff;
          padding: 3px 8px; 
          border-radius: 6px; 
          font-weight: 700;
          align-self: flex-start;
          margin-top: 8px;
          text-transform: uppercase;
        }
      `}</style>

      <div className="grid-wrapper">
        <div className="grid-header">Time</div>
        {DAYS.map(day => <div key={day} className="grid-header">{day}</div>)}

        {TIMES.map(time => (
          <React.Fragment key={time}>
            <div className="time-col">{time}</div>
            {DAYS.map(day => {
              const entry = getEntry(day, time);
              return (
                <div key={`${day}-${time}`} className="slot">
                  {entry ? (
                    <div className="entry-card">
                      <div>
                        <span className="subject-name">{entry.subject_name}</span>
                        <span className="faculty-name">{entry.faculty_name}</span>
                      </div>
                      <span className="room-tag">Room {entry.room_number}</span>
                    </div>
                  ) : (
                    <div className="slot-empty" />
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