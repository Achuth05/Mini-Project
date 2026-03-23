// src/pages/admin/Dashboard.jsx

export default function AdminDashboard() {
  const stats = [
    { label: 'Total Faculty', value: '42', icon: '👥' },
    { label: 'Total Rooms', value: '15', icon: '🏫' },
    { label: 'Subjects', value: '86', icon: '📚' },
    { label: 'Status', value: 'Unpublished', icon: '⏳' },
  ];

  const workloadData = [
    { name: 'Dr. Aris', hours: 18, dept: 'CSE' },
    { name: 'Prof. Sarah', hours: 14, dept: 'IT' },
    { name: 'Dr. Kevin', hours: 16, dept: 'CSE' },
    { name: 'Prof. Smith', hours: 12, dept: 'ECE' },
  ];

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

      {/* 4 Quick Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '30px' }}>
        {stats.map(s => (
          <div key={s.label} className="admin-card" style={{ marginBottom: 0 }}>
            <div style={{ fontSize: '1.8rem', marginBottom: '12px' }}>{s.icon}</div>
            <p style={{ color: '#888', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px' }}>{s.label}</p>
            <h3 style={{ fontFamily: 'Syne', fontSize: '1.8rem', fontWeight: 800 }}>{s.value}</h3>
          </div>
        ))}
      </div>

      {/* Faculty Workload Section */}
      <div className="admin-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h3 style={{ fontFamily: 'Syne', fontWeight: 800 }}>Faculty Workload</h3>
          <span className="status-badge">Semester 6</span>
        </div>
        
        <table className="workload-table">
          <thead>
            <tr>
              <th>Faculty Name</th>
              <th>Department</th>
              <th>Assigned Hours</th>
            </tr>
          </thead>
          <tbody>
            {workloadData.map((f, i) => (
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
        
        <div style={{ marginTop: '24px', textAlign: 'center' }}>
          <button style={{ 
            background: 'none', 
            border: 'none', 
            color: '#7EC8E3', 
            fontFamily: 'Syne', 
            fontWeight: 700, 
            cursor: 'pointer',
            fontSize: '0.9rem'
          }}>
            View Full Report →
          </button>
        </div>
      </div>
    </div>
  );
}