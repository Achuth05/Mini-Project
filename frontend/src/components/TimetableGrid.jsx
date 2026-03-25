// File: src/components/TimetableGrid.jsx
import React from 'react';

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const PERIODS = [1, 2, 3, 4, 5, 6];

// Helper to map period numbers to display times (matching your screenshot)
const timeSlots = {
  1: "09:00 AM",
  2: "10:00 AM",
  3: "11:00 AM",
  4: "12:00 PM",
  5: "02:00 PM",
  6: "03:00 PM"
};

export default function TimetableGrid({ data = [] }) {
  // Function to find a class for a specific day and period
  const findEntry = (day, period) => {
    return data.find(item => item.day === day && item.period === period);
  };

  return (
    <div className="timetable-container">
      <style>{`
        .timetable-table { width: 100%; border-collapse: separate; border-spacing: 8px; table-layout: fixed; }
        .timetable-table th { 
          font-family: 'Syne', sans-serif; text-transform: uppercase; font-size: 0.75rem; 
          color: #94a3b8; padding: 15px; letter-spacing: 0.1em; 
        }
        .time-col { 
          font-family: 'DM Sans', sans-serif; font-size: 0.8rem; font-weight: 700; 
          color: #64748b; width: 100px; text-align: left; 
        }
        .slot { 
          background: #f8fafc; border: 2px dashed #e2e8f0; border-radius: 16px; 
          height: 100px; transition: all 0.3s ease; padding: 12px;
        }
        .slot.filled { 
          background: #ffffff; border: 1px solid #e2e8f0; border-bottom: 4px solid #7EC8E3;
          box-shadow: 0 4px 12px rgba(0,0,0,0.03); border-style: solid;
        }
        .subject-name { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 0.9rem; color: #111; margin-bottom: 8px; }
        .room-badge { 
          display: inline-block; background: #7EC8E3; color: white; padding: 2px 8px; 
          border-radius: 6px; font-size: 0.7rem; font-weight: 800; font-family: 'DM Sans';
        }
        .type-label { font-size: 0.65rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; margin-top: 4px; }
      `}</style>

      <table className="timetable-table">
        <thead>
          <tr>
            <th style={{ width: '100px' }}>Time</th>
            {DAYS.map(day => <th key={day}>{day}</th>)}
          </tr>
        </thead>
        <tbody>
          {PERIODS.map(period => (
            <tr key={period}>
              <td className="time-col">{timeSlots[period]}</td>
              {DAYS.map(day => {
                const entry = findEntry(day, period);
                return (
                  <td key={`${day}-${period}`}>
                    <div className={`slot ${entry ? 'filled' : ''}`}>
                      {entry && (
                        <>
                          <div className="subject-name">{entry.subject_name}</div>
                          <div className="room-badge">{entry.room_number}</div>
                          <div className="type-label">{entry.type}</div>
                        </>
                      )}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}