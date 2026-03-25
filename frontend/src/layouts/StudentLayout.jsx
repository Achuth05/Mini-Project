import { Outlet, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'

export default function StudentLayout() {
  const navigate = useNavigate()
  const [userName, setUserName] = useState('Student')

  useEffect(() => {
    // Get user name from localStorage (set during login)
    const name = localStorage.getItem('userName')
    if (name) setUserName(name)
  }, [])

  const handleLogout = () => {
    // Clear auth data
    localStorage.removeItem('token')
    localStorage.removeItem('userRole')
    localStorage.removeItem('userName')
    navigate('/login')
  }

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif", background: "#7EC8E3", minHeight: "100vh" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
        
        .student-nav {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px 48px;
          background: rgba(255, 255, 255, 0.8);
          backdrop-filter: blur(12px);
          position: sticky;
          top: 0;
          z-index: 100;
          border-bottom: 1px solid rgba(0,0,0,0.05);
        }
        .nav-logo {
          font-family: 'Syne', sans-serif;
          font-weight: 800;
          font-size: 1.2rem;
          color: #111;
          letter-spacing: -0.5px;
        }
        .user-chip {
          background: rgba(0,0,0,0.05);
          padding: 6px 16px;
          border-radius: 999px;
          font-size: 0.85rem;
          font-weight: 500;
        }
        .logout-btn {
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 0.85rem;
          color: #e05c5c;
          background: none;
          border: none;
          cursor: pointer;
          margin-left: 20px;
        }
      `}</style>

      <nav className="student-nav">
        <div className="flex items-center gap-4">
          <span className="nav-logo" onClick={() => navigate("/")} style={{cursor: 'pointer'}}>
            TimeTablue
          </span>
          <span className="user-chip">👋 {userName}</span>
        </div>
        <button className="logout-btn" onClick={handleLogout}>LOGOUT</button>
      </nav>

      <main style={{ padding: "40px 24px" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <Outlet />
        </div>
      </main>
    </div>
  )
}