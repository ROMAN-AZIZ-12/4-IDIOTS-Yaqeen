import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";

const DOC_TYPE_OPTIONS = [
  { value: "cnic", label: "CNIC" },
  { value: "utility_bill", label: "Utility bill" },
  { value: "transaction_statement", label: "Transaction statement" },
];

export default function OfficerDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [app, setApp] = useState(null);
  const [error, setError] = useState("");
  const [urls, setUrls] = useState({});
  const [decisionForm, setDecisionForm] = useState({ decision: "approved", note: "", requested_doc_type: "cnic" });

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

  async function openDocument(docId) {
    try {
      const data = await api.documentUrl(docId);
      setUrls((u) => ({ ...u, [docId]: data.url }));
      window.open(data.url, "_blank");
    } catch (err) {
      setError(err.message);
    }
  }

  async function submitDecision(e) {
    e.preventDefault();
    setError("");
    try {
      await api.makeDecision(id, decisionForm);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function retry() {
    setError("");
    try {
      await api.retryApplication(id);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  if (!app) return <p>Loading...</p>;

  return (
    <div className="card detail">
      <h1>Application detail</h1>
      {error && <p className="error">{error}</p>}
      <p><strong>Borrower:</strong> {app.borrower_full_name} ({app.borrower_email})</p>
      <p><strong>Bank:</strong> {app.bank_name}</p>
      <p><strong>Amount:</strong> {app.amount_pkr}</p>
      <p><strong>Status:</strong> <span className={`status ${app.status}`}>{app.status.replace(/_/g, " ")}</span></p>

      <h2>Documents</h2>
      <ul className="doc-list">
        {app.documents?.map((doc) => (
          <li key={doc.id}>
            <strong>{doc.doc_type.replace(/_/g, " ")}</strong> (v{doc.version}, {doc.pages} pages, {doc.extraction_status})
            <button onClick={() => openDocument(doc.id)}>Open</button>
          </li>
        ))}
      </ul>

      {app.flags?.length > 0 && (
        <>
          <h2>Flags</h2>
          <ul className="flags">
            {app.flags.map((f, i) => <li key={i}>{f.replace(/_/g, " ")}</li>)}
          </ul>
        </>
      )}

      {app.assessment && (
        <>
          <h2>Assessment</h2>
          <p><strong>Score:</strong> {app.assessment.score_total}/100</p>
          <p><strong>Suggestion:</strong> {app.assessment.suggestion.replace(/_/g, " ")}</p>
          <p className="notice">This is a suggestion only. You decide.</p>
          <h3>Factor breakdown</h3>
          <ul className="factors">
            {Object.entries(app.assessment.factors_json || {}).map(([name, data]) => (
              <li key={name}>
                <strong>{name.replace(/_/g, " ")}:</strong> {data.points} points — {data.evidence}
              </li>
            ))}
          </ul>
          <h3>Report</h3>
          <p>{app.assessment.report_json?.summary}</p>
          <ul>
            {(app.assessment.report_json?.factor_notes || []).map((note, i) => <li key={i}>{note}</li>)}
          </ul>
        </>
      )}

      {app.status === "processing_failed" && (
        <button onClick={retry}>Retry processing</button>
      )}

      {["ready_for_review", "needs_manual_review"].includes(app.status) && (
        <>
          <h2>Decision</h2>
          <form onSubmit={submitDecision}>
            <label>Decision
              <select value={decisionForm.decision} onChange={(e) => setDecisionForm({ ...decisionForm, decision: e.target.value })}>
                <option value="approved">Approve</option>
                <option value="rejected">Reject</option>
                <option value="request_document">Request document</option>
              </select>
            </label>
            {decisionForm.decision === "request_document" && (
              <label>Document type
                <select value={decisionForm.requested_doc_type} onChange={(e) => setDecisionForm({ ...decisionForm, requested_doc_type: e.target.value })}>
                  {DOC_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </label>
            )}
            {decisionForm.decision !== "approved" && (
              <label>Note
                <textarea value={decisionForm.note} onChange={(e) => setDecisionForm({ ...decisionForm, note: e.target.value })} required />
              </label>
            )}
            <button type="submit">Submit decision</button>
          </form>
        </>
      )}

      {app.decision && (
        <div className="decision-box">
          <p><strong>Latest decision:</strong> {app.decision.decision.replace(/_/g, " ")}</p>
          {app.decision.note && <p><strong>Note:</strong> {app.decision.note}</p>}
        </div>
      )}
    </div>
  );
}
