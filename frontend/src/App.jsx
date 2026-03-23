import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Home from "./Home";
import Login from "./Login";
import StudentLayout from './layouts/StudentLayout';
import StudentTimetable from './pages/student/StudentTimetable';
import AdminLayout from './layouts/AdminLayout';
import AdminDashboard from './pages/admin/Dashboard';
import UploadData from './pages/admin/UploadData';
import GenerateTimetable from './pages/admin/GenerateTimetable';
import ManageFaculty from './pages/admin/ManageFaculty';
import ManageRooms from './pages/admin/ManageRooms';
import Publish from './pages/admin/Publish';
import FacultyLayout from './layouts/FacultyLayout';
import MyTimetable from './pages/faculty/MyTimetable';
import MyAvailability from './pages/faculty/MyAvailability';
function App() {
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
           
              <FacultyLayout />
            
          }
        >
          <Route path="timetable" element={<MyTimetable />} />
          <Route path="availability" element={<MyAvailability />} />
        </Route>

        <Route path="/student" element={<StudentLayout />}>
          <Route index element={<StudentTimetable />} />
        </Route>
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<AdminDashboard />} />
          <Route path="upload" element={<UploadData />} />
          <Route path="generate" element={<GenerateTimetable />} />
          <Route path="faculty" element={<ManageFaculty />} />
          <Route path="rooms" element={<ManageRooms />} />
          <Route path="publish" element={<Publish />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;