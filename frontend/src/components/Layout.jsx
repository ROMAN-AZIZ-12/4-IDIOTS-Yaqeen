import { useRef } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { getUser } from "../utils";
import { useI18n } from "../locale";
import BrandLogo from "./BrandLogo";
import Icon from "./Icon";

export default function Layout({ children }) {
  const user = getUser();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { language, setLanguage, t } = useI18n();
  const dialog = useRef(null);
  const signInButton = useRef(null);
  const isLanding = pathname === "/" && !user;
  const isAuth = ["/signup", "/login", "/officer-login"].includes(pathname);
  function logout() {
    localStorage.removeItem("access_token");
    navigate("/");
  }
  function closeChooser() { dialog.current?.close(); }
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">{t("Skip to content")}</a>
    <header className="site-header"><div className="header-inner">
      <Link to="/" className="brand-link" aria-label={`Yaqeen — ${t("Home")}`}><BrandLogo /></Link>
      <nav aria-label={t("Main navigation")} className="header-nav">
        {!user && <a className="nav-section-link" href="/#how-it-works">{t("How it works")}</a>}
        {user?.role === "borrower" && <><NavLink to="/borrower">{t("My applications")}</NavLink><NavLink to="/apply">{t("New application")}</NavLink></>}
        {user?.role === "officer" && <NavLink to="/officer">{t("Review workspace")}</NavLink>}
        <div className="language-switch" role="group" aria-label="Language / زبان">
          <button type="button" lang="en" aria-pressed={language === "en"} onClick={() => setLanguage("en")}>EN</button>
          <button type="button" lang="ur" aria-pressed={language === "ur"} onClick={() => setLanguage("ur")}>اردو</button>
        </div>
        {user ? <><span className="role-chip">{t(user.role === "officer" ? "Bank officer" : "Borrower")}</span><button className="button ghost signout" type="button" onClick={logout}><Icon name="logout" />{t("Sign out")}</button></> :
          <><button ref={signInButton} type="button" className="button ghost" onClick={() => dialog.current.showModal()}>{t("Sign in")}</button><Link className="button header-cta" to="/signup">{t("Create account")}</Link></>}
      </nav>
    </div></header>
    <main id="main-content" tabIndex={-1} className={isLanding ? "landing-main" : isAuth ? "auth-main" : "workspace"}>{children}</main>
    <footer className="site-footer"><div className="footer-inner"><div><BrandLogo /><p>{t("Loan application preparation for small businesses in Pakistan.")}</p></div><nav aria-label={t("Main navigation")}><Link to="/">{t("Home")}</Link>{user ? <Link to={user.role === "officer" ? "/officer" : "/borrower"}>{t(user.role === "officer" ? "Review workspace" : "My applications")}</Link> : <><a href="/#how-it-works">{t("How it works")}</a><a href="/#documents">{t("Documents needed")}</a></>}</nav><p className="footer-note">{t("A bank officer makes every lending decision.")}</p></div></footer>
    <dialog ref={dialog} className="role-dialog" aria-labelledby="role-title" onClose={() => signInButton.current?.focus()} onClick={(event) => { if (event.target === dialog.current) closeChooser(); }}>
      <div className="role-dialog-inner"><div className="section-heading"><span className="eyebrow">{t("Sign in")}</span><button type="button" className="icon-button" onClick={closeChooser} aria-label={t("Close")} autoFocus><Icon name="close" /></button></div>
        <h2 id="role-title">{t("Choose your workspace")}</h2><p>{t("How would you like to sign in?")}</p>
        <Link to="/login" className="role-option" onClick={closeChooser}><span className="icon-tile"><Icon name="business" /></span><span><strong>{t("Borrower")}</strong><small>{t("Access your application and track progress.")}</small></span><Icon name="arrow" className="directional" /></Link>
        <Link to="/officer-login" className="role-option" onClick={closeChooser}><span className="icon-tile"><Icon name="bank" /></span><span><strong>{t("Bank officer")}</strong><small>{t("Review applications for your bank.")}</small></span><Icon name="arrow" className="directional" /></Link>
        <p className="hint">{t("Officers use accounts provided by their bank.")}</p>
      </div>
    </dialog>
  </div>;
}
