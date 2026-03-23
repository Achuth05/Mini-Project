export default function TimetableGrid({ data }) {
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
  const slots = ['09:00', '10:00', '11:00', '12:00', '02:00', '03:00']

  return (
    <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: "8px" }}>
      <thead>
        <tr>
          <th style={{ fontFamily: 'Syne', fontSize: '0.8rem', opacity: 0.4 }}>TIME</th>
          {days.map(d => (
            <th key={d} style={{ fontFamily: 'Syne', fontWeight: 800, padding: '10px', color: '#111' }}>
              {d.toUpperCase()}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {slots.map(slot => (
          <tr key={slot}>
            <td style={{ fontFamily: 'DM Sans', fontWeight: 500, fontSize: '0.8rem', textAlign: 'center' }}>
              {slot}
            </td>
            {days.map(day => {
              const entry = data.find(i => i.day === day && i.time_slot.startsWith(slot))
              return (
                <td key={day} style={{ 
                  background: entry ? '#f8fcff' : 'rgba(0,0,0,0.02)',
                  border: entry ? '1px solid #7EC8E3' : '1px dashed #eee',
                  borderRadius: '12px',
                  padding: '12px',
                  minHeight: '80px',
                  minWidth: '140px'
                }}>
                  {entry && (
                    <div style={{ fontFamily: 'DM Sans' }}>
                      <p style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '4px' }}>{entry.subject_name}</p>
                      <p style={{ fontSize: '0.75rem', opacity: 0.6 }}>{entry.faculty_name}</p>
                      <p style={{ fontSize: '0.7rem', fontWeight: 700, color: '#7EC8E3', marginTop: '4px' }}>
                        ROOM {entry.room_number}
                      </p>
                    </div>
                  )}
                </td>
              )
            })}
          </tr>
        ))}
      </tbody>
    </table>
  )
}