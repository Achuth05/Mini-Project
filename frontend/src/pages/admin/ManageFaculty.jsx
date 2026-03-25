import { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

export default function ManageFaculty() {
  const [faculty, setFaculty] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchFaculty();
  }, []);

  const fetchFaculty = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch from faculty table where is_active = true
      const { data: facultyData, error: fError } = await supabase
        .from('faculty')
        .select('id, faculty_code')
        .eq('is_active', true)
        .order('faculty_code', { ascending: true });

      if (fError) throw fError;

      // Fetch profiles for full_name
      const { data: profilesData, error: pError } = await supabase
        .from('profiles')
        .select('id, full_name');

      if (pError) {
        console.warn('Could not fetch profiles:', pError.message);
      }

      // Fetch auth users for email
      const { data: authData, error: aError } = await supabase
        .from('auth.users')
        .select('id, email');

      if (aError) {
        console.warn('Could not fetch auth users:', aError.message);
      }

      // Merge faculty, profile, and auth data
      const merged = facultyData.map(fac => {
        const profile = profilesData?.find(p => p.id === fac.id);
        const authUser = authData?.find(a => a.id === fac.id);
        return {
          id: fac.id,
          full_name: profile?.full_name || 'N/A',
          faculty_code: fac.faculty_code,
          email: authUser?.email || 'N/A'
        };
      });

      setFaculty(merged);
    } catch (err) {
      console.error('Error fetching faculty:', err);
      setError('Failed to load faculty data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ animation: 'fadeUp 0.6s ease-out' }}>
      <div style={{ background: '#fff', padding: '32px', borderRadius: '24px', boxShadow: '0 10px 30px rgba(0,0,0,0.02)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
          <h2 style={{ fontFamily: 'Syne', fontWeight: 800 }}>Faculty Directory</h2>
          <button style={{ background: '#7EC8E3', border: 'none', padding: '10px 20px', borderRadius: '10px', fontWeight: 700, cursor: 'pointer' }}>
            + Add Faculty
          </button>
        </div>

        {error && (
          <div style={{ background: '#fee', color: '#c33', padding: '12px', borderRadius: '8px', marginBottom: '20px' }}>
            {error}
          </div>
        )}

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>Loading faculty data...</div>
        ) : faculty.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>No active faculty found</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'DM Sans' }}>
            <thead>
              <tr style={{ textAlign: 'left', color: '#888', fontSize: '0.8rem', borderBottom: '1px solid #eee' }}>
                <th style={{ padding: '12px' }}>FULL NAME</th>
                <th style={{ padding: '12px' }}>FACULTY CODE</th>
                <th style={{ padding: '12px' }}>EMAIL</th>
                <th style={{ padding: '12px' }}>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {faculty.map(f => (
                <tr key={f.id} style={{ borderBottom: '1px solid #fafafa' }}>
                  <td style={{ padding: '16px 12px', fontWeight: 600 }}>{f.full_name}</td>
                  <td style={{ padding: '16px 12px', fontFamily: 'monospace', fontSize: '0.9rem', fontWeight: 700, color: '#7EC8E3' }}>{f.faculty_code}</td>
                  <td style={{ padding: '16px 12px', color: '#666' }}>{f.email}</td>
                  <td style={{ padding: '16px 12px' }}>
                    <button style={{ background: 'none', border: 'none', cursor: 'pointer', marginRight: '10px' }}>✏️</button>
                    <button style={{ background: 'none', border: 'none', cursor: 'pointer' }}>🗑️</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}