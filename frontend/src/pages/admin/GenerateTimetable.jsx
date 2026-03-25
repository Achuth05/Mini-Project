import { useState, useEffect } from 'react';
import TimetableGrid from '../../components/TimetableGrid';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

const DUMMY_GENERATION_ID = '00000000-0000-0000-0000-000000000006';

const AGENTS = [
  { id: 1, name: 'Data Collector Agent', desc: 'Gathering faculty preferences and room capacities...' },
  { id: 2, name: 'Constraint Analyzer', desc: 'Checking for overlapping slots and teacher availability...' },
  { id: 3, name: 'Scheduler Agent', desc: 'Generating optimal slot assignments using AI...' },
  { id: 4, name: 'Validator Agent', desc: 'Final audit of the generated schedule...' },
  { id: 5, name: 'Reporter Agent', desc: 'Formatting data for final review...' }
];

export default function GenerateTimetable() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState('');
  const [timetableData, setTimetableData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isGenerating && currentStep > 0 && currentStep <= AGENTS.length) {
      const timer = setTimeout(() => {
        setCurrentStep(prev => prev + 1);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [currentStep, isGenerating]);

  useEffect(() => {
    if (!selectedBatch) return;
    fetchTimetable(selectedBatch);
  }, [selectedBatch]);

  const fetchTimetable = async (batch) => {
    setLoading(true);
    setError('');
    const { data, error } = await supabase
      .from('s6_timetable')
      .select('*')
      .eq('generation_id', DUMMY_GENERATION_ID)
      .eq('batch', batch)
      .order('day')
      .order('period');

    if (error) {
      setError('Failed to load timetable: ' + error.message);
      setLoading(false);
      return;
    }

    const transformed = data.map(row => ({
      day: row.day,
      time_slot: String(row.period),
      subject_name: row.subject,
      faculty_name: Array.isArray(row.faculty) ? row.faculty.join(', ') : row.faculty,
      room_number: row.room_name,
      type: row.type,
      entry_type: row.entry_type
    }));

    setTimetableData(transformed);
    setLoading(false);
  };

  // UI-ONLY SWAP LOGIC
  const handleSwap = (draggedEntry, targetDay, targetPeriod) => {
    setTimetableData(prev => {
      const newData = [...prev];
      const targetPeriodStr = String(targetPeriod);
      
      // 1. Find the entry already at the target slot (if any)
      const targetEntryIndex = newData.findIndex(
        item => item.day === targetDay && String(item.time_slot) === targetPeriodStr
      );

      // 2. Find the dragged entry index
      const draggedEntryIndex = newData.findIndex(
        item => item.day === draggedEntry.day && String(item.time_slot) === String(draggedEntry.time_slot)
      );

      if (draggedEntryIndex > -1) {
        if (targetEntryIndex > -1) {
          // SWAP: Move target entry to dragged entry's old position
          const targetEntry = { ...newData[targetEntryIndex] };
          newData[targetEntryIndex] = { 
            ...newData[draggedEntryIndex], 
            day: targetDay, 
            time_slot: targetPeriodStr 
          };
          newData[draggedEntryIndex] = { 
            ...targetEntry, 
            day: draggedEntry.day, 
            time_slot: String(draggedEntry.time_slot) 
          };
        } else {
          // MOVE: Simply update the dragged entry to the new empty slot
          newData[draggedEntryIndex] = { 
            ...newData[draggedEntryIndex], 
            day: targetDay, 
            time_slot: targetPeriodStr 
          };
        }
      }
      return newData;
    });
  };

  // UI-ONLY EDIT LOGIC
  const handleEdit = (entry) => {
    const newSubject = prompt("Edit Subject Name:", entry.subject_name);
    const newFaculty = prompt("Edit Faculty Name:", entry.faculty_name);
    const newRoom = prompt("Edit Room Name:", entry.room_number);

    if (newSubject || newFaculty || newRoom) {
      setTimetableData(prev => prev.map(item => {
        if (item.day === entry.day && String(item.time_slot) === String(entry.time_slot)) {
          return {
            ...item,
            subject_name: newSubject || item.subject_name,
            faculty_name: newFaculty || item.faculty_name,
            room_number: newRoom || item.room_number
          };
        }
        return item;
      }));
    }
  };

  const startGen = () => {
    setIsGenerating(true);
    setCurrentStep(1);
    setShowPreview(false);
    setSelectedBatch('');
    setTimetableData([]);
  };

  return (
    <div style={{ animation: 'fadeUp 0.6s ease-out' }}>
      <style>{`
        .admin-card { background: #fff; border-radius: 24px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.03); border: 1px solid rgba(0,0,0,0.02); }
        .agent-item { display: flex; justify-content: space-between; align-items: center; background: #fafafa; padding: 20px; border-radius: 16px; margin-bottom: 12px; border: 1px solid transparent; transition: 0.3s; }
        .agent-active { background: #fff; border-color: #7EC8E3; box-shadow: 0 8px 20px rgba(126, 200, 227, 0.15); transform: scale(1.02); }
        .btn-primary { background: #111; color: #fff; font-family: 'Syne', sans-serif; font-weight: 700; padding: 16px 40px; border-radius: 12px; border: none; cursor: pointer; transition: 0.2s; width: 100%; }
        .btn-primary:hover { background: #222; transform: translateY(-2px); }
        .batch-selector { display: flex; gap: 12px; margin-bottom: 28px; }
        .batch-btn { padding: 10px 28px; border-radius: 10px; border: 2px solid #eee; background: #fafafa; font-family: 'Syne', sans-serif; font-weight: 700; cursor: pointer; transition: 0.2s; color: #555; }
        .batch-btn.active { background: #7EC8E3; border-color: #7EC8E3; color: #111; }
      `}</style>

      {!isGenerating && !showPreview && (
        <div className="admin-card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '20px' }}>🤖</div>
          <h2 style={{ fontFamily: 'Syne', fontWeight: 800 }}>AI Orchestrator</h2>
          <p style={{ color: '#777', marginBottom: '30px' }}>Trigger agents to generate the optimal schedule.</p>
          <button className="btn-primary" onClick={startGen} style={{ maxWidth: '300px' }}>Trigger Agents</button>
        </div>
      )}

      {isGenerating && !showPreview && (
        <div className="admin-card">
          <h3 style={{ fontFamily: 'Syne', fontWeight: 800, marginBottom: '24px' }}>System Progress</h3>
          {AGENTS.map((agent, idx) => {
            const stepNum = idx + 1;
            return (
              <div key={agent.id} className={`agent-item ${currentStep === stepNum ? 'agent-active' : ''}`} style={{ opacity: stepNum > currentStep ? 0.4 : 1 }}>
                <div>
                  <h4 style={{ fontFamily: 'Syne', fontWeight: 700 }}>{agent.name}</h4>
                  <p style={{ fontSize: '0.8rem', color: '#888' }}>{agent.desc}</p>
                </div>
                <div style={{ fontSize: '1.2rem' }}>{currentStep > stepNum ? '✅' : currentStep === stepNum ? '🔄' : '⏳'}</div>
              </div>
            );
          })}
          {currentStep > AGENTS.length && (
            <button className="btn-primary" style={{ marginTop: '20px', background: '#7EC8E3', color: '#111' }} onClick={() => setShowPreview(true)}>Review Generated Timetable →</button>
          )}
        </div>
      )}

      {showPreview && (
        <div className="admin-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '30px' }}>
            <h2 style={{ fontFamily: 'Syne', fontWeight: 800 }}>Generated Timetable</h2>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button className="btn-primary" style={{ background: '#f5f5f5', color: '#111', width: 'auto' }} onClick={() => setShowPreview(false)}>← Back</button>
              <button className="btn-primary" style={{ background: '#7EC8E3', color: '#111', width: 'auto' }} onClick={() => window.location.href = '/admin/publish'}>Publish →</button>
            </div>
          </div>

          <div className="batch-selector">
            {['A', 'B', 'C'].map(batch => (
              <button key={batch} className={`batch-btn ${selectedBatch === batch ? 'active' : ''}`} onClick={() => setSelectedBatch(batch)}>Batch {batch}</button>
            ))}
          </div>

          <div style={{ border: '1px solid #eee', borderRadius: '16px', padding: '20px', background: '#fafafa', minHeight: '400px' }}>
            {selectedBatch && !loading ? (
              <TimetableGrid 
                data={timetableData} 
                readOnly={false} 
                onSwap={handleSwap} 
                onEdit={handleEdit}
              />
            ) : (
              <p style={{ textAlign: 'center', color: '#aaa', marginTop: '100px' }}>{loading ? 'Loading...' : 'Select a batch above'}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}