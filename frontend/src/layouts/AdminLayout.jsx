// src/layouts/AdminLayout.jsx

import { Outlet, useNavigate, Link, useLocation } from 'react-router-dom';

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation(); // Used to highlight the active link

  const menuItems = [
  { name: 'Dashboard', path: '/admin' },
  { name: 'Upload Data', path: '/admin/upload' },
  { name: 'Manage Faculty', path: '/admin/faculty' },
  { name: 'Manage Rooms', path: '/admin/rooms' }, // New Link
  { name: 'Generate', path: '/admin/generate' },
  { name: 'Publish', path: '/admin/publish' },
];

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#F4F7F9', fontFamily: "'DM Sans', sans-serif" }}>
      <style>{`
        .sidebar { 
          width: 280px; 
          background: #111; 
          color: #fff; 
          padding: 40px 20px; 
          display: flex; 
          flex-direction: column;
          position: fixed;
          height: 100vh;
        }
        .nav-container {
          display: flex;
          flex-direction: column;
          gap: 10px; /* Space between links */
          margin-top: 40px;
          flex: 1;
        }
        .nav-item { 
          color: rgba(255,255,255,0.6); 
          text-decoration: none; 
          padding: 12px 16px; 
          border-radius: 12px; 
          font-family: 'Syne', sans-serif; 
          font-weight: 600;
          font-size: 0.9rem;
          transition: all 0.2s ease;
          display: block; /* Ensures they take full width */
        }
        .nav-item:hover {
          color: #fff;
          background: rgba(255,255,255,0.05);
        }
        .nav-item.active { 
          background: #7EC8E3; 
          color: #111; 
        }
        .admin-main { 
          flex: 1; 
          margin-left: 280px; /* Must match sidebar width */
          padding: 40px 60px; 
        }
        .top-bar { 
          display: flex; 
          justify-content: space-between; 
          align-items: center; 
          margin-bottom: 40px; 
        }
        .logout-btn {
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          color: #fff;
          padding: 12px;
          border-radius: 12px;
          cursor: pointer;
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          transition: 0.2s;
        }
        .logout-btn:hover {
          background: #e05c5c;
          border-color: #e05c5c;
        }
      `}</style>

      {/* Sidebar */}
      <aside className="sidebar">
        <h2 style={{ fontFamily: 'Syne', fontWeight: 800, fontSize: '1.5rem', color: '#7EC8E3', letterSpacing: '-1px' }}>
          TT Admin
        </h2>
        
        <nav className="nav-container">
          {menuItems.map(item => (
            <Link 
              key={item.path} 
              to={item.path} 
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              {item.name}
            </Link>
          ))}
        </nav>

        <button className="logout-btn" onClick={() => navigate('/login')}>
          Logout
        </button>
      </aside>

      {/* Main Content */}
      <main className="admin-main">
        <div className="top-bar">
          <h1 style={{ fontFamily: 'Syne', fontWeight: 800, fontSize: '2rem' }}>Control Center</h1>
          <div style={{ background: '#fff', padding: '10px 24px', borderRadius: '999px', boxShadow: '0 4px 12px rgba(0,0,0,0.03)', fontSize: '0.9rem' }}>
            System Status: <span style={{ color: '#7EC8E3', fontWeight: 700 }}>Active</span>
          </div>
        </div>
        
        {/* Pages like Dashboard, Upload, etc. will render here */}
        <Outlet />
      </main>
    </div>
  );
}