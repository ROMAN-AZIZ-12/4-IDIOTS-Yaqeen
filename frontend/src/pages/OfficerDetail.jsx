import { useI18n } from "../locale";
import { BackLink, PageHeading, ErrorNotice, LoadingState, EmptyState, Money, StatusBadge, DocumentCard, DecisionPanel, ApplicationOverview } from "../components/UI";
import { DOC_LABELS } from "../components/uiLabels";
import Icon from "../components/Icon";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";

const DOC_TYPE_OPTIONS = [
  { value: "cnic", label: "CNIC" },
  { value: "utility_bill", label: "Utility bill" },
  { value: "transaction_statement", label: "Transaction statement" },
];

export default function OfficerDetail() {
  const { t } = useI18n();
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

  if (!app) return error ? <ErrorNotice message={error} /> : <LoadingState />;

  const assessment = app.assessment;
  const factorLabels = { income_consistency: "Income consistency", bill_payment: "Bill payment", transaction_regularity: "Transaction regularity", document_quality: "Document quality" };
  const factorMax = { income_consistency: 30, bill_payment: 25, transaction_regularity: 25, document_quality: 20 };
  const suggestions = { lean_approve: "Leans approve", review: "Needs review", lean_reject: "Leans reject" };
  const flagLabels = { thin_statement_data: "Thin statement data", thin_bill_history: "Thin bill history", missing_required_fields: "Missing required fields", printed_totals_mismatch: "Printed totals mismatch", statement_name_mismatch: "Statement name mismatch", bill_name_mismatch: "Bill name mismatch", zero_mean_credits: "Zero mean credits", missing_transaction_rows: "Missing transaction rows", handwritten_statement_unverified_not_scored: "Handwritten statement: unverified, not scored" };

  return (
    <>
      <BackLink to="/officer">{t("Back to applications")}</BackLink>
      <PageHeading eyebrow={t("Officer workspace")} title={t("Application review")} action={<StatusBadge status={app.status} />} />
      <ErrorNotice message={error} />
      <section className="surface overview-surface"><h2>{t("Applicant overview")}</h2><ApplicationOverview app={app} officer /></section>
      <div className="review-layout">
        <div className="review-main">
          <section className="surface"><div className="section-heading"><h2>{t("Documents")}</h2></div>
            <div className="review-documents">{app.documents?.map((doc) => <DocumentCard key={doc.id} type={doc.doc_type} document={doc} open={() => openDocument(doc.id)} />)}</div>
            {!app.documents?.length && <p className="hint">{t("No documents available")}</p>}
          </section>
          <section className="surface flags-surface"><h2>{t("Flags and missing information")}</h2>
            {app.flags?.length > 0 ? <ul className="flag-list">{app.flags.map((f, i) => <li key={i}><Icon name="alert" /><span dir="auto">{flagLabels[f] ? t(flagLabels[f]) : f}</span></li>)}</ul> : <p className="hint">{t("No flags reported")}</p>}
          </section>
          {assessment ? <>
            <section className="surface"><h2>{t("Factor breakdown")}</h2><div className="factor-list">{Object.entries(assessment.factors_json || {}).map(([name, data]) => <article className="factor-row" key={name}>
              <div className="section-heading"><h3>{t(factorLabels[name] || name)}</h3><strong dir="ltr">{data.points}{factorMax[name] != null ? ` / ${factorMax[name]}` : ` ${t("points")}`}</strong></div>
              {factorMax[name] != null && <meter min="0" max={factorMax[name]} value={data.points} aria-label={t(factorLabels[name] || name)}>{data.points} / {factorMax[name]}</meter>}
              <p dir="auto" className="preserve-text">{data.evidence}</p>
            </article>)}</div></section>
            <section className="surface report-surface"><div className="section-heading"><h2>{t("Explanation")}</h2>{assessment.report_source && <span className="report-source">{t(assessment.report_source === "template" ? "Template report" : assessment.report_source === "model" ? "AI-assisted report" : assessment.report_source)}</span>}</div>
              <p dir="auto" className="report-summary preserve-text">{assessment.report_json?.summary}</p>
              <ul className="report-notes">{(assessment.report_json?.factor_notes || []).map((note, i) => <li dir="auto" key={i}>{note}</li>)}</ul>
            </section>
            <section className="surface affordability-surface"><div className="section-heading"><h2>{t("Affordability information")}</h2><span className="neutral-tag">{t("Not scored")}</span></div><p className="hint">{t("Compare these figures as part of your review. They do not contribute to the score.")}</p><dl className="affordability-grid"><div><dt>{t("Requested amount")}</dt><dd><Money value={assessment.features_json?.requested_amount} /></dd></div><div><dt>{t("Average monthly net inflow")}</dt><dd><Money value={assessment.features_json?.avg_monthly_net_inflow} /></dd></div></dl></section>
          </> : <section className="surface"><EmptyState title={t("No assessment available yet")} icon="review" /></section>}
        </div>
        <aside className="review-sidebar">
          {assessment && <section className="surface score-surface"><p className="eyebrow">{t("Assessment score")}</p><div className="score-display" dir="ltr">{assessment.score_total}<span>/100</span></div><p className="small-label">{t("Assessment suggestion")}</p><p className={`suggestion suggestion-${assessment.suggestion}`}>{t(suggestions[assessment.suggestion] || assessment.suggestion)}</p><p className="hint">{t("This is an assessment, not an approval probability. The final decision is yours.")}</p></section>}
          <DecisionPanel decision={app.decision} />
          {app.status === "processing_failed" && <section className="surface"><span className="icon-tile warning"><Icon name="alert" /></span><h2>{t("Processing needs attention")}</h2><p>{t("Retry the existing application when the service is available.")}</p><button className="button" onClick={retry}>{t("Retry processing")}</button></section>}
          {["ready_for_review", "needs_manual_review"].includes(app.status) && <section className="surface decision-form"><h2>{t("Your decision")}</h2><p className="hint">{t("Review the documents and assessment before recording your decision.")}</p>
            <form onSubmit={submitDecision}>
              <label>{t("Decision")}<select value={decisionForm.decision} onChange={(e) => setDecisionForm({ ...decisionForm, decision: e.target.value })}><option value="approved">{t("Approve")}</option><option value="rejected">{t("Reject")}</option><option value="request_document">{t("Request a document")}</option></select></label>
              {decisionForm.decision === "request_document" && <label>{t("Document type")}<select value={decisionForm.requested_doc_type} onChange={(e) => setDecisionForm({ ...decisionForm, requested_doc_type: e.target.value })}>{DOC_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{t(DOC_LABELS[o.value])}</option>)}</select></label>}
              {decisionForm.decision !== "approved" && <label>{t("Note")}<textarea dir="auto" value={decisionForm.note} onChange={(e) => setDecisionForm({ ...decisionForm, note: e.target.value })} required aria-describedby="decision-note-hint" /><span className="hint" id="decision-note-hint">{t("Explain your decision or what the borrower should provide.")}</span></label>}
              <button type="submit" className={`button ${decisionForm.decision === "rejected" ? "danger" : ""}`}>{t("Submit decision")}</button>
            </form>
          </section>}
        </aside>
      </div>
    </>
  );
}
