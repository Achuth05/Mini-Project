// File: src/pages/faculty/MyTimetable.jsx
import { useEffect, useState } from "react";
import TimetableGrid from "../../components/TimetableGrid"; // Adjust path as needed

export default function MyTimetable() {
  const [schedule, setSchedule] = useState([]);
  const [loading, setLoading] = useState(true);

  // Mock data for demonstration - you can replace this with your API results
  const mockData = [
    { day: "Monday", time_slot: "10:00 AM", subject_name: "Data Structures", room_number: "402" },
    { day: "Wednesday", time_slot: "02:00 PM", subject_name: "Operating Systems", room_number: "101" },
    { day: "Friday", time_slot: "09:00 AM", subject_name: "Computer Networks", room_number: "305" },
  ];

  useEffect(() => {
    async function fetchTimetable() {
      try {
        // Step 1: Get profile (e.g., const profile = await fetch('/api/auth/me')...)
        // Step 2: Get schedule (e.g., const data = await fetch(`/api/timetable?faculty_id=${profile.faculty_id}`)...)
        
        // Simulating API loading delay
        setTimeout(() => {
          // Toggle between mockData and [] to test the empty state
          setSchedule(mockData); 
          setLoading(false);
        }, 800);
      } catch (err) {
        console.error("Failed to fetch timetable", err);
        setLoading(false);
      }
    }
    fetchTimetable();
  }, []);

  return (
    <div style={{ animation: "fadeIn 0.5s ease-out" }}>
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .page-header { 
          display: flex; 
          justify-content: space-between; 
          align-items: flex-end; 
          margin-bottom: 40px; 
        }

        .page-title { 
          font-family: 'Syne', sans-serif; 
          font-size: 2.2rem; 
          font-weight: 800; 
          color: #111; 
          line-height: 1.1;
        }

        .print-btn { 
          background: #111; 
          color: #fff; 
          border: none; 
          padding: 14px 28px; 
          border-radius: 12px; 
          font-family: 'Syne', sans-serif; 
          font-weight: 700; 
          cursor: pointer; 
          transition: all 0.2s;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .print-btn:hover { 
          background: #333;
          transform: translateY(-2px); 
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .empty-state { 
          background: #fff; 
          border: 2px dashed #e0e7ff; 
          border-radius: 24px; 
          padding: 100px 40px; 
          text-align: center; 
          color: #888; 
        }

        .loading-spinner {
          font-family: 'DM Sans', sans-serif;
          color: #7EC8E3;
          font-weight: 500;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        @media print {
          .sidebar, .top-bar, .print-btn { display: none !important; }
          .content-area { padding: 0 !important; margin: 0 !important; }
          body { background: white !important; }
        }
      `}</style>

      <div className="page-header">
        <div>
          <h1 className="page-title">My Weekly<br />Schedule</h1>
          <p style={{ color: "#888", marginTop: "12px", fontFamily: "'DM Sans', sans-serif" }}>
            Spring Semester 2026 • Faculty View
          </p>
        </div>
        
        {schedule.length > 0 && (
          <button className="print-btn" onClick={() => window.print()}>
            <span>🖨️</span> Print Timetable
          </button>
        )}
      </div>

      {loading ? (
        <div className="loading-spinner">
          <div className="spinner-dot"></div> {/* Add your spinner CSS here if desired */}
          Fetching your personalized schedule...
        </div>
      ) : schedule.length > 0 ? (
        <div style={{ 
          background: "#fff", 
          padding: "24px", 
          borderRadius: "24px", 
          boxShadow: "0 20px 50px rgba(0,0,0,0.04)",
          border: "1px solid #f0f4f8"
        }}>
           <TimetableGrid data={schedule} readOnly={true} />
        </div>
      ) : (
        <div className="empty-state">
          <div style={{ fontSize: "3rem", marginBottom: "20px" }}>📅</div>
          <h3 style={{ 
            color: "#111", 
            marginBottom: "12px", 
            fontFamily: 'Syne', 
            fontSize: "1.5rem" 
          }}>
            No Schedule Published
          </h3>
          <p style={{ fontFamily: "'DM Sans', sans-serif", maxWidth: "400px", margin: "0 auto", lineHeight: "1.6" }}>
            The academic department hasn't finalized the timetable for this semester yet. 
            Once published, your classes will appear here automatically.
          </p>
        </div>
      )}
    </div>
  );
}