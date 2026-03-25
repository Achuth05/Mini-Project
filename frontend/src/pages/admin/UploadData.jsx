import { useState } from 'react';

export default function UploadData() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, uploading, success, error

  const handleUpload = () => {
    if (!file) return;
    setStatus('uploading');
    // Simulate Backend Validation
    setTimeout(() => {
      setStatus('success');
    }, 2000);
  };

  return (
    <div style={{ animation: 'fadeUp 0.6s ease-out' }}>
      <style>{`
        .drop-zone {
          border: 2px dashed #7EC8E3;
          background: rgba(126, 200, 227, 0.05);
          border-radius: 24px;
          padding: 60px;
          text-align: center;
          transition: 0.3s;
          cursor: pointer;
        }
        .drop-zone:hover { background: rgba(126, 200, 227, 0.1); }
        .btn-upload {
          background: #111; color: #fff; font-family: 'Syne'; font-weight: 700;
          padding: 14px 40px; border-radius: 12px; border: none; margin-top: 20px; cursor: pointer;
        }
      `}</style>

      <div style={{ background: '#fff', padding: '40px', borderRadius: '24px', boxShadow: '0 10px 30px rgba(0,0,0,0.03)' }}>
        <h2 style={{ fontFamily: 'Syne', fontWeight: 800, marginBottom: '10px' }}>Import Academic Data</h2>
        <p style={{ color: '#777', marginBottom: '30px' }}>Upload your .xlsx file containing Faculty, Subjects, and Room details.</p>

        {status === 'idle' && (
          <div className="drop-zone" onClick={() => document.getElementById('fileInput').click()}>
            <input type="file" id="fileInput" hidden onChange={(e) => setFile(e.target.files[0])} />
            <div style={{ fontSize: '3rem', marginBottom: '10px' }}>📁</div>
            <p style={{ fontFamily: 'DM Sans', fontWeight: 500 }}>
              {file ? file.name : "Drag & Drop or Click to Browse"}
            </p>
            {file && <button className="btn-upload" onClick={(e) => { e.stopPropagation(); handleUpload(); }}>Validate & Upload</button>}
          </div>
        )}

        {status === 'uploading' && (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div className="spinner" style={{ margin: '0 auto 20px' }} />
            <p style={{ fontFamily: 'Syne', fontWeight: 700 }}>Validating Constraints...</p>
          </div>
        )}

        {status === 'success' && (
          <div style={{ background: '#f0fff4', border: '1px solid #c6f6d5', padding: '20px', borderRadius: '12px', textAlign: 'center' }}>
            <p style={{ color: '#2f855a', fontWeight: 700 }}>✅ Data Loaded Successfully!</p>
            <p style={{ fontSize: '0.8rem', color: '#555' }}>20 Faculty, 8 Subjects, and 6 Rooms detected.</p>
            <button className="btn-upload" style={{ background: '#2f855a' }} onClick={() => window.location.href='/admin/generate'}>Proceed to Generation</button>
          </div>
        )}
      </div>
    </div>
  );
}