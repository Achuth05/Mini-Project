import { Outlet, useNavigate, Link, useLocation } from "react-router-dom";

export default function FacultyLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = { name: "Dr. Arshith", role: "Faculty" }; // Mock user

  const menuItems = [
    { name: "My Timetable", path: "/faculty/timetable", icon: "📅" },
    { name: "My Availability", path: "/faculty/availability", icon: "⏳" },
  ];

  return (
    <div className="faculty-root">
      {/* Global Font Import & Reset */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;700&display=swap');

        .faculty-root { 
          display: flex; 
          min-height: 100vh; 
          background: #f8fbfd; 
          font-family: 'DM Sans', sans-serif; /* Default body font */
          color: #111;
        }

        .sidebar { 
          width: 280px; 
          background: #fff; 
          border-right: 1px solid #eef2f5; 
          padding: 40px 24px; 
          display: flex; 
          flex-direction: column; 
          position: sticky;
          top: 0;
          height: 100vh;
        }

        .side-logo { 
          font-family: 'Syne', sans-serif; 
          font-weight: 800; 
          font-size: 1.4rem; 
          color: #111; 
          margin-bottom: 48px; 
          padding-left: 12px;
          letter-spacing: -0.5px;
        }

        .nav-item { 
          display: flex; 
          align-items: center; 
          gap: 12px; 
          padding: 14px 18px; 
          text-decoration: none; 
          color: #666; 
          border-radius: 12px; 
          margin-bottom: 8px; 
          transition: 0.2s; 
          font-family: 'DM Sans', sans-serif;
          font-weight: 500; 
          font-size: 0.95rem;
        }

        .nav-item:hover { background: #f0f7fa; color: #7EC8E3; }
        .nav-item.active { background: #7EC8E3; color: #fff; font-weight: 600; }
        
        .top-bar { 
          height: 80px; 
          display: flex; 
          align-items: center; 
          justify-content: flex-end; 
          padding: 0 48px; 
        }

        .user-name { 
          font-family: 'DM Sans', sans-serif; 
          font-weight: 600; 
          color: #111; 
        }

        .logout-btn { 
          background: #fff; 
          border: 1px solid #eee; 
          padding: 8px 16px; 
          border-radius: 8px; 
          cursor: pointer; 
          font-family: 'Syne', sans-serif; 
          font-weight: 700; 
          font-size: 0.75rem; 
          margin-left: 16px;
          transition: 0.2s; 
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .logout-btn:hover { background: #fff0f0; border-color: #ffcccc; color: #e05c5c; }
        
        .content-area { flex: 1; padding: 0 48px 48px; }
      `}</style>

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="side-logo">TimeTablue</div>
        <nav style={{ flex: 1 }}>
          {menuItems.map((item) => (
            <Link 
              key={item.path} 
              to={item.path} 
              className={`nav-item ${location.pathname === item.path ? "active" : ""}`}
            >
              <span style={{ fontSize: '1.1rem' }}>{item.icon}</span> {item.name}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main Container */}
      <main style={{ flex: 1 }}>
        <header className="top-bar">
          <div className="user-profile">
            <span className="user-name">{user.name}</span>
            <button className="logout-btn" onClick={() => navigate("/login")}>Logout</button>
          </div>
        </header>
        
        <div className="content-area">
          <Outlet />
        </div>
      </main>
    </div>
  );
}