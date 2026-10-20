import { useI18n } from "../locale";
import { PageHeading, ErrorNotice, LoadingState, EmptyState, Money, DateText, StatusBadge } from "../components/UI";
import Icon from "../components/Icon";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function BorrowerDashboard() {
  const { t } = useI18n();
  const [apps, setApps] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listApplications()
      .then(setApps)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState />;

  return (
    <>
      <PageHeading eyebrow={t("Borrower workspace")} title={t("My applications")} description={t("Keep track of your next business step.")} action={apps.length > 0 && !apps.some((app) => !["approved", "rejected"].includes(app.status)) ? <Link className="button" to="/apply"><Icon name="plus" />{t("New application")}</Link> : null} />
      <ErrorNotice message={error} />
      {!error && apps.length === 0 ? <section className="surface"><EmptyState title={t("No applications yet")} description={t("Start with your business details. You can upload your documents next.")} action={<Link className="button" to="/apply">{t("Start an application")}<Icon name="arrow" className="directional" /></Link>} icon="business" /></section> : (
        <div className="borrower-apps">{apps.map((app) => <article className="surface borrower-application" key={app.id}>
          <div className="section-heading"><span className="bank-heading"><span className="icon-tile"><Icon name="bank" /></span><strong dir="auto">{app.bank_name}</strong></span><StatusBadge status={app.status} /></div>
          <div className="borrower-application-body"><div><p className="small-label">{t("Requested amount")}</p><div className="amount-display"><Money value={app.amount_pkr} /></div></div><dl><div><dt>{t("Purpose")}</dt><dd dir="auto">{app.purpose}</dd></div><div><dt>{t("Business type")}</dt><dd dir="auto">{app.business_type}</dd></div><div><dt>{t("Created")}</dt><dd><DateText value={app.created_at} /></dd></div></dl></div>
          <div className="application-card-footer"><span className="hint">{t("Reference")}: <bdi dir="ltr">{app.id.slice(0, 8)}</bdi></span><Link className="button secondary" to={app.status === "draft" ? `/upload/${app.id}` : `/status/${app.id}`}>{t(app.status === "draft" ? "Continue application" : "View application")}<Icon name="arrow" className="directional" /></Link></div>
        </article>)}</div>
      )}
    </>
  );
}
