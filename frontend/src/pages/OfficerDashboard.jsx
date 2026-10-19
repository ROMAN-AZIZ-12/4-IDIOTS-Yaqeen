import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

const STATUSES = ["", "processing", "ready_for_review", "needs_manual_review", "processing_failed", "needs_documents", "approved", "rejected"];

export default function OfficerDashboard() {
  const [apps, setApps] = useState([]);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.listApplications(filter || undefined)
      .then(setApps)
      .catch((err) => setError(err.message));
  }, [filter]);

  return (
    <div className="card">
      <h1>Officer dashboard</h1>
      {error && <p className="error">{error}</p>}
      <label>Filter by status
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          {STATUSES.map((s) => <option key={s} value={s}>{s ? s.replace(/_/g, " ") : "All"}</option>)}
        </select>
      </label>
      <ul className="app-list">
        {apps.map((app) => (
          <li key={app.id}>
            <Link to={`/officer/application/${app.id}`}>
              <strong>{app.bank_name}</strong>
              <span>{app.amount_pkr}</span>
              <span className={`status ${app.status}`}>{app.status.replace(/_/g, " ")}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
