import { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

const emptyForm = { full_name: '', faculty_code: '', email: '' };

export default function ManageFaculty() {
  const [faculty, setFaculty] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('add');
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  const [deleteId, setDeleteId] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchFaculty();
  }, []);

  // ── FETCH ────────────────────────────────────────────────────
  const fetchFaculty = async () => {
    try {
      setLoading(true);
      setError(null);

      const { data, error: fError } = await supabase
        .from('faculty')
        .select('id, faculty_code, is_active, full_name, email')
        .eq('is_active', true)
        .order('full_name', { ascending: true });

      if (fError) throw fError;
      setFaculty(data || []);
    } catch (err) {
      console.error('Error fetching faculty:', err);
      setError('Failed to load faculty data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // ── MODAL HELPERS ────────────────────────────────────────────
  const openAddModal = () => {
    setForm(emptyForm);
    setFormError('');
    setModalMode('add');
    setEditingId(null);
    setShowModal(true);
  };

  const openEditModal = (f) => {
    setForm({ full_name: f.full_name || '', faculty_code: f.faculty_code || '', email: f.email || '' });
    setFormError('');
    setModalMode('edit');
    setEditingId(f.id);
    setShowModal(true);
  };

  const closeModal = () => {
    if (saving) return;
    setShowModal(false);
    setForm(emptyForm);
    setFormError('');
    setEditingId(null);
  };

  // ── ADD ──────────────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!form.full_name.trim()) { setFormError('Full name is required.'); return; }
    if (!form.faculty_code.trim()) { setFormError('Faculty code is required.'); return; }
    if (!form.email.trim()) { setFormError('Email is required.'); return; }

    setSaving(true);
    setFormError('');

    try {
      if (modalMode === 'add') {
        const { error: insertError } = await supabase
          .from('faculty')
          .insert({
            full_name: form.full_name.trim(),
            faculty_code: form.faculty_code.trim().toUpperCase(),
            email: form.email.trim(),
            is_active: true
          });

        if (insertError) throw insertError;

      } else {
        const { error: updateError } = await supabase
          .from('faculty')
          .update({
            full_name: form.full_name.trim(),
            faculty_code: form.faculty_code.trim().toUpperCase(),
            email: form.email.trim()
          })
          .eq('id', editingId);

        if (updateError) throw updateError;
      }

      await fetchFaculty();
      closeModal();

    } catch (err) {
      console.error('Save error:', err);
      setFormError('Failed to save: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  // ── DELETE ───────────────────────────────────────────────────
  const handleDelete = async () => {
    setDeleting(true);
    try {
      const { error: deleteError } = await supabase
        .from('faculty')
        .delete()
        .eq('id', deleteId);

      if (deleteError) throw deleteError;

      await fetchFaculty();
      setDeleteId(null);

    } catch (err) {
      console.error('Delete error:', err);
      alert('Failed to delete: ' + err.message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div style={{ animation: 'fadeUp 0.6s ease-out' }}>
      <style>{`
        .modal-overlay {
          position: fixed; inset: 0;
          background: rgba(0,0,0,0.25);
          display: flex; align-items: center; justify-content: center;
          z-index: 1000;
        }
        .modal-box {
          background: #fff;
          border-radius: 20px;
          padding: 36px;
          width: 440px;
          max-width: 95vw;
          box-shadow: 0 20px 60px rgba(0,0,0,0.12);
          animation: popIn 0.25s ease;
        }
        @keyframes popIn {
          from { opacity: 0; transform: scale(0.95) translateY(10px); }
          to   { opacity: 1; transform: scale(1) translateY(0); }
        }
        .modal-title {
          font-family: 'Syne', sans-serif;
          font-weight: 800;
          font-size: 1.3rem;
          margin-bottom: 24px;
          color: #111;
        }
        .form-group { margin-bottom: 18px; }
        .form-label {
          display: block;
          font-size: 0.75rem;
          font-weight: 700;
          color: #888;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 7px;
          font-family: 'Syne', sans-serif;
        }
        .form-input {
          width: 100%;
          padding: 11px 14px;
          border: 1.5px solid #eee;
          border-radius: 10px;
          font-size: 0.95rem;
          font-family: 'DM Sans', sans-serif;
          outline: none;
          box-sizing: border-box;
          transition: border-color 0.2s;
          color: #111;
          background: #fff;
        }
        .form-input:focus { border-color: #7EC8E3; }
        .form-input:disabled { background: #fafafa; color: #aaa; }
        .form-error {
          color: #e55;
          font-size: 0.82rem;
          margin-bottom: 14px;
          font-family: 'DM Sans', sans-serif;
        }
        .modal-actions { display: flex; gap: 10px; margin-top: 24px; }
        .btn-cancel {
          flex: 1; padding: 12px; border-radius: 10px;
          border: 1.5px solid #eee; background: #fafafa;
          font-family: 'Syne', sans-serif; font-weight: 700;
          cursor: pointer; color: #555; transition: 0.2s;
        }
        .btn-cancel:hover:not(:disabled) { background: #f0f0f0; }
        .btn-save {
          flex: 1; padding: 12px; border-radius: 10px;
          border: none; background: #7EC8E3;
          font-family: 'Syne', sans-serif; font-weight: 700;
          cursor: pointer; color: #111; transition: 0.2s;
        }
        .btn-save:hover:not(:disabled) { background: #5ab8d8; }
        .btn-save:disabled { opacity: 0.6; cursor: not-allowed; }
        .btn-delete-confirm {
          flex: 1; padding: 12px; border-radius: 10px;
          border: none; background: #ff4d4d;
          font-family: 'Syne', sans-serif; font-weight: 700;
          cursor: pointer; color: #fff; transition: 0.2s;
        }
        .btn-delete-confirm:hover:not(:disabled) { background: #e03e3e; }
        .btn-delete-confirm:disabled { opacity: 0.6; cursor: not-allowed; }
        .fac-row:hover td { background: #fafcff; }
        .action-btn {
          border: none; border-radius: 8px;
          padding: 6px 10px; cursor: pointer;
          font-size: 0.85rem; transition: 0.2s;
        }
      `}</style>

      <div style={{ background: '#fff', padding: '32px', borderRadius: '24px', boxShadow: '0 10px 30px rgba(0,0,0,0.02)' }}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
          <div>
            <h2 style={{ fontFamily: 'Syne', fontWeight: 800, margin: 0 }}>Faculty Directory</h2>
            {!loading && (
              <p style={{ color: '#aaa', fontSize: '0.82rem', margin: '4px 0 0', fontFamily: 'DM Sans' }}>
                {faculty.length} active faculty member{faculty.length !== 1 ? 's' : ''}
              </p>
            )}
          </div>
          <button
            onClick={openAddModal}
            style={{ background: '#7EC8E3', border: 'none', padding: '10px 22px', borderRadius: '10px', fontWeight: 700, cursor: 'pointer', fontFamily: 'Syne', fontSize: '0.9rem' }}
          >
            + Add Faculty
          </button>
        </div>

        {/* Error */}
        {error && (
          <div style={{ background: '#fee', color: '#c33', padding: '12px 16px', borderRadius: '10px', marginBottom: '20px', fontFamily: 'DM Sans', fontSize: '0.9rem' }}>
            {error}
          </div>
        )}

        {/* Table */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px', color: '#aaa', fontFamily: 'DM Sans' }}>
            Loading faculty data...
          </div>
        ) : faculty.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px', color: '#aaa', fontFamily: 'DM Sans' }}>
            No active faculty found. Click "+ Add Faculty" to get started.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'DM Sans' }}>
            <thead>
              <tr style={{ textAlign: 'left', color: '#888', fontSize: '0.75rem', borderBottom: '2px solid #f0f0f0' }}>
                <th style={{ padding: '12px', fontFamily: 'Syne', letterSpacing: '0.5px' }}>FULL NAME</th>
                <th style={{ padding: '12px', fontFamily: 'Syne', letterSpacing: '0.5px' }}>FACULTY CODE</th>
                <th style={{ padding: '12px', fontFamily: 'Syne', letterSpacing: '0.5px' }}>EMAIL</th>
                <th style={{ padding: '12px', fontFamily: 'Syne', letterSpacing: '0.5px' }}>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {faculty.map(f => (
                <tr key={f.id} className="fac-row" style={{ borderBottom: '1px solid #f5f5f5' }}>
                  <td style={{ padding: '16px 12px', fontWeight: 600, color: '#111' }}>{f.full_name || '—'}</td>
                  <td style={{ padding: '16px 12px', fontFamily: 'monospace', fontSize: '0.9rem', fontWeight: 700, color: '#7EC8E3' }}>
                    {f.faculty_code}
                  </td>
                  <td style={{ padding: '16px 12px', color: '#666' }}>{f.email || '—'}</td>
                  <td style={{ padding: '16px 12px' }}>
                    <button
                      className="action-btn"
                      onClick={() => openEditModal(f)}
                      title="Edit"
                      style={{ background: '#f5f5f5', marginRight: '8px' }}
                      onMouseEnter={e => e.currentTarget.style.background = '#e8e8e8'}
                      onMouseLeave={e => e.currentTarget.style.background = '#f5f5f5'}
                    >
                      ✏️
                    </button>
                    <button
                      className="action-btn"
                      onClick={() => setDeleteId(f.id)}
                      title="Delete"
                      style={{ background: '#fff0f0' }}
                      onMouseEnter={e => e.currentTarget.style.background = '#ffe0e0'}
                      onMouseLeave={e => e.currentTarget.style.background = '#fff0f0'}
                    >
                      🗑️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* ── ADD / EDIT MODAL ── */}
      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-box" onClick={e => e.stopPropagation()}>
            <div className="modal-title">
              {modalMode === 'add' ? '+ Add New Faculty' : '✏️ Edit Faculty'}
            </div>

            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input
                className="form-input"
                placeholder="e.g. Dr. Arun Kumar"
                value={form.full_name}
                disabled={saving}
                onChange={e => setForm(p => ({ ...p, full_name: e.target.value }))}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Faculty Code</label>
              <input
                className="form-input"
                placeholder="e.g. ARK"
                value={form.faculty_code}
                disabled={saving}
                onChange={e => setForm(p => ({ ...p, faculty_code: e.target.value }))}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Email</label>
              <input
                className="form-input"
                type="email"
                placeholder="e.g. arun@college.edu"
                value={form.email}
                disabled={saving}
                onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
              />
            </div>

            {formError && <div className="form-error">⚠ {formError}</div>}

            <div className="modal-actions">
              <button className="btn-cancel" onClick={closeModal} disabled={saving}>
                Cancel
              </button>
              <button className="btn-save" onClick={handleSubmit} disabled={saving}>
                {saving ? 'Saving...' : modalMode === 'add' ? 'Add Faculty' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── DELETE CONFIRM MODAL ── */}
      {deleteId && (
        <div className="modal-overlay" onClick={() => !deleting && setDeleteId(null)}>
          <div className="modal-box" onClick={e => e.stopPropagation()} style={{ width: '380px' }}>
            <div className="modal-title" style={{ fontSize: '1.1rem' }}>🗑️ Delete Faculty?</div>
            <p style={{ color: '#666', fontFamily: 'DM Sans', fontSize: '0.9rem', margin: '0 0 8px' }}>
              Are you sure you want to delete{' '}
              <strong style={{ color: '#111' }}>
                {faculty.find(f => f.id === deleteId)?.full_name}
              </strong>?
            </p>
            <p style={{ color: '#aaa', fontFamily: 'DM Sans', fontSize: '0.8rem', margin: 0 }}>
              This will permanently remove them from the database.
            </p>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setDeleteId(null)} disabled={deleting}>
                Cancel
              </button>
              <button className="btn-delete-confirm" onClick={handleDelete} disabled={deleting}>
                {deleting ? 'Deleting...' : 'Yes, Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}