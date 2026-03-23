import { useState } from 'react';
// import api from '../../services/api'; // Commented out for UI testing

// A small component for the grid so you don't need a separate file yet
const LocalTimetableGrid = ({ data }) => {
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
  const slots = ['09:00', '10:00', '11:00', '12:00', '02:00', '03:00'];

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: "8px" }}>
        <thead>
          <tr>
            <th style={{ fontFamily: 'Syne', fontSize: '0.7rem', opacity: 0.4, padding: '10px' }}>TIME</th>
            {days.map(d => (
              <th key={d} style={{ fontFamily: 'Syne', fontWeight: 800, padding: '10px', color: '#111', fontSize: '0.9rem' }}>
                {d.toUpperCase()}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {slots.map(slot => (
            <tr key={slot}>
              <td style={{ fontFamily: 'DM Sans', fontWeight: 600, fontSize: '0.75rem', textAlign: 'center', color: '#444' }}>
                {slot}
              </td>
              {days.map(day => {
                const entry = data.find(i => i.day === day && i.time_slot.startsWith(slot));
                return (
                  <td key={day} style={{ 
                    background: entry ? '#fff' : 'rgba(255,255,255,0.3)',
                    border: entry ? '1px solid #7EC8E3' : '1px dashed rgba(0,0,0,0.05)',
                    borderRadius: '16px',
                    padding: '14px',
                    minHeight: '90px',
                    minWidth: '160px',
                    transition: 'transform 0.2s ease'
                  }}>
                    {entry ? (
                      <div style={{ fontFamily: 'DM Sans' }}>
                        <p style={{ fontWeight: 700, fontSize: '0.85rem', color: '#111', marginBottom: '4px' }}>{entry.subject_name}</p>
                        <p style={{ fontSize: '0.75rem', color: '#666', marginBottom: '6px' }}>{entry.faculty_name}</p>
                        <span style={{ 
                          fontSize: '0.65rem', 
                          fontWeight: 800, 
                          color: '#7EC8E3', 
                          background: '#f0faff', 
                          padding: '3px 8px', 
                          borderRadius: '6px' 
                        }}>
                          ROOM {entry.room_number}
                        </span>
                      </div>
                    ) : null}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default function StudentTimetable() {
  const [selection, setSelection] = useState({ semester: '', batch: '' });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleViewClick = () => {
    if (!selection.semester || !selection.batch) {
      alert("Please select both Semester and Batch");
      return;
    }

    setLoading(true);
    // MOCK DATA DELAY
    setTimeout(() => {
      setData([
        { day: 'Monday', time_slot: '09:00', subject_name: 'Theory of Computation', faculty_name: 'Dr. Aris', room_number: '402' },
        { day: 'Monday', time_slot: '11:00', subject_name: 'Database Systems', faculty_name: 'Prof. Sarah', room_number: 'Lab 1' },
        { day: 'Tuesday', time_slot: '10:00', subject_name: 'Operating Systems', faculty_name: 'Dr. Kevin', room_number: '201' },
        { day: 'Wednesday', time_slot: '09:00', subject_name: 'Machine Learning', faculty_name: 'Dr. Alice', room_number: '305' },
        { day: 'Thursday', time_slot: '12:00', subject_name: 'Compiler Design', faculty_name: 'Prof. Smith', room_number: '402' },
        { day: 'Friday', time_slot: '02:00', subject_name: 'Professional Ethics', faculty_name: 'Dr. Maria', room_number: '102' }
      ]);
      setLoading(false);
    }, 800);
  };

  return (
    <div style={{ animation: "fadeUp 0.8s cubic-bezier(0.22, 1, 0.36, 1) both" }}>
      <style>{`
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .glass-card {
          background: rgba(255, 255, 255, 0.9);
          backdrop-filter: blur(10px);
          border-radius: 28px;
          padding: 40px;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
          margin-bottom: 30px;
          border: 1px solid rgba(255,255,255,0.3);
        }
        .controls {
          display: grid;
          grid-template-columns: 1fr 1fr auto;
          gap: 20px;
          align-items: center;
        }
        .custom-select {
          padding: 16px;
          border-radius: 14px;
          border: 2px solid #f0f0f0;
          font-family: 'DM Sans', sans-serif;
          font-weight: 500;
          font-size: 0.95rem;
          outline: none;
          background: #fff;
          transition: border-color 0.2s;
          cursor: pointer;
        }
        .custom-select:focus { border-color: #7EC8E3; }
        .btn-view {
          background: #111;
          color: #fff;
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 1rem;
          padding: 16px 40px;
          border-radius: 14px;
          border: none;
          cursor: pointer;
          transition: transform 0.2s, background 0.2s;
        }
        .btn-view:hover { transform: translateY(-2px); background: #222; }
        .btn-view:disabled { opacity: 0.5; cursor: not-allowed; }
      `}</style>

      {/* Selector Section */}
      <div className="glass-card">
        <h2 style={{ fontFamily: 'Syne', fontWeight: 800, fontSize: '1.8rem', marginBottom: '8px', letterSpacing: '-1px' }}>
          Your Schedule
        </h2>
        <p style={{ fontFamily: 'DM Sans', color: '#777', marginBottom: '32px', fontSize: '0.9rem' }}>
          Select your details to view the current academic timetable.
        </p>
        
        <div className="controls">
          <select 
            className="custom-select"
            value={selection.semester}
            onChange={e => setSelection({...selection, semester: e.target.value})}
          >
            <option value="">Select Semester</option>
            {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
          </select>

          <select 
            className="custom-select"
            value={selection.batch}
            onChange={e => setSelection({...selection, batch: e.target.value})}
          >
            <option value="">Select Batch</option>
            {['CSE-A', 'CSE-B', 'ECE-A', 'MECH-A'].map(b => <option key={b} value={b}>{b}</option>)}
          </select>

          <button 
            className="btn-view" 
            onClick={handleViewClick}
            disabled={loading}
          >
            {loading ? "Searching..." : "View Table"}
          </button>
        </div>
      </div>

      {/* Timetable Section */}
      {data && (
        <div className="glass-card" style={{ padding: '24px' }}>
          <LocalTimetableGrid data={data} />
        </div>
      )}
    </div>
  );
}