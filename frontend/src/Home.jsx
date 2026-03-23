import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div style={{ fontFamily: "'Syne', sans-serif", background: "#7EC8E3", minHeight: "100vh", overflow: "hidden" }}>
      {/* Google Font */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

        * { margin: 0; padding: 0; box-sizing: border-box; }

        .navbar {
          position: fixed;
          top: 0; left: 0; right: 0;
          z-index: 100;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 18px 48px;
          transition: background 0.3s ease, backdrop-filter 0.3s ease;
        }
        .navbar.scrolled {
          background: rgba(126, 200, 227, 0.6);
          backdrop-filter: blur(12px);
        }

        .nav-logo {
          font-family: 'Syne', sans-serif;
          font-weight: 800;
          font-size: 1.1rem;
          color: #111;
          letter-spacing: -0.5px;
        }

        .nav-links {
          display: flex;
          gap: 36px;
          list-style: none;
        }
        .nav-links a {
          font-family: 'DM Sans', sans-serif;
          font-size: 0.9rem;
          font-weight: 400;
          color: #111;
          text-decoration: none;
          opacity: 0.75;
          transition: opacity 0.2s;
        }
        .nav-links a:hover { opacity: 1; }

        .nav-signin {
          font-family: 'DM Sans', sans-serif;
          font-size: 0.9rem;
          font-weight: 500;
          color: #111;
          background: rgba(0,0,0,0.08);
          border: 1px solid rgba(0,0,0,0.15);
          padding: 8px 22px;
          border-radius: 999px;
          cursor: pointer;
          transition: background 0.2s, transform 0.15s;
          text-decoration: none;
        }
        .nav-signin:hover {
          background: rgba(0,0,0,0.15);
          transform: translateY(-1px);
        }

        .hero {
          position: relative;
          width: 100%;
          height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          overflow: hidden;
        }

        .spline-bg {
          position: absolute;
          top: 0;
          left: 0;
          width: 100vw;
          height: 100vh;
          border: none;
          z-index: 0;
          display: block;
        }

        .hero-content {
          position: relative;
          z-index: 10;
          text-align: center;
          pointer-events: none;
          animation: fadeUp 0.9s cubic-bezier(0.22, 1, 0.36, 1) both;
        }

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(30px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        .hero-title {
          font-family: 'Syne', sans-serif;
          font-size: clamp(64px, 12vw, 130px);
          font-weight: 800;
          color: #111;
          line-height: 0.92;
          letter-spacing: -3px;
          mix-blend-mode: multiply;
        }

        .hero-description {
          margin-top: 20px;
          font-family: 'DM Sans', sans-serif;
          font-size: clamp(13px, 1.5vw, 16px);
          font-weight: 400;
          color: #222;
          opacity: 0.75;
          max-width: 420px;
          margin-left: auto;
          margin-right: auto;
          line-height: 1.65;
          animation: fadeUp 0.9s 0.15s cubic-bezier(0.22, 1, 0.36, 1) both;
        }

        .learn-more {
          position: absolute;
          bottom: 36px;
          left: 48px;
          z-index: 10;
          font-family: 'DM Sans', sans-serif;
          font-size: 0.85rem;
          font-weight: 500;
          color: #111;
          opacity: 0.6;
          text-decoration: none;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: opacity 0.2s, gap 0.2s;
          animation: fadeUp 0.9s 0.3s cubic-bezier(0.22, 1, 0.36, 1) both;
        }
        .learn-more:hover { opacity: 1; gap: 10px; }
        .learn-more::after {
          content: '↓';
          font-size: 1rem;
        }
      `}</style>

      {/* Navbar */}
      <nav className={`navbar${scrolled ? " scrolled" : ""}`}>
        <span className="nav-logo">TimeTablue</span>
        <ul className="nav-links">
          <li><a href="#">Home</a></li>
          <li><a href="#usecases">Use Cases</a></li>
        </ul>
        <a className="nav-signin" onClick={() => navigate("/login")}>Sign In</a>
      </nav>

      {/* Hero */}
      <section className="hero">
        <iframe
          src="https://my.spline.design/floweryellowcopycopy-B1WXRgMtalWvNp3WFRyctSGW-lRi/"
          className="spline-bg"
          title="3D Background"
          allowFullScreen
        />

        <div className="hero-content">
          <h1 className="hero-title">Time<br />Tablue</h1>
          <p className="hero-description">
            AI-powered academic timetable scheduling.<br />
            Built for admins, faculty, and students —<br />
            conflict-free, automated, and instant.
          </p>
        </div>

        <a href="#usecases" className="learn-more">Learn more</a>
      </section>

      {/* Use Cases Section */}
      <section id="usecases" style={{
        background: "#fff",
        padding: "100px 48px",
        minHeight: "60vh",
      }}>
        <style>{`
          .uc-grid {
            max-width: 960px;
            margin: 0 auto;
          }
          .uc-label {
            font-family: 'DM Sans', sans-serif;
            font-size: 0.75rem;
            font-weight: 500;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #7EC8E3;
            margin-bottom: 16px;
          }
          .uc-heading {
            font-family: 'Syne', sans-serif;
            font-size: clamp(32px, 5vw, 52px);
            font-weight: 800;
            color: #111;
            letter-spacing: -1.5px;
            margin-bottom: 56px;
            line-height: 1.05;
          }
          .uc-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 24px;
          }
          .uc-card {
            border: 1px solid #eee;
            border-radius: 16px;
            padding: 32px 28px;
            transition: transform 0.2s, box-shadow 0.2s;
          }
          .uc-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 16px 40px rgba(0,0,0,0.07);
          }
          .uc-card-icon {
            font-size: 1.8rem;
            margin-bottom: 16px;
          }
          .uc-card-title {
            font-family: 'Syne', sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            color: #111;
            margin-bottom: 10px;
          }
          .uc-card-desc {
            font-family: 'DM Sans', sans-serif;
            font-size: 0.88rem;
            color: #555;
            line-height: 1.65;
          }
        `}</style>
        <div className="uc-grid">
          <p className="uc-label">Use Cases</p>
          <h2 className="uc-heading">Who is it for?</h2>
          <div className="uc-cards">
            <div className="uc-card">
              <div className="uc-card-icon">🛠️</div>
              <div className="uc-card-title">Admin</div>
              <div className="uc-card-desc">Upload faculty, subjects, and rooms. Trigger AI scheduling, review the generated timetable, make tweaks, and publish — all from one dashboard.</div>
            </div>
            <div className="uc-card">
              <div className="uc-card-icon">🎓</div>
              <div className="uc-card-title">Faculty</div>
              <div className="uc-card-desc">Log in to view your personal weekly schedule. Set your availability preferences for the next semester so the system schedules around you.</div>
            </div>
            <div className="uc-card">
              <div className="uc-card-icon">📚</div>
              <div className="uc-card-title">Student</div>
              <div className="uc-card-desc">Select your department and semester to instantly see your full class timetable — subjects, faculty, rooms, and time slots in one clean view.</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}