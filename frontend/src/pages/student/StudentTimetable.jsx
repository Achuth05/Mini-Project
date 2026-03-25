import { useState, useEffect } from 'react';
import { supabase, initializeAuthSession } from '../../supabaseClient';

// Grid component to display timetable
const TimetableGrid = ({ data }) => {
  const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
  const PERIODS = [1, 2, 3, 4, 5, 6];

  const timeSlots = {
    1: "09:00 AM",
    2: "10:00 AM",
    3: "11:00 AM",
    4: "12:00 PM",
    5: "02:00 PM",
    6: "03:00 PM"
  };

  const findEntry = (day, period) => {
    return data.find(item => item.day === day && item.period === period);
  };

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: "8px", tableLayout: "fixed" }}>
        <thead>
          <tr>
            <th style={{ width: '100px', fontFamily: 'Syne', fontSize: '0.75rem', color: '#94a3b8', padding: '15px', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Time</th>
            {DAYS.map(day => (
              <th key={day} style={{ fontFamily: 'Syne', fontWeight: 800, padding: '15px', color: '#111', fontSize: '0.85rem', textTransform: 'uppercase' }}>
                {day}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {PERIODS.map(period => (
            <tr key={period}>
              <td style={{ fontFamily: 'DM Sans', fontWeight: 700, fontSize: '0.8rem', color: '#64748b', width: '100px', textAlign: 'left' }}>
                {timeSlots[period]}
              </td>
              {DAYS.map(day => {
                const entry = findEntry(day, period);
                return (
                  <td key={`${day}-${period}`} style={{
                    background: entry ? '#ffffff' : '#f8fafc',
                    border: entry ? '1px solid #e2e8f0' : '2px dashed #e2e8f0',
                    borderBottomWidth: entry ? '4px' : '2px',
                    borderBottomColor: entry ? '#7EC8E3' : '#e2e8f0',
                    borderRadius: '16px',
                    padding: '12px',
                    minHeight: '100px',
                    transition: 'all 0.3s ease'
                  }}>
                    {entry && (
                      <div>
                        <p style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: '0.9rem', color: '#111', marginBottom: '8px', margin: 0 }}>
                          {entry.subject}
                        </p>
                        <span style={{
                          display: 'inline-block',
                          background: '#7EC8E3',
                          color: 'white',
                          padding: '2px 8px',
                          borderRadius: '6px',
                          fontSize: '0.7rem',
                          fontWeight: 800,
                          fontFamily: 'DM Sans',
                          marginBottom: '4px'
                        }}>
                          {entry.room_name}
                        </span>
                        <p style={{ fontFamily: 'DM Sans', fontSize: '0.65rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700, marginTop: '4px', margin: 0 }}>
                          {entry.type}
                        </p>
                      </div>
                    )}
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
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);

  // Initialize auth on component mount
  useEffect(() => {
    const initAuth = async () => {
      const authUser = await initializeAuthSession();
      if (!authUser) {
        const { data: { user: currentUser } } = await supabase.auth.getUser();
        setUser(currentUser);
      } else {
        setUser(authUser);
      }
    };
    initAuth();
  }, []);

  const handleViewTimetable = async () => {
    if (!selection.semester || !selection.batch) {
      setError("Please select both Semester and Batch");
      return;
    }

    if (!user) {
      setError("Please log in to view the timetable");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Fetch timetable entries from s6_timetable for selected batch
      const { data: timetableData, error: tError } = await supabase
        .from('s6_timetable')
        .select('*')
        .eq('batch', selection.batch)
        .eq('status', 'published')
        .order('day', { ascending: true })
        .order('period', { ascending: true });

      if (tError) throw tError;

      if (!timetableData || timetableData.length === 0) {
        setError(`No timetable found for Batch ${selection.batch}`);
        setData(null);
        setLoading(false);
        return;
      }

      console.log(`✓ Loaded ${timetableData.length} entries for Batch ${selection.batch}`);
      setData(timetableData);
      setError(null);
    } catch (err) {
      console.error('Timetable fetch error:', err);
      setError(`Unable to load timetable: ${err.message}`);
      setData(null);
    } finally {
      setLoading(false);
    }
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
        .error-box {
          background: #fff5f5;
          border: 2px solid #fdd;
          border-radius: 14px;
          padding: 16px;
          color: #e05c5c;
          font-family: 'DM Sans', sans-serif;
          margin-bottom: 20px;
        }
      `}</style>

      {/* Selector Section */}
      <div className="glass-card">
        <h2 style={{ fontFamily: 'Syne', fontWeight: 800, fontSize: '1.8rem', marginBottom: '8px', letterSpacing: '-1px' }}>
          Your Schedule
        </h2>
        <p style={{ fontFamily: 'DM Sans', color: '#777', marginBottom: '32px', fontSize: '0.9rem' }}>
          Select your semester and batch to view the current academic timetable.
        </p>
        
        {error && <div className="error-box">⚠️ {error}</div>}
        
        <div className="controls">
          <select 
            className="custom-select"
            value={selection.semester}
            onChange={e => setSelection({...selection, semester: e.target.value})}
            disabled={loading}
          >
            <option value="">Select Semester</option>
            {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
          </select>

          <select 
            className="custom-select"
            value={selection.batch}
            onChange={e => setSelection({...selection, batch: e.target.value})}
            disabled={loading}
          >
            <option value="">Select Batch</option>
            <option value="A">Batch A</option>
            <option value="B">Batch B</option>
            <option value="C">Batch C</option>
          </select>

          <button 
            className="btn-view" 
            onClick={handleViewTimetable}
            disabled={loading || !selection.semester || !selection.batch}
          >
            {loading ? "Loading..." : "View Timetable"}
          </button>
        </div>
      </div>

      {/* Timetable Section */}
      {data && data.length > 0 && (
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontFamily: 'Syne', fontWeight: 700, marginBottom: '20px', color: '#111' }}>
            Batch {selection.batch} - Semester {selection.semester} Schedule
          </h3>
          <TimetableGrid data={data} />
        </div>
      )}

      {data && data.length === 0 && !loading && (
        <div className="glass-card" style={{ textAlign: 'center', padding: '60px 40px' }}>
          <span style={{ fontSize: '2rem', display: 'block', marginBottom: '16px' }}>📭</span>
          <h3 style={{ fontFamily: 'Syne', color: '#111', marginBottom: '8px' }}>No classes found</h3>
          <p style={{ fontFamily: 'DM Sans', color: '#888' }}>There are no classes scheduled for this batch.</p>
        </div>
      )}
    </div>
  );
}