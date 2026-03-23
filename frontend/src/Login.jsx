import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("Please fill in all fields.");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.message || "Invalid credentials. Please try again.");
      }

      // 1. Save authentication data
      localStorage.setItem("token", data.token);
      localStorage.setItem("userRole", data.role); // Storing role from DB
      localStorage.setItem("userName", data.name || "User");

      // 2. Redirect based on the role stored in DB
      if (data.role === "admin") {
        navigate("/admin");
      } else if (data.role === "faculty") {
        navigate("/faculty/timetable");
      } else if (data.role === "student") {
        navigate("/student");
      } else {
        setError("Unauthorized role. Contact admin.");
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleForgot = async (e) => {
    e.preventDefault();
    setError("");
    if (!email) { setError("Please enter your email address."); return; }
    
    setLoading(true);
    try {
      const res = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      
      if (!res.ok) throw new Error("Could not send reset link.");
      
      setMode("sent");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ fontFamily: "'Syne', sans-serif", minHeight: "100vh", background: "#7EC8E3", display: "flex", alignItems: "center", justifyContent: "center", padding: "24px" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        .login-wrap { width: 100%; max-width: 440px; animation: popIn 0.6s cubic-bezier(0.22, 1, 0.36, 1) both; }
        @keyframes popIn { from { opacity: 0; transform: translateY(24px) scale(0.98); } to { opacity: 1; transform: translateY(0) scale(1); } }
        .login-card { background: #fff; border-radius: 24px; padding: 48px 44px; box-shadow: 0 24px 64px rgba(0,0,0,0.12); }
        .back-home { display: inline-flex; align-items: center; gap: 6px; font-family: 'DM Sans', sans-serif; font-size: 0.82rem; color: #111; opacity: 0.55; text-decoration: none; margin-bottom: 36px; cursor: pointer; transition: opacity 0.2s; background: none; border: none; }
        .back-home:hover { opacity: 1; }
        .login-logo { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.5rem; color: #111; letter-spacing: -1px; margin-bottom: 6px; }
        .login-subtitle { font-family: 'DM Sans', sans-serif; font-size: 0.88rem; color: #888; margin-bottom: 36px; }
        .login-title { font-family: 'Syne', sans-serif; font-size: 1.65rem; font-weight: 800; color: #111; letter-spacing: -0.8px; margin-bottom: 28px; line-height: 1.1; }
        .field { margin-bottom: 16px; }
        .field label { display: block; font-family: 'DM Sans', sans-serif; font-size: 0.78rem; font-weight: 500; color: #555; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 7px; }
        .field-inner { position: relative; }
        .field input { width: 100%; padding: 13px 16px; border: 1.5px solid #e8e8e8; border-radius: 12px; font-family: 'DM Sans', sans-serif; font-size: 0.95rem; color: #111; background: #fafafa; outline: none; transition: border-color 0.2s, background 0.2s; }
        .field input:focus { border-color: #7EC8E3; background: #fff; }
        .toggle-pass { position: absolute; right: 14px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 1rem; opacity: 0.4; transition: opacity 0.2s; }
        .toggle-pass:hover { opacity: 0.8; }
        .forgot-link { display: block; text-align: right; font-family: 'DM Sans', sans-serif; font-size: 0.82rem; color: #7EC8E3; cursor: pointer; margin-top: 6px; margin-bottom: 24px; background: none; border: none; text-decoration: underline; text-underline-offset: 3px; }
        .error-msg { font-family: 'DM Sans', sans-serif; font-size: 0.83rem; color: #e05c5c; background: #fff0f0; border: 1px solid #fdd; border-radius: 10px; padding: 10px 14px; margin-bottom: 16px; }
        .btn-primary { width: 100%; padding: 14px; background: #111; color: #fff; border: none; border-radius: 12px; font-family: 'Syne', sans-serif; font-size: 0.95rem; font-weight: 700; letter-spacing: 0.3px; cursor: pointer; transition: background 0.2s, transform 0.15s; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .btn-primary:hover:not(:disabled) { background: #222; transform: translateY(-1px); }
        .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
        .spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .divider { display: flex; align-items: center; gap: 12px; margin: 24px 0 0; }
        .divider-line { flex: 1; height: 1px; background: #eee; }
        .divider-text { font-family: 'DM Sans', sans-serif; font-size: 0.78rem; color: #bbb; }
        .role-note { margin-top: 20px; font-family: 'DM Sans', sans-serif; font-size: 0.8rem; color: #aaa; text-align: center; line-height: 1.5; }
      `}</style>

      <div className="login-wrap">
        <button className="back-home" onClick={() => navigate("/")}>← Back to home</button>

        <div className="login-card">
          {mode === "login" && (
            <>
              <div className="login-logo">Time<span>Tablue</span></div>
              <p className="login-subtitle">Academic Timetable Scheduling</p>
              <h2 className="login-title">Welcome back.</h2>

              <form onSubmit={handleLogin}>
                <div className="field">
                  <label>Email</label>
                  <input type="email" placeholder="you@university.edu" value={email} onChange={e => setEmail(e.target.value)} />
                </div>

                <div className="field">
                  <label>Password</label>
                  <div className="field-inner">
                    <input type={showPass ? "text" : "password"} placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} />
                    <button type="button" className="toggle-pass" onClick={() => setShowPass(!showPass)}>
                      {showPass ? "🙈" : "👁️"}
                    </button>
                  </div>
                </div>

                <button type="button" className="forgot-link" onClick={() => setMode("forgot")}>Forgot password?</button>

                {error && <div className="error-msg">⚠️ {error}</div>}

                <button className="btn-primary" type="submit" disabled={loading}>
                  {loading ? <div className="spinner" /> : "Sign In →"}
                </button>
              </form>

              <div className="divider">
                <div className="divider-line" />
                <span className="divider-text">role assigned automatically</span>
                <div className="divider-line" />
              </div>
              <p className="role-note">Your access level is determined by your account.</p>
            </>
          )}

          {mode === "forgot" && (
            <form onSubmit={handleForgot}>
               <h2 className="login-title">Reset Password</h2>
               <div className="field">
                  <label>Email</label>
                  <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@university.edu" />
               </div>
               {error && <div className="error-msg">⚠️ {error}</div>}
               <button className="btn-primary" type="submit" disabled={loading}>Send Reset Link</button>
               <button className="back-home" style={{marginTop: '20px'}} onClick={() => setMode("login")}>← Back to Login</button>
            </form>
          )}

          {mode === "sent" && (
            <div style={{textAlign: 'center'}}>
              <span style={{fontSize: '3rem'}}>📬</span>
              <h2 className="login-title">Check your inbox.</h2>
              <p style={{fontFamily: 'DM Sans', color: '#666', marginBottom: '20px'}}>Reset link sent to {email}</p>
              <button className="btn-primary" onClick={() => setMode("login")}>Back to Login</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}