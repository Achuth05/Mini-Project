import { useState, useEffect } from 'react';
import TimetableGrid from '../../components/TimetableGrid';

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

  // Mock data for the review state
  const generatedMockData = [
    { day: 'Monday', time_slot: '09:00', subject_name: 'Theory of Computation', faculty_name: 'Dr. Aris', room_number: '402' },
    { day: 'Tuesday', time_slot: '11:00', subject_name: 'Database Systems', faculty_name: 'Prof. Sarah', room_number: 'Lab 1' },
    { day: 'Wednesday', time_slot: '09:00', subject_name: 'Operating Systems', faculty_name: 'Dr. Kevin', room_number: '201' },
    { day: 'Thursday', time_slot: '12:00', subject_name: 'Machine Learning', faculty_name: 'Dr. Alice', room_number: '305' },
    { day: 'Friday', time_slot: '02:00', subject_name: 'Compiler Design', faculty_name: 'Prof. Smith', room_number: '402' }
  ];

  const startGen = () => {
    setIsGenerating(true);
    setCurrentStep(1);
    setShowPreview(false);
  };

  useEffect(() => {
    if (isGenerating && currentStep > 0 && currentStep <= AGENTS.length) {
      const timer = setTimeout(() => {
        setCurrentStep(prev => prev + 1);
      }, 2000); // 2 seconds per agent for UI testing
      return () => clearTimeout(timer);
    }
  }, [currentStep, isGenerating]);

  return (
    <div style={{ animation: 'fadeUp 0.6s ease-out' }}>
      <style>{`
        .admin-card {
          background: #fff;
          border-radius: 24px;
          padding: 40px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.03);
          border: 1px solid rgba(0,0,0,0.02);
        }
        .agent-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: #fafafa;
          padding: 20px;
          border-radius: 16px;
          margin-bottom: 12px;
          border: 1px solid transparent;
          transition: 0.3s;
        }
        .agent-active {
          background: #fff;
          border-color: #7EC8E3;
          box-shadow: 0 8px 20px rgba(126, 200, 227, 0.15);
          transform: scale(1.02);
        }
        .btn-primary {
          background: #111; color: #fff; font-family: 'Syne'; font-weight: 700;
          padding: 16px 40px; border-radius: 12px; border: none; cursor: pointer;
          width: 100%; transition: 0.2s;
        }
        .btn-primary:hover { background: #222; transform: translateY(-2px); }
      `}</style>

      {/* ── STATE 1: NOT STARTED ── */}
      {!isGenerating && !showPreview && (
        <div className="admin-card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '20px' }}>🤖</div>
          <h2 style={{ fontFamily: 'Syne', fontWeight: 800, marginBottom: '12px' }}>AI Orchestrator</h2>
          <p style={{ color: '#777', marginBottom: '30px', maxWidth: '400px', margin: '0 auto 30px' }}>
            Ready to trigger the multi-agent system? This will analyze all constraints and generate the most optimal schedule.
          </p>
          <button className="btn-primary" onClick={startGen} style={{ maxWidth: '300px' }}>
            Trigger Agents
          </button>
        </div>
      )}

      {/* ── STATE 2: GENERATING ── */}
      {isGenerating && !showPreview && (
        <div className="admin-card">
          <h3 style={{ fontFamily: 'Syne', fontWeight: 800, marginBottom: '24px' }}>System Progress</h3>
          {AGENTS.map((agent, idx) => {
            const stepNum = idx + 1;
            const isDone = currentStep > stepNum;
            const isActive = currentStep === stepNum;

            return (
              <div key={agent.id} className={`agent-item ${isActive ? 'agent-active' : ''}`} style={{ opacity: stepNum > currentStep ? 0.4 : 1 }}>
                <div>
                  <h4 style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: '1rem' }}>{agent.name}</h4>
                  <p style={{ fontSize: '0.8rem', color: '#888' }}>{agent.desc}</p>
                </div>
                <div style={{ fontSize: '1.2rem' }}>
                  {isDone ? '✅' : isActive ? '🔄' : '⏳'}
                </div>
              </div>
            );
          })}

          {currentStep > AGENTS.length && (
            <button 
              className="btn-primary" 
              style={{ marginTop: '20px', background: '#7EC8E3', color: '#111' }}
              onClick={() => setShowPreview(true)}
            >
              Review Generated Timetable →
            </button>
          )}
        </div>
      )}

      {/* ── STATE 3: REVIEW TIMETABLE ── */}
      {showPreview && (
        <div className="admin-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
            <div>
              <h2 style={{ fontFamily: 'Syne', fontWeight: 800 }}>Generated Review</h2>
              <p style={{ color: '#777', fontSize: '0.9rem' }}>Review the AI output before publishing to students.</p>
            </div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button className="btn-primary" style={{ background: '#f5f5f5', color: '#111', padding: '12px 24px' }} onClick={() => setShowPreview(false)}>
                Back
              </button>
              <button className="btn-primary" style={{ background: '#7EC8E3', color: '#111', padding: '12px 24px' }} onClick={() => window.location.href='/admin/publish'}>
                Looks Good, Publish
              </button>
            </div>
          </div>

          {/* Full Grid Preview */}
          <div style={{ border: '1px solid #eee', borderRadius: '16px', padding: '20px', background: '#fafafa' }}>
            <TimetableGrid data={generatedMockData} readOnly={true} />
          </div>
        </div>
      )}
    </div>
  );
}