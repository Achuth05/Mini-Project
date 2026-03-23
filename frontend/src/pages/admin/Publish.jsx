import { useState } from 'react';

export default function Publish() {
  const [published, setPublished] = useState(false);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
      <div style={{ textAlign: 'center', maxWidth: '500px', background: '#fff', padding: '60px', borderRadius: '32px', boxShadow: '0 20px 60px rgba(0,0,0,0.05)' }}>
        {!published ? (
          <>
            <div style={{ fontSize: '4rem', marginBottom: '20px' }}>📢</div>
            <h2 style={{ fontFamily: 'Syne', fontWeight: 800, marginBottom: '16px' }}>Ready to Publish?</h2>
            <p style={{ color: '#777', marginBottom: '40px', lineHeight: '1.6' }}>
              This will make the generated schedule visible to all students and faculty members. 
              Ensure you have reviewed all constraints.
            </p>
            <button 
              onClick={() => setPublished(true)}
              style={{ background: '#111', color: '#fff', width: '100%', padding: '16px', borderRadius: '14px', border: 'none', fontFamily: 'Syne', fontWeight: 700, cursor: 'pointer' }}
            >
              Confirm & Publish
            </button>
          </>
        ) : (
          <div style={{ animation: 'fadeUp 0.5s ease' }}>
            <div style={{ fontSize: '4rem', marginBottom: '20px' }}>🎉</div>
            <h2 style={{ fontFamily: 'Syne', fontWeight: 800, color: '#2f855a' }}>Live!</h2>
            <p style={{ color: '#777', marginTop: '10px' }}>The timetable is now official and visible to everyone.</p>
            <button 
              onClick={() => window.location.href='/admin'}
              style={{ marginTop: '30px', background: 'none', border: 'none', color: '#7EC8E3', fontWeight: 700, cursor: 'pointer' }}
            >
              ← Back to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}