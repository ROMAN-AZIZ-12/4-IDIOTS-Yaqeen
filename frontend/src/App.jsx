import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ApplicationForm from "./pages/ApplicationForm";
import BorrowerDashboard from "./pages/BorrowerDashboard";
import Login from "./pages/Login";
import OfficerDashboard from "./pages/OfficerDashboard";
import OfficerDetail from "./pages/OfficerDetail";
import OfficerLogin from "./pages/OfficerLogin";
import Signup from "./pages/Signup";
import StatusPage from "./pages/StatusPage";
import UploadPage from "./pages/UploadPage";
import { getUser } from "./utils";

function RoleRoute({ role, children }) {
  const user = getUser();
  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) return <Navigate to="/" replace />;
  return children;
}

function Home() {
  const user = getUser();
  if (user?.role === "borrower") return <Navigate to="/borrower" replace />;
  if (user?.role === "officer") return <Navigate to="/officer" replace />;
  return (
    <div className="hero-card">
      <h1>Yaqeen</h1>
      <p>Small-business loan file preparation for Pakistan.</p>
      <p><em>The AI extracts. Code scores. The officer decides.</em></p>
      <div className="actions">
        <a href="/signup"><button>Get started</button></a>
        <a href="/login"><button>Log in</button></a>
        <a href="/officer-login"><button className="secondary">Officer login</button></a>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/login" element={<Login />} />
          <Route path="/officer-login" element={<OfficerLogin />} />
          <Route path="/borrower" element={<RoleRoute role="borrower"><BorrowerDashboard /></RoleRoute>} />
          <Route path="/apply" element={<RoleRoute role="borrower"><ApplicationForm /></RoleRoute>} />
          <Route path="/upload/:id" element={<RoleRoute role="borrower"><UploadPage /></RoleRoute>} />
          <Route path="/status/:id" element={<RoleRoute role="borrower"><StatusPage /></RoleRoute>} />
          <Route path="/officer" element={<RoleRoute role="officer"><OfficerDashboard /></RoleRoute>} />
          <Route path="/officer/application/:id" element={<RoleRoute role="officer"><OfficerDetail /></RoleRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}
