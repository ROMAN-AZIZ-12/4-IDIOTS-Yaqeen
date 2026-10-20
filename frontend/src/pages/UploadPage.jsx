import { useI18n } from "../locale";
import Icon from "../components/Icon";
import { BackLink, PageHeading, ProgressSteps, ErrorNotice, LoadingState, DocumentCard, Money, StatusBadge } from "../components/UI";
import { DOC_LABELS } from "../components/uiLabels";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";

const DOC_TYPES = [
  { key: "cnic", label: "CNIC" },
  { key: "utility_bill", label: "Utility bill" },
  { key: "transaction_statement", label: "Transaction statement" },
];

export default function UploadPage() {
  const { t } = useI18n();
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
      if (app.status !== "draft") navigate(`/status/${id}`, { replace: true });
    } catch (err) {
      setErrors({ general: err.message });
    }
  }

  useEffect(() => {
    load();
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

  if (!application) return errors.general ? <ErrorNotice message={errors.general} /> : <LoadingState />;

  const currentTypes = new Set(application.documents?.map((d) => d.doc_type) || []);
  const canSubmit = application.status === "draft" && DOC_TYPES.every((d) => currentTypes.has(d.key)) && !Object.values(busy).some(Boolean);

  return (
    <>
      <BackLink to="/borrower">{t("Back to my applications")}</BackLink>
      <PageHeading eyebrow={t("Upload documents")} title={t("Clear documents make a clearer application.")} description={t("Upload all three documents before submitting.")} />
      <ProgressSteps status={application.status} />
      <div className="application-strip"><span><Icon name="bank" /><bdi>{application.bank_name}</bdi></span><Money value={application.amount_pkr} /><StatusBadge status={application.status} /></div>
      <ErrorNotice message={errors.general} />
      <div className="section-heading"><h2>{t("Documents")}</h2><span className="hint">{t("{count} of 3 documents uploaded", { count: DOC_TYPES.filter((d) => currentTypes.has(d.key)).length })}</span></div>
      <p className="hint upload-requirements">{t("JPG, PNG or PDF · Up to 10 MB · Up to 5 pages")}</p>
      <div className="upload-grid">
        {DOC_TYPES.map(({ key }) => {
          const doc = application.documents?.find((d) => d.doc_type === key);
          return <DocumentCard key={key} type={key} document={doc}>
            {!currentTypes.has(key) && <>
              <label className={`file-picker ${busy[key] ? "is-disabled" : ""}`} htmlFor={`file-${key}`}><Icon name="upload" />{t("Choose file")}<span className="sr-only">{t(DOC_LABELS[key])}</span>
                <input id={`file-${key}`} type="file" accept=".pdf,.jpg,.jpeg,.png" disabled={busy[key] || submitting} onChange={(e) => e.target.files?.[0] && upload(key, e.target.files[0])} />
              </label>
              {busy[key] && <p role="status" className="hint">{t("Uploading...")}</p>}
              <ErrorNotice message={errors[key]} />
            </>}
          </DocumentCard>;
        })}
      </div>
      <div className="submit-panel surface"><div><h2>{t("Submit application")}</h2><p>{t("A bank officer makes every lending decision.")}</p>{!canSubmit && <p className="hint">{t("Upload all three documents to submit.")}</p>}</div><button className="button" onClick={submit} disabled={!canSubmit || submitting}>{submitting ? t("Submitting...") : t("Submit application")}<Icon name="arrow" className="directional" /></button></div>
      <p className="demo-note"><Icon name="shield" size={18} /><span>{t("Demo reminder")}: {t("Use synthetic documents only in this demo.")}</span></p>
    </>
  );
}
