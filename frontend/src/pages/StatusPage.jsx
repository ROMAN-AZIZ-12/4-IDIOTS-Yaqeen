import { useI18n } from "../locale";
import Icon from "../components/Icon";
import { BackLink, PageHeading, ProgressSteps, ErrorNotice, LoadingState, DocumentCard, StatusBadge, DecisionPanel, ApplicationOverview } from "../components/UI";
import { DOC_LABELS, STATUS_HELP } from "../components/uiLabels";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";

const DOC_TYPES = [
  { key: "cnic", label: "CNIC" },
  { key: "utility_bill", label: "Utility bill" },
  { key: "transaction_statement", label: "Transaction statement" },
];

export default function StatusPage() {
  const { t } = useI18n();
  const { id } = useParams();
  const [app, setApp] = useState(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  async function load() {
    try {
      const data = await api.getApplication(id);
      setApp(data);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    let cancelled = false;
    let timer;
    async function poll() {
      let terminal = false;
      try {
        const data = await api.getApplication(id);
        if (cancelled) return;
        setApp(data);
        setError("");
        terminal = ["approved", "rejected"].includes(data.status);
      } catch (err) {
        if (!cancelled) setError(err.message);
      }
      if (!cancelled && !terminal) timer = setTimeout(poll, 5000);
    }
    setApp(null);
    poll();
    return () => { cancelled = true; clearTimeout(timer); };
  }, [id]);

  async function handleFile(docType, file) {
    setUploading(true);
    setError("");
    setMessage("");
    try {
      await api.uploadDocument(id, docType, file);
      await load();
      setMessage("Document uploaded. Processing has restarted automatically.");
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  if (!app) return error ? <ErrorNotice message={error} /> : <LoadingState />;

  return (
    <>
      <BackLink to="/borrower">{t("Back to my applications")}</BackLink>
      <PageHeading eyebrow={t("Application status")} title={t("Your application’s next chapter.")} action={<StatusBadge status={app.status} />} />
      <ErrorNotice message={error} />
      {message && <div className="notice-panel success-panel" role="status"><Icon name="check" />{t(message)}</div>}
      <DecisionPanel decision={app.decision} />
      <section className="surface status-summary"><div className="section-heading"><h2>{t("Application details")}</h2></div><ApplicationOverview app={app} /><ProgressSteps status={app.status} /><p className={`status-explainer status-${app.status}`}><Icon name={app.status === "processing" ? "clock" : "document"} /><span>{t(STATUS_HELP[app.status] || app.status)}</span></p>
        {app.status === "draft" && <Link className="button" to={`/upload/${app.id}`}>{t("Continue application")}<Icon name="arrow" className="directional" /></Link>}
      </section>
      {app.status === "needs_documents" && app.decision?.requested_doc_type && (
        <section className="request-panel">
          <span className="icon-tile"><Icon name="upload" size={26} /></span>
          <div><h2>{t("Requested document")}</h2><p>{t("Upload a new {document} to continue the review.", { document: t(DOC_LABELS[app.decision.requested_doc_type] || app.decision.requested_doc_type) })}</p>
            <p className="hint">{t("JPG, PNG or PDF · Up to 10 MB · Up to 5 pages")}</p>
            <label className={`file-picker ${uploading ? "is-disabled" : ""}`} htmlFor="replacement-file"><Icon name="upload" />{t(uploading ? "Uploading..." : "Choose file")}
              <input id="replacement-file" type="file" accept=".pdf,.jpg,.jpeg,.png" disabled={uploading} onChange={(e) => {
                const file = e.target.files?.[0];
                e.target.value = "";
                if (file) handleFile(app.decision.requested_doc_type, file);
              }} />
            </label>
          </div>
        </section>
      )}
      <div className="section-heading"><h2>{t("Documents")}</h2></div>
      <div className="upload-grid">{DOC_TYPES.map(({ key }) => <DocumentCard key={key} type={key} document={app.documents?.find((d) => d.doc_type === key)} />)}</div>
    </>
  );
}
