import { useI18n } from "../locale";
import { PageHeading, ErrorNotice, LoadingState, EmptyState, Money, DateText, StatusBadge } from "../components/UI";
import { STATUS_LABELS } from "../components/uiLabels";
import Icon from "../components/Icon";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

const STATUSES = ["", "processing", "ready_for_review", "needs_manual_review", "processing_failed", "needs_documents", "approved", "rejected"];

export default function OfficerDashboard() {
  const { t } = useI18n();
  const [apps, setApps] = useState([]);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listApplications(filter || undefined)
      .then(setApps)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <>
      <PageHeading eyebrow={t("Officer workspace")} title={t("Applications")} description={t("Review your bank’s applications, documents and decisions.")} />
      <section className="surface applications-surface">
        <div className="table-toolbar"><span className="bank-heading"><span className="icon-tile"><Icon name="bank" /></span><strong dir="auto">{apps[0]?.bank_name || t("Review workspace")}</strong></span>
          <label className="filter-label">{t("Filter by status")}<select value={filter} onChange={(e) => { setLoading(true); setError(""); setFilter(e.target.value); }}>{STATUSES.map((s) => <option key={s} value={s}>{t(s ? STATUS_LABELS[s] : "All statuses")}</option>)}</select></label>
        </div>
        <ErrorNotice message={error} />
        {loading ? <LoadingState /> : error ? null : apps.length === 0 ? <EmptyState title={t("No applications in this view")} description={t("Applications matching your selected status will appear here.")} icon="review" /> : (
          <div className="table-wrap"><table className="applications-table"><thead><tr><th>{t("Reference")}</th><th>{t("Requested amount")}</th><th>{t("Business type")}</th><th>{t("Created")}</th><th>{t("Status")}</th><th><span className="sr-only">{t("Review application")}</span></th></tr></thead><tbody>{apps.map((app) => <tr key={app.id}>
            <td data-label={t("Reference")}><Link className="reference-link" to={`/officer/application/${app.id}`}><bdi dir="ltr">{app.id.slice(0, 8)}</bdi></Link></td>
            <td data-label={t("Requested amount")}><Money value={app.amount_pkr} /></td>
            <td data-label={t("Business type")}><bdi>{app.business_type}</bdi></td>
            <td data-label={t("Created")}><DateText value={app.created_at} /></td>
            <td data-label={t("Status")}><StatusBadge status={app.status} /></td>
            <td><Link className="table-action" to={`/officer/application/${app.id}`}>{t("Review application")}<Icon name="arrow" className="directional" size={18} /></Link></td>
          </tr>)}</tbody></table></div>
        )}
      </section>
    </>
  );
}
