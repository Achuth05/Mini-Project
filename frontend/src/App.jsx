import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Home from "./Home";
import Login from "./Login";

import FacultyLayout from "./layouts/FacultyLayout";
import MyTimetable from "./pages/faculty/MyTimetable";
import MyAvailability from "./pages/faculty/MyAvailability";

// Dummy ProtectedRoute (replace later)
function ProtectedRoute({ children }) {
  const isLoggedIn = true; // TODO: replace with real auth
  const role = "faculty"; // TODO: dynamic

  if (!isLoggedIn) return <Navigate to="/login" />;
  if (role !== "faculty") return <Navigate to="/" />;

  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* Public */}
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />

        {/* Faculty */}
        <Route
          path="/faculty"
          element={
            <ProtectedRoute>
              <FacultyLayout />
            </ProtectedRoute>
          }
        >
          <Route path="timetable" element={<MyTimetable />} />
          <Route path="availability" element={<MyAvailability />} />
        </Route>

      </Routes>
    </BrowserRouter>
  );
}