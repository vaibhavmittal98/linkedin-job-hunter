import { Routes, Route, Link, useNavigate, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import JobDetail from "./pages/JobDetail";
import Scrape from "./pages/Scrape";
import Profile from "./pages/Profile";
import Schedule from "./pages/Schedule";
import CoverLetter from "./pages/CoverLetter";
import Signup from "./pages/Signup";
import Login from "./pages/Login";

function isLoggedIn() {
  return !!localStorage.getItem("token");
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!isLoggedIn()) return <Navigate to="/login" />;
  return <>{children}</>;
}

export default function App() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  return (
    <>
      <nav>
        <Link to="/">Jobs</Link>
        <Link to="/scrape">Scrape</Link>
        <Link to="/cover-letter">Cover Letter</Link>
        <Link to="/schedule">Schedule</Link>
        <Link to="/profile">Profile</Link>
        {isLoggedIn() ? (
          <a href="#" onClick={handleLogout} style={{ marginLeft: "auto" }}>Logout</a>
        ) : (
          <Link to="/login" style={{ marginLeft: "auto" }}>Login</Link>
        )}
      </nav>
      <div className="container">
        <Routes>
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/jobs/:id" element={<ProtectedRoute><JobDetail /></ProtectedRoute>} />
          <Route path="/scrape" element={<ProtectedRoute><Scrape /></ProtectedRoute>} />
          <Route path="/cover-letter" element={<ProtectedRoute><CoverLetter /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path="/schedule" element={<ProtectedRoute><Schedule /></ProtectedRoute>} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </div>
    </>
  );
}
