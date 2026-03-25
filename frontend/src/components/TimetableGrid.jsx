import React from "react";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

const PERIOD_LABELS = {
  1: "Period 1",
  2: "Period 2",
  3: "Period 3",
  4: "Period 4",
  5: "Period 5",
  6: "Period 6",
};

export default function TimetableGrid({ data = [], readOnly = true, onSwap, onEdit }) {

  const getEntry = (day, period) => {
    return data.find(
      item => item.day === day && String(item.time_slot) === String(period)
    );
  };

  const handleDragStart = (e, entry) => {
    if (readOnly) return;
    e.dataTransfer.setData("draggedEntry", JSON.stringify(entry));
  };

  const handleDrop = (e, targetDay, targetPeriod) => {
    e.preventDefault();
    if (readOnly) return;
    const draggedEntry = JSON.parse(e.dataTransfer.getData("draggedEntry"));
    onSwap(draggedEntry, targetDay, targetPeriod);
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
          min-height: 94px;
          background: rgba(0,0,0,0.01);
        }
        .entry-card {
          height: 100%;
          min-height: 94px;
          background: #f8fcff;
          border: 1.5px solid #7EC8E3;
          border-radius: 14px;
          padding: 12px;
          font-family: 'DM Sans', sans-serif;
          animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          cursor: ${readOnly ? 'default' : 'grab'};
        }
        .entry-card:active { cursor: grabbing; }
        .entry-card.lab {
          background: #fff8f0;
          border-color: #f4a261;
        }
        @keyframes popIn {
          from { opacity: 0; transform: translateY(10px) scale(0.95); }
          to   { opacity: 1; transform: translateY(0)  scale(1);    }
        }
        .subject-name  { font-weight: 700; font-size: 0.85rem; color: #111; line-height: 1.3; }
        .faculty-name  { font-size: 0.72rem; color: #666; margin-top: 4px; display: block; }
        .type-tag      { font-size: 0.62rem; color: #999; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.5px; }
        .room-tag {
          font-size: 0.62rem;
          background: #7EC8E3;
          color: #fff;
          padding: 3px 8px;
          border-radius: 6px;
          font-weight: 700;
          align-self: flex-start;
          margin-top: 8px;
          text-transform: uppercase;
        }
        .room-tag.lab { background: #f4a261; }
      `}</style>

      <div className="grid-wrapper">
        <div className="grid-header">Period</div>
        {DAYS.map(day => (
          <div key={day} className="grid-header">{day}</div>
        ))}

        {[1, 2, 3, 4, 5, 6].map(period => (
          <React.Fragment key={period}>
            <div className="time-col">{PERIOD_LABELS[period]}</div>
            {DAYS.map(day => {
              const entry = getEntry(day, period);
              const isLab = entry?.type === 'lab' || entry?.entry_type === 'lab';
              return (
                <div 
                  key={`${day}-${period}`} 
                  className="slot"
                  onDragOver={(e) => !readOnly && e.preventDefault()}
                  onDrop={(e) => handleDrop(e, day, period)}
                >
                  {entry ? (
                    <div 
                      className={`entry-card ${isLab ? 'lab' : ''}`}
                      draggable={!readOnly}
                      onDragStart={(e) => handleDragStart(e, entry)}
                      onClick={() => !readOnly && onEdit(entry)}
                    >
                      <div>
                        <span className="subject-name">{entry.subject_name}</span>
                        <span className="faculty-name">{entry.faculty_name}</span>
                        {entry.type && (
                          <span className="type-tag">{entry.type}</span>
                        )}
                      </div>
                      <span className={`room-tag ${isLab ? 'lab' : ''}`}>
                        {entry.room_number}
                      </span>
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