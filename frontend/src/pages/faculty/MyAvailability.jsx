// File: src/pages/faculty/MyAvailability.jsx
export default function MyAvailability() {
  return (
    <div style={{ maxWidth: "600px" }}>
      <style>{`
        .status-card { background: #fff; padding: 40px; border-radius: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.03); border: 1px solid #eef2f5; }
        .info-tag { display: inline-block; background: #f0f7fa; color: #7EC8E3; padding: 6px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 20px; }
      `}</style>

      <h1 style={{ fontFamily: 'Syne', fontSize: "2.2rem", fontWeight: 800, marginBottom: "32px" }}>Availability</h1>
      
      <div className="status-card">
        <span className="info-tag">System Managed</span>
        <h2 style={{ fontFamily: 'Syne', fontSize: "1.2rem", fontWeight: 700, marginBottom: "12px" }}>Managed by Administrator</h2>
        <p style={{ color: "#555", lineHeight: "1.6", marginBottom: "24px" }}>
          Your availability preferences are currently managed through the central administration data upload. 
          The AI scheduler uses these constraints to ensure you are not booked during your restricted hours.
        </p>
        <div style={{ padding: "16px", background: "#fafafa", borderRadius: "12px", fontSize: "0.85rem", color: "#888" }}>
          <strong>Need to make changes?</strong><br />
          Please contact your department coordinator to update your preferred time slots for the upcoming semester.
        </div>
      </div>
    </div>
  );
}