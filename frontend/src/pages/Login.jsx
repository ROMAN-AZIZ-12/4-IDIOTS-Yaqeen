import { useI18n } from "../locale";
import { AuthLayout, ErrorNotice } from "../components/UI";
import Icon from "../components/Icon";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Login() {
  const { t } = useI18n();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await api.login(form);
      if (data.status === "ok") {
        api.setToken(data.access_token);
        navigate("/borrower");
      } else {
        setError("This account needs officer login.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title={t("Welcome back")} description={t("Sign in to continue your application or check its progress.")}>
      <ErrorNotice message={error} />
      <form onSubmit={handleSubmit} aria-busy={loading}>
        <label>{t("Email address")}
          <input name="email" type="email" autoComplete="username" dir="ltr" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        </label>
        <label>{t("Password")}
          <input name="password" type="password" autoComplete="current-password" dir="ltr" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        </label>
        <button className="button full-width" disabled={loading}>{loading ? t("Signing in...") : t("Sign in")}<Icon name="arrow" className="directional" /></button>
      </form>
      <p className="auth-links">{t("New to Yaqeen?")} <Link to="/signup">{t("Create account")}</Link></p>
      <p className="auth-links subtle"><Link to="/officer-login">{t("Looking for officer sign in?")}</Link></p>
    </AuthLayout>
  );
}
