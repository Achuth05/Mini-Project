import { useState } from 'react';

export default function ManageFaculty() {
  const [faculty] = useState([
    { id: 1, name: 'Dr. Aris', dept: 'CSE', email: 'aris@univ.edu', load: '18h' },
    { id: 2, name: 'Prof. Sarah', dept: 'IT', email: 'sarah@univ.edu', load: '14h' },
    { id: 3, name: 'Dr. Kevin', dept: 'CSE', email: 'kevin@univ.edu', load: '16h' },
  ]);

  return (
    <div style={{ animation: 'fadeUp 0.6s ease-out' }}>
      <div style={{ background: '#fff', padding: '32px', borderRadius: '24px', boxShadow: '0 10px 30px rgba(0,0,0,0.02)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
          <h2 style={{ fontFamily: 'Syne', fontWeight: 800 }}>Faculty Directory</h2>
          <button style={{ background: '#7EC8E3', border: 'none', padding: '10px 20px', borderRadius: '10px', fontWeight: 700, cursor: 'pointer' }}>
            + Add Faculty
          </button>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'DM Sans' }}>
          <thead>
            <tr style={{ textAlign: 'left', color: '#888', fontSize: '0.8rem', borderBottom: '1px solid #eee' }}>
              <th style={{ padding: '12px' }}>NAME</th>
              <th style={{ padding: '12px' }}>DEPARTMENT</th>
              <th style={{ padding: '12px' }}>EMAIL</th>
              <th style={{ padding: '12px' }}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {faculty.map(f => (
              <tr key={f.id} style={{ borderBottom: '1px solid #fafafa' }}>
                <td style={{ padding: '16px 12px', fontWeight: 600 }}>{f.name}</td>
                <td style={{ padding: '16px 12px' }}>{f.dept}</td>
                <td style={{ padding: '16px 12px', color: '#666' }}>{f.email}</td>
                <td style={{ padding: '16px 12px' }}>
                  <button style={{ background: 'none', border: 'none', cursor: 'pointer', marginRight: '10px' }}>✏️</button>
                  <button style={{ background: 'none', border: 'none', cursor: 'pointer' }}>🗑️</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}