import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import LandingPage from "./pages/LandingPage";
import { LanguageProvider } from "./i18n";
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
  return <LandingPage />;
}

export default function App() {
  return (
    <LanguageProvider>
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
    </LanguageProvider>
  );
}
