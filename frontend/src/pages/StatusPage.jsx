import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";

const DOC_TYPES = [
  { key: "cnic", label: "CNIC" },
  { key: "utility_bill", label: "Utility bill" },
  { key: "transaction_statement", label: "Transaction statement" },
];

export default function StatusPage() {
  const { id } = useParams();
  const [app, setApp] = useState(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  async function load() {
    try {
      const data = await api.getApplication(id);
      setApp(data);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
    const timer = setInterval(() => {
      if (app?.status === "processing") load();
    }, 5000);
    return () => clearInterval(timer);
  }, [id, app?.status]);

  async function handleFile(docType, file) {
    setUploading(true);
    setError("");
    try {
      await api.uploadDocument(id, docType, file);
      await load();
      setMessage("Document uploaded");
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  if (!app) return <p>Loading...</p>;

  return (
    <div className="card">
      <h1>Application status</h1>
      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}
      <p><strong>Bank:</strong> {app.bank_name}</p>
      <p><strong>Amount:</strong> {app.amount_pkr}</p>
      <p><strong>Status:</strong> <span className={`status ${app.status}`}>{app.status.replace(/_/g, " ")}</span></p>

      {app.decision && (
        <div className="decision-box">
          <p><strong>Officer decision:</strong> {app.decision.decision.replace(/_/g, " ")}</p>
          {app.decision.note && <p><strong>Note:</strong> {app.decision.note}</p>}
        </div>
      )}

      {app.status === "needs_documents" && app.decision?.requested_doc_type && (
        <div className="request-box">
          <p>The officer requested a new <strong>{app.decision.requested_doc_type.replace(/_/g, " ")}</strong>.</p>
          <input
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            disabled={uploading}
            onChange={(e) => e.target.files?.[0] && handleFile(app.decision.requested_doc_type, e.target.files[0])}
          />
        </div>
      )}

      <h3>Documents</h3>
      <ul className="doc-list">
        {DOC_TYPES.map(({ key, label }) => {
          const doc = app.documents?.find((d) => d.doc_type === key);
          return (
            <li key={key}>
              {label}: {doc ? `uploaded (version ${doc.version})` : "not uploaded"}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
