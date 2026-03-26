// src/pages/admin/Dashboard.jsx
import { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

export default function AdminDashboard() {
  const [stats, setStats] = useState([
    { label: 'Total Faculty', value: '—', icon: '👥' },
    { label: 'Total Rooms', value: '—', icon: '🏫' },
    { label: 'Subjects', value: '—', icon: '📚' },
    { label: 'Status', value: 'Unpublished', icon: '⏳' },
  ]);

  const [workloadData, setWorkloadData] = useState([]);
  const [showAllFaculty, setShowAllFaculty] = useState(false); // 👈 new
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      const { data: subjects, error: subError } = await supabase
        .from('subjects')
        .select('id', { count: 'exact' });
      if (subError) console.error('Error fetching subjects:', subError);

      const { data: faculty, error: facError } = await supabase
        .from('faculty')
        .select('id', { count: 'exact' })
        .eq('is_active', true);
      if (facError) console.error('Error fetching faculty:', facError);

      const { data: rooms, error: roomError } = await supabase
        .from('rooms')
        .select('id', { count: 'exact' });
      if (roomError) console.error('Error fetching rooms:', roomError);

      setStats(prev => [
        { ...prev[0], value: faculty?.length?.toString() || '0' },
        { ...prev[1], value: rooms?.length?.toString() || '0' },
        { ...prev[2], value: subjects?.length?.toString() || '0' },
        { ...prev[3] }
      ]);

      const { data: timetableData, error: ttError } = await supabase
        .from('s6_timetable')
        .select('faculty');

      if (!ttError && timetableData && timetableData.length > 0) {
        const facultyHours = {};
        timetableData.forEach(entry => {
          if (entry.faculty && Array.isArray(entry.faculty)) {
            entry.faculty.forEach(code => {
              if (code && code !== '--') {
                facultyHours[code] = (facultyHours[code] || 0) + 1;
              }
            });
          }
        });

        const facultyCodes = Object.keys(facultyHours);
        const { data: facultyData, error: fError } = await supabase
          .from('faculty')
          .select('faculty_code, full_name')
          .in('faculty_code', facultyCodes);

        if (!fError && facultyData) {
          const facultyMap = {};
          facultyData.forEach(f => {
            if (facultyHours[f.faculty_code]) {
              facultyMap[f.faculty_code] = {
                name: f.full_name || f.faculty_code,
                hours: facultyHours[f.faculty_code],
                dept: 'N/A'
              };
            }
          });

          // 👇 Store ALL faculty sorted, no slice
          const workload = Object.values(facultyMap)
            .sort((a, b) => b.hours - a.hours);
          setWorkloadData(workload);
        }
      } else if (ttError) {
        console.error('Error fetching timetable data:', ttError);
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  // 👇 Slice here based on toggle state
  const displayedFaculty = showAllFaculty ? workloadData : workloadData.slice(0, 4);

  return (
    <div style={{ animation: 'fadeUp 0.6s ease-out' }}>
      <style>{`
        .admin-card {
          background: #fff;
          border-radius: 24px;
          padding: 30px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.02);
          border: 1px solid rgba(0,0,0,0.03);
          margin-bottom: 30px;
        }
        .workload-table {
          width: 100%;
          border-collapse: collapse;
          font-family: 'DM Sans', sans-serif;
        }
        .workload-table th {
          text-align: left;
          padding: 12px;
          color: #888;
          font-size: 0.8rem;
          text-transform: uppercase;
          border-bottom: 1px solid #eee;
        }
        .workload-table td {
          padding: 16px 12px;
          border-bottom: 1px solid #fafafa;
          font-size: 0.95rem;
        }
        .status-badge {
          background: #f0faff;
          color: #7EC8E3;
          padding: 4px 12px;
          border-radius: 999px;
          font-size: 0.75rem;
          font-weight: 700;
        }
      `}</style>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '30px' }}>
        {stats.map(s => (
          <div key={s.label} className="admin-card" style={{ marginBottom: 0 }}>
            <div style={{ fontSize: '1.8rem', marginBottom: '12px' }}>{s.icon}</div>
            <p style={{ color: '#888', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px' }}>{s.label}</p>
            <h3 style={{ fontFamily: 'Syne', fontSize: '1.8rem', fontWeight: 800 }}>{s.value}</h3>
          </div>
        ))}
      </div>

      <div className="admin-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h3 style={{ fontFamily: 'Syne', fontWeight: 800 }}>Faculty Workload</h3>
          <span className="status-badge">Semester 6</span>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>Loading faculty data...</div>
        ) : workloadData.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>No faculty data available</div>
        ) : (
          <>
            <table className="workload-table">
              <thead>
                <tr>
                  <th>Faculty Name</th>
                  <th>Department</th>
                  <th>Assigned Hours</th>
                </tr>
              </thead>
              <tbody>
                {displayedFaculty.map((f, i) => ( // 👈 use displayedFaculty
                  <tr key={i}>
                    <td style={{ fontWeight: 600 }}>{f.name}</td>
                    <td style={{ color: '#666' }}>{f.dept}</td>
                    <td style={{ color: '#111', fontWeight: 700 }}>
                      <span style={{ color: '#7EC8E3' }}>{f.hours}</span> / 20 hrs
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {workloadData.length > 4 && ( // 👈 only show button if there's more
              <div style={{ marginTop: '24px', textAlign: 'center' }}>
                <button
                  onClick={() => setShowAllFaculty(prev => !prev)} // 👈 toggle
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#7EC8E3',
                    fontFamily: 'Syne',
                    fontWeight: 700,
                    cursor: 'pointer',
                    fontSize: '0.9rem'
                  }}
                >
                  {showAllFaculty ? '← Show Less' : 'View Full Report →'} // 👈 dynamic label
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}