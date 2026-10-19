import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";

const DOC_TYPES = [
  { key: "cnic", label: "CNIC" },
  { key: "utility_bill", label: "Utility bill" },
  { key: "transaction_statement", label: "Transaction statement" },
];

export default function UploadPage() {
  const { id } = useParams();
  const [application, setApplication] = useState(null);
  const [uploads, setUploads] = useState({});
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  async function load() {
    try {
      const app = await api.getApplication(id);
      setApplication(app);
    } catch (err) {
      setErrors({ general: err.message });
    }
  }

  useEffect(() => {
    load();
    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, [id]);

  async function upload(docType, file) {
    setBusy((b) => ({ ...b, [docType]: true }));
    setErrors((e) => ({ ...e, [docType]: "" }));
    try {
      const doc = await api.uploadDocument(id, docType, file);
      setUploads((u) => ({ ...u, [docType]: doc }));
      await load();
    } catch (err) {
      setErrors((e) => ({ ...e, [docType]: err.message }));
    } finally {
      setBusy((b) => ({ ...b, [docType]: false }));
    }
  }

  async function submit() {
    setSubmitting(true);
    setErrors((e) => ({ ...e, general: "" }));
    try {
      await api.submitApplication(id);
      navigate(`/status/${id}`);
    } catch (err) {
      setErrors((e) => ({ ...e, general: err.message }));
    } finally {
      setSubmitting(false);
    }
  }

  if (!application) return <p>Loading...</p>;

  const currentTypes = new Set(application.documents?.map((d) => d.doc_type) || []);
  const canSubmit = DOC_TYPES.every((d) => currentTypes.has(d.key));

  return (
    <div className="card">
      <h1>Upload documents</h1>
      <p>Application to <strong>{application.bank_name}</strong> for {application.amount_pkr}</p>
      {errors.general && <p className="error">{errors.general}</p>}
      <div className="upload-grid">
        {DOC_TYPES.map(({ key, label }) => (
          <div key={key} className="upload-slot">
            <h3>{label}</h3>
            {currentTypes.has(key) ? (
              <p className="ok">Uploaded (version {application.documents.find((d) => d.doc_type === key)?.version})</p>
            ) : (
              <>
                <input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={(e) => e.target.files?.[0] && upload(key, e.target.files[0])}
                />
                {busy[key] && <p>Uploading...</p>}
                {errors[key] && <p className="error small">{errors[key]}</p>}
              </>
            )}
          </div>
        ))}
      </div>
      <button onClick={submit} disabled={!canSubmit || submitting}>
        {submitting ? "Submitting..." : "Submit application"}
      </button>
      {!canSubmit && <p className="hint">Upload all three documents to submit.</p>}
    </div>
  );
}
