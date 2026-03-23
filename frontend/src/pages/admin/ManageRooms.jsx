import { useState } from 'react';

export default function ManageRooms() {
  const [rooms] = useState([
    { id: 1, number: '402', type: 'Lecture Hall', capacity: 60 },
    { id: 2, number: 'Lab 1', type: 'Computer Lab', capacity: 30 },
    { id: 3, number: '201', type: 'Classroom', capacity: 45 },
  ]);

  return (
    <div style={{ animation: 'fadeUp 0.6s ease-out' }}>
      <div style={{ background: '#fff', padding: '32px', borderRadius: '24px', boxShadow: '0 10px 30px rgba(0,0,0,0.02)' }}>
        <h2 style={{ fontFamily: 'Syne', fontWeight: 800, marginBottom: '30px' }}>Room Allocation</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '20px' }}>
          {rooms.map(r => (
            <div key={r.id} style={{ border: '1px solid #eee', padding: '20px', borderRadius: '16px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', marginBottom: '10px' }}>🏫</div>
              <h3 style={{ fontFamily: 'Syne' }}>{r.number}</h3>
              <p style={{ fontSize: '0.8rem', color: '#777' }}>{r.type}</p>
              <div style={{ marginTop: '10px', fontWeight: 700, color: '#7EC8E3' }}>Cap: {r.capacity}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}