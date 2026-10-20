import { Link } from "react-router-dom";
import { useI18n } from "../locale";
import { formatCurrency } from "../utils";
import Icon from "./Icon";
import BrandLogo from "./BrandLogo";

import { DOC_LABELS, STATUS_LABELS } from "./uiLabels";
export function StatusBadge({ status }) {
  const { t } = useI18n();
  return <span className={`status-badge status-${status}`}><span className="status-dot" />{t(STATUS_LABELS[status] || status)}</span>;
}
export function BackLink({ to, children }) {
  return <Link className="back-link" to={to}><Icon name="back" className="directional" />{children}</Link>;
}
export function PageHeading({ eyebrow, title, description, action }) {
  return <div className="page-heading"><div>{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h1>{title}</h1>{description && <p className="page-description">{description}</p>}</div>{action}</div>;
}
export function ErrorNotice({ message: error }) {
  const { message } = useI18n();
  if (!error) return null;
  return <div className="notice-panel error-panel" role="alert"><Icon name="alert" /><span dir="auto">{message(error)}</span></div>;
}
export function LoadingState() {
  const { t } = useI18n();
  return <div className="loading-state" role="status"><span className="spinner" />{t("Loading...")}</div>;
}
export function EmptyState({ title, description, action, icon = "document" }) {
  return <div className="empty-state"><span className="icon-tile"><Icon name={icon} size={28} /></span><h2>{title}</h2>{description && <p>{description}</p>}{action}</div>;
}
export function AuthLayout({ title, description, officer = false, children }) {
  const { t } = useI18n();
  return <div className="auth-shell">
    <aside className="auth-story"><BrandLogo monochrome /><div><p className="eyebrow">{t(officer ? "Officer workspace" : "For Pakistan’s small businesses")}</p><h2>{t(officer ? "Clarity for every review." : "Your next step starts here.")}</h2><p>{t(officer ? "Documents, evidence and assessments, ready for your judgment." : "Keep your application, documents and updates together.")}</p></div><div className="auth-story-foot"><Icon name="shield" />{t("A bank officer makes every lending decision.")}</div></aside>
    <section className="auth-card"><BackLink to="/">{t("Back to home")}</BackLink><div className="auth-title"><p className="eyebrow">{t(officer ? "Bank officer" : "Borrower")}</p><h1>{title}</h1><p>{description}</p></div>{children}</section>
  </div>;
}
export function Money({ value }) {
  const { t } = useI18n();
  return <bdi dir="ltr">{value == null || value === "" ? t("Unavailable") : formatCurrency(value)}</bdi>;
}
export function DateText({ value }) {
  const { language, t } = useI18n();
  const date = value ? new Date(value) : null;
  return <bdi>{date && !Number.isNaN(date.valueOf()) ? date.toLocaleDateString(language === "ur" ? "ur-PK" : "en-PK", { day: "numeric", month: "short", year: "numeric" }) : t("Unavailable")}</bdi>;
}
export function ApplicationOverview({ app, officer = false }) {
  const { t } = useI18n();
  return <dl className="overview-grid">
    {officer && <div><dt>{t("Applicant")}</dt><dd dir="auto">{app.borrower_full_name}<small dir="ltr">{app.borrower_email}</small></dd></div>}
    <div><dt>{t("Bank")}</dt><dd dir="auto">{app.bank_name}</dd></div>
    <div><dt>{t("Requested amount")}</dt><dd><Money value={app.amount_pkr} /></dd></div>
    {app.business_type && <div><dt>{t("Business type")}</dt><dd dir="auto">{app.business_type}</dd></div>}
    {app.purpose && <div><dt>{t("Purpose")}</dt><dd dir="auto">{app.purpose}</dd></div>}
    {app.created_at && <div><dt>{t("Created")}</dt><dd><DateText value={app.created_at} /></dd></div>}
    <div className="reference"><dt>{t("Reference")}</dt><dd dir="ltr">{app.id}</dd></div>
  </dl>;
}
export function DecisionPanel({ decision }) {
  const { t } = useI18n();
  if (!decision) return null;
  return <section className={`decision-panel decision-${decision.decision}`} aria-label={t("Latest officer decision")}>
    <div className="section-heading"><h2>{t("Latest decision")}</h2><StatusBadge status={decision.decision} /></div>
    {decision.note && <><p className="small-label">{t("Officer note")}</p><p className="preserve-text" dir="auto">{decision.note}</p></>}
  </section>;
}
export function DocumentCard({ type, document, children, open }) {
  const { t } = useI18n();
  const extraction = { ok: "Extracted", pending: "Pending", failed: "Failed" };
  return <article className={`document-card ${document ? "document-present" : ""}`}>
    <div className="document-card-top"><span className="icon-tile"><Icon name={type === "cnic" ? "identity" : "document"} size={24} /></span>{document && <span className="document-check"><Icon name="check" /><span className="sr-only">{t("Uploaded")}</span></span>}</div>
    <h3>{t(DOC_LABELS[type] || type)}</h3>
    {document ? <div className="document-meta"><p>{t("Uploaded")} · {t("Version {version}", { version: document.version })}</p><p>{document.pages != null && t("{count} pages", { count: document.pages })}{document.mime && ` · ${document.mime.replace("application/", "").replace("image/", "").toUpperCase()}`}{document.size_bytes != null && ` · ${(document.size_bytes / 1024).toFixed(0)} KB`}</p>{open && <p>{t("Document analysis")}: {t(extraction[document.extraction_status] || document.extraction_status)}</p>}</div> : <p className="document-meta">{t("Not uploaded")}</p>}
    {children}
    {open && <button type="button" className="button secondary" onClick={open}><Icon name="document" />{t("Open document")}</button>}
  </article>;
}
export function ProgressSteps({ status = "draft", created = true }) {
  const { t } = useI18n();
  const stage = !created ? 0 : status === "draft" ? 1 : 2;
  return <ol className="progress-steps" aria-label={t("Application")}>
    {["Application", "Documents", "Review and decision"].map((label, index) => <li key={label} className={index <= stage ? "step-active" : ""} aria-current={index === stage ? "step" : undefined}><span>{index < stage ? <Icon name="check" size={16} /> : index + 1}</span>{t(label)}</li>)}
  </ol>;
}
