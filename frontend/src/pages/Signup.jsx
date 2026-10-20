import { useI18n } from "../locale";
import { AuthLayout, ErrorNotice } from "../components/UI";
import Icon from "../components/Icon";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Signup() {
  const { t } = useI18n();
  const [form, setForm] = useState({ email: "", password: "", full_name: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.signup(form);
      const login = await api.login({ email: form.email, password: form.password });
      api.setToken(login.access_token);
      navigate("/borrower");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title={t("Create your account")} description={t("A few details to start your borrower journey.")}>
      <ErrorNotice message={error} />
      <form onSubmit={handleSubmit} aria-busy={loading}>
        <label>{t("Full name")}
          <input name="full_name" autoComplete="name" dir="auto" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
        </label>
        <label>{t("Email address")}
          <input name="email" type="email" autoComplete="email" dir="ltr" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        </label>
        <label>{t("Password")}
          <input name="password" type="password" autoComplete="new-password" dir="ltr" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={8} aria-describedby="password-hint" />
          <span className="hint" id="password-hint">{t("Use at least 8 characters.")}</span>
        </label>
        <button className="button full-width" disabled={loading}>{loading ? t("Creating account...") : t("Create account")}<Icon name="arrow" className="directional" /></button>
      </form>
      <p className="auth-links">{t("Already have an account?")} <Link to="/login">{t("Sign in")}</Link></p>
    </AuthLayout>
  );
}
