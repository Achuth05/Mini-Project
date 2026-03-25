// File: src/pages/faculty/MyTimetable.jsx
import { useEffect, useState } from "react";
import { supabase, initializeAuthSession } from "../../supabaseClient"; 
import TimetableGrid from "../../components/TimetableGrid";

export default function MyTimetable() {
  const [schedule, setSchedule] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBatch, setSelectedBatch] = useState("A");
  const [facultyCode, setFacultyCode] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function initializeFacultyPortal() {
      try {
        setLoading(true);
        setError(null);

        // 1. Initialize auth session from localStorage token
        let user = await initializeAuthSession();
        
        // 1b. If still no user, check current session
        if (!user) {
          const { data: { user: currentUser } } = await supabase.auth.getUser();
          user = currentUser;
        }
        
        if (!user) {
          setError("You are not logged in. Please log in to view your timetable.");
          setLoading(false);
          return;
        }
        console.log("1. Logged in User ID:", user.id);

        // 2. Lookup the faculty_code
        const { data: facultyData, error: fError } = await supabase
          .from('faculty')
          .select('faculty_code')
          .eq('id', user.id)
          .single();

        if (fError || !facultyData) {
          setError("Faculty profile not found. Please contact the administrator.");
          setLoading(false);
          return;
        }

        const code = facultyData.faculty_code;
        console.log("2. Found Faculty Code:", code);
        setFacultyCode(code);

        // 3. Fetch assignments from s6_timetable
        const { data: timetableData, error: tError } = await supabase
          .from('s6_timetable')
          .select('*')
          .eq('batch', selectedBatch)
          .contains('faculty', [code])
          .eq('status', 'published');

        if (tError) throw tError;
        console.log("3. Rows found in Timetable:", timetableData?.length);

        // 4. Map to Grid Component format
        // NOTE: Field names match s6_timetable schema exactly
        const formattedData = timetableData.map(item => ({
          day: item.day,
          period: item.period,
          subject_name: item.subject,
          room_number: item.room_name,
          type: item.type
        }));

        setSchedule(formattedData);
        setError(null);

      } catch (err) {
        console.error('Timetable error:', err);
        setError(`Error loading timetable: ${err.message}`);
      } finally {
        setLoading(false);
      }
    }

    initializeFacultyPortal();
  }, [selectedBatch]);

  // Clear error when batch changes and attempt to reload
  const handleBatchChange = (batch) => {
    setError(null);
    setSelectedBatch(batch);
  };

  return (
    <div style={{ animation: "fadeIn 0.5s ease-out", padding: "20px" }}>
      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; }
        .page-title { font-family: 'Syne', sans-serif; font-size: 2.2rem; font-weight: 800; color: #111; }
        .batch-dropdown { padding: 8px 16px; border-radius: 12px; border: 1px solid #e2e8f0; font-family: 'Syne', sans-serif; font-weight: 700; outline: none; cursor: pointer; }
        .print-btn { background: #111; color: #fff; border: none; padding: 10px 20px; border-radius: 12px; cursor: pointer; font-weight: 700; }
      `}</style>
      
      <div className="page-header">
        <div>
          <h1 className="page-title">My Schedule</h1>
          <p style={{ color: "#888", marginTop: "8px", fontFamily: "'DM Sans', sans-serif" }}>
            Faculty: <strong>{facultyCode || 'Fetching...'}</strong> • Batch {selectedBatch}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
          <select 
            className="batch-dropdown"
            value={selectedBatch}
            onChange={(e) => handleBatchChange(e.target.value)}
          >
            <option value="A">Batch A</option>
            <option value="B">Batch B</option>
            <option value="C">Batch C</option>
          </select>

          {schedule.length > 0 && (
            <button className="print-btn" onClick={() => window.print()}>Print</button>
          )}
        </div>
      </div>

      {error ? (
        <div style={{ textAlign: 'center', padding: '80px 40px', border: '2px solid #fdd', borderRadius: '24px', background: '#fff5f5' }}>
          <span style={{ fontSize: '3rem', marginBottom: '16px', display: 'block' }}>⚠️</span>
          <h3 style={{ color: '#e05c5c', fontFamily: "'Syne', sans-serif", marginBottom: '12px' }}>Access Error</h3>
          <p style={{ color: '#888', fontFamily: "'DM Sans', sans-serif", marginBottom: '20px' }}>{error}</p>
          <button onClick={() => window.location.href = '/login'} style={{ background: '#e05c5c', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '8px', cursor: 'pointer', fontFamily: "'Syne', sans-serif", fontWeight: '700' }}>
            Go to Login
          </button>
        </div>
      ) : loading ? (
        <div style={{ textAlign: 'center', padding: '50px', color: '#888' }}>Loading your personalized schedule...</div>
      ) : schedule.length > 0 ? (
        <TimetableGrid data={schedule} readOnly={true} />
      ) : (
        <div style={{ textAlign: 'center', padding: '100px', border: '2px dashed #eee', borderRadius: '24px' }}>
          <h3>No Classes assigned for Batch {selectedBatch}</h3>
          <p>Try switching batches or contact the administrator.</p>
        </div>
      )}
    </div>
  );
}