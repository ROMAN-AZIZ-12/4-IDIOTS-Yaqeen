import { useI18n } from "../locale";
import Icon from "../components/Icon";
import { BackLink, PageHeading, ProgressSteps, ErrorNotice } from "../components/UI";
import { DOCUMENTS, DOC_LABELS } from "../components/uiLabels";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function ApplicationForm() {
  const { t } = useI18n();
  const [banks, setBanks] = useState([]);
  const [banksLoading, setBanksLoading] = useState(true);
  const [banksError, setBanksError] = useState("");
  const [bankReload, setBankReload] = useState(0);
  const [form, setForm] = useState({ bank_id: "", amount_pkr: "", purpose: "", business_type: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    setBanksLoading(true);
    setBanksError("");
    setBanks([]);
    api.banks().then((data) => {
      if (cancelled) return;
      if (!Array.isArray(data) || data.some((bank) =>
        !bank || typeof bank.id !== "string" || !bank.id ||
        typeof bank.name !== "string" || !bank.name.trim())) {
        throw new Error("Unexpected bank response");
      }
      setBanks(data);
      setForm((current) => ({
        ...current,
        bank_id: data.some((bank) => bank.id === current.bank_id) ? current.bank_id : "",
      }));
    }).catch(() => {
      if (!cancelled) setBanksError("Could not load banks. Please try again.");
    }).finally(() => {
      if (!cancelled) setBanksLoading(false);
    });
    return () => { cancelled = true; };
  }, [bankReload]);

  const banksReady = !banksLoading && !banksError && banks.length > 0;

  async function handleSubmit(e) {
    e.preventDefault();
    if (!banksReady || !banks.some((bank) => bank.id === form.bank_id)) return;
    setLoading(true);
    setError("");
    try {
      const app = await api.createApplication({
        bank_id: form.bank_id,
        amount_pkr: Number(form.amount_pkr),
        purpose: form.purpose,
        business_type: form.business_type,
      });
      navigate(`/upload/${app.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <BackLink to="/borrower">{t("Back to my applications")}</BackLink>
      <PageHeading eyebrow={t("New loan application")} title={t("Tell us about your business.")} description={t("Choose your bank and share the details needed to prepare your application.")} />
      <ProgressSteps created={false} />
      <div className="form-layout">
        <section className="surface form-surface">
          <h2>{t("Application details")}</h2>
          <ErrorNotice message={error} />
          <form onSubmit={handleSubmit} aria-busy={loading}>
            <label>{t("Bank")}
              <select value={form.bank_id} onChange={(e) => setForm({ ...form, bank_id: e.target.value })} required disabled={!banksReady || loading} aria-busy={banksLoading} aria-describedby="bank-status">
                <option value="">{t(banksLoading ? "Loading banks..." : banksError ? "Banks unavailable" : banks.length === 0 ? "No banks available" : "Select a bank")}</option>
                {banks.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </label>
            <div id="bank-status" aria-live="polite">
              {banksLoading && <p className="hint">{t("Loading available banks...")}</p>}
              <ErrorNotice message={banksError} />
              {!banksLoading && !banksError && banks.length === 0 && <p>{t("No banks are available yet. Please contact support.")}</p>}
            </div>
            {!banksLoading && (banksError || banks.length === 0) && <button type="button" className="button secondary" onClick={() => setBankReload((count) => count + 1)}>{t("Reload banks")}</button>}
            <label>{t("Amount (PKR)")}
              <input type="number" dir="ltr" min="1" step="0.01" value={form.amount_pkr} onChange={(e) => setForm({ ...form, amount_pkr: e.target.value })} required aria-describedby="amount-hint" />
              <span className="hint" id="amount-hint">{t("Enter the amount you wish to request.")}</span>
            </label>
            <label>{t("Purpose")}
              <input dir="auto" value={form.purpose} onChange={(e) => setForm({ ...form, purpose: e.target.value })} required aria-describedby="purpose-hint" />
              <span className="hint" id="purpose-hint">{t("What will this loan help your business do?")}</span>
            </label>
            <label>{t("Business type")}
              <input dir="auto" value={form.business_type} onChange={(e) => setForm({ ...form, business_type: e.target.value })} required aria-describedby="business-hint" />
              <span className="hint" id="business-hint">{t("Describe the kind of business you run.")}</span>
            </label>
            <button className="button" disabled={loading || !banksReady || !form.bank_id}>{loading ? t("Creating...") : t("Continue to documents")}<Icon name="arrow" className="directional" /></button>
          </form>
        </section>
        <aside className="surface guidance-panel"><span className="icon-tile"><Icon name="document" size={28} /></span><h2>{t("What comes next")}</h2><p>{t("After saving these details, upload your three required documents and submit for review.")}</p><ul className="check-list">{DOCUMENTS.map((key) => <li key={key}><Icon name="check" />{t(DOC_LABELS[key])}</li>)}</ul><div className="aside-note">{t("One active application at a time.")}</div></aside>
      </div>
    </>
  );
}
