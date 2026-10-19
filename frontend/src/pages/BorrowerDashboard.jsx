import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function BorrowerDashboard() {
  const [apps, setApps] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listApplications()
      .then(setApps)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading...</p>;

  return (
    <div className="card">
      <h1>My applications</h1>
      {error && <p className="error">{error}</p>}
      {apps.length === 0 ? (
        <>
          <p>You do not have any applications yet.</p>
          <Link to="/apply"><button>Start an application</button></Link>
        </>
      ) : (
        <ul className="app-list">
          {apps.map((app) => (
            <li key={app.id}>
              <Link to={`/status/${app.id}`}>
                <strong>{app.bank_name}</strong>
                <span>{app.amount_pkr}</span>
                <span className={`status ${app.status}`}>{app.status.replace(/_/g, " ")}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
