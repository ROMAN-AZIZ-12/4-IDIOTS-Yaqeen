import { Link } from "react-router-dom";
import { useI18n } from "../locale";
import Icon from "../components/Icon";
import BrandLogo, { BrandMark } from "../components/BrandLogo";

export default function LandingPage() {
  const { t } = useI18n();
  return <>
    <section className="hero"><div className="public-width hero-grid">
      <div className="hero-copy"><BrandLogo className="hero-brand" /><p className="eyebrow pill"><span className="tiny-dot" />{t("For Pakistan’s small businesses")}</p>
        <h1>{t("Your business’s next step,")} <span>{t("with Yaqeen.")}</span></h1>
        <p className="hero-description">{t("Prepare your loan application, submit documents, and follow your bank’s review in one place.")}</p>
        <div className="hero-actions"><Link to="/signup" className="button large">{t("Start my application")}<Icon name="arrow" className="directional" /></Link><a className="text-link" href="#how-it-works">{t("See how it works")}<span aria-hidden="true">↗</span></a></div>
        <p className="hero-footnote"><Icon name="shield" size={18} />{t("A bank officer makes every lending decision.")}</p>
      </div>
      <div className="journey-art" role="img" aria-label={t("Application journey illustration")}>
        <div className="art-orbit orbit-one" /><div className="art-orbit orbit-two" />
        <div className="art-document"><div className="art-doc-top"><BrandMark size={32} /><span lang="en">Yaqeen</span><span className="art-dots">•••</span></div><div className="art-document-heading">{t("Application")}</div><div className="skeleton-line long" /><div className="skeleton-line short" /><div className="art-field-grid"><div /><div /><div /><div /></div><div className="art-document-list">{["CNIC", "Utility bill", "Transaction statement"].map((item) => <div key={item}><Icon name="document" /><span>{t(item)}</span><span className="art-row-line" /></div>)}</div></div>
        <div className="art-note note-docs"><span className="icon-tile"><Icon name="upload" /></span><span>{t("Documents")}<span className="art-mini-line" /></span></div>
        <div className="art-note note-review"><span className="icon-tile"><Icon name="review" /></span><span>{t("Bank review")}<span className="art-mini-line" /></span></div>
        <div className="art-caption"><span className="tiny-dot" />{t("Small steps. Clear progress.")}</div>
      </div>
    </div></section>
    <section id="how-it-works" className="public-section public-width"><div className="section-intro"><p className="eyebrow">{t("How it works")}</p><h2>{t("A clearer path from paperwork to review.")}</h2><p>{t("Three steps. One place to keep track.")}</p></div>
      <div className="steps-grid">{[
        ["business", "Prepare your application", "Choose a bank and tell us about your business and the amount you need."],
        ["upload", "Upload your documents", "Add a clear CNIC, utility bill and transaction statement."],
        ["review", "Follow the review", "See your application status and your officer’s decision or document request."],
      ].map(([icon, title, desc], i) => <article className="step-card" key={title}><div className="step-card-top"><span className="icon-tile"><Icon name={icon} size={28} /></span><span className="step-number" dir="ltr">0{i + 1}</span></div><h3>{t(title)}</h3><p>{t(desc)}</p></article>)}</div>
    </section>
    <section id="documents" className="documents-section"><div className="public-width documents-inner"><div className="section-intro"><p className="eyebrow">{t("Documents needed")}</p><h2>{t("A little preparation goes a long way.")}</h2><p>{t("Keep these three documents ready before you begin.")}</p></div><div className="needed-list">{[
      ["identity", "CNIC", "A clear copy of your identity document."],
      ["document", "Utility bill", "Include the printed payment history, where available."],
      ["bank", "Transaction statement", "Your bank, Easypaisa or JazzCash transaction history."],
    ].map(([icon, title, desc]) => <article key={title}><span className="icon-tile"><Icon name={icon} size={24} /></span><div><h3>{t(title)}</h3><p>{t(desc)}</p></div></article>)}</div></div></section>
    <section className="public-width public-section"><div className="human-panel"><span className="human-icon"><Icon name="shield" size={42} /></span><div><p className="eyebrow">{t("Bank review")}</p><h2>{t("Human decisions, supported by clarity.")}</h2><p>{t("AI helps read your documents. Code calculates an assessment. Your bank officer reviews the information and makes the decision.")}</p></div></div></section>
    <section className="final-cta public-width"><div><h2>{t("Ready for your next step?")}</h2><p>{t("Bring your business story and documents together.")}</p></div><Link to="/signup" className="button">{t("Create a borrower account")}<Icon name="arrow" className="directional" /></Link></section>
  </>;
}
