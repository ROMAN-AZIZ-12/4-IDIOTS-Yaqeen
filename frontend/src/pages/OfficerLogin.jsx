import { useI18n } from "../locale";
import { AuthLayout, ErrorNotice } from "../components/UI";
import Icon from "../components/Icon";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { api } from "../api";

export default function OfficerLogin() {
  const { t } = useI18n();
  const [form, setForm] = useState({ email: "", password: "" });
  const [pendingToken, setPendingToken] = useState("");
  const [setupUri, setSetupUri] = useState("");
  const [secret, setSecret] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function login(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await api.login(form);
      if (data.status === "ok") {
        api.setToken(data.access_token);
        navigate("/officer");
        return;
      }
      setPendingToken(data.pending_token);
      if (data.status === "2fa_enroll_required") {
        const setup = await api.setup2fa(data.pending_token);
        setSetupUri(setup.otpauth_uri);
        setSecret(setup.secret);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function verify(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await api.verify2fa({ pending_token: pendingToken, code }, pendingToken);
      api.setToken(data.access_token);
      navigate("/officer");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout officer title={t(!pendingToken ? "Officer sign in" : setupUri ? "Set up two-step verification" : "Verify your sign in")} description={t(!pendingToken ? "Use your provisioned bank account. Two-step verification keeps your workspace protected." : "Enter the 6-digit code from your authenticator app.")}>
      <ErrorNotice message={error} />
      {!pendingToken ? (
        <form onSubmit={login} aria-busy={loading}>
          <label>{t("Email address")}
            <input name="email" type="email" autoComplete="username" dir="ltr" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </label>
          <label>{t("Password")}
            <input name="password" type="password" autoComplete="current-password" dir="ltr" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          </label>
          <button className="button full-width" disabled={loading}>{loading ? t("Checking...") : t("Continue")}<Icon name="arrow" className="directional" /></button>
          <p className="hint">{t("Officers use accounts provided by their bank.")}</p>
        </form>
      ) : (
        <form onSubmit={verify} aria-busy={loading}>
          {setupUri && (
            <div className="totp-setup">
              <p>{t("Scan this QR code with your authenticator app, then enter the 6-digit code.")}</p>
              <div className="qr-surface" role="img" aria-label={t("Authenticator setup QR code")}><QRCodeSVG value={setupUri} size={180} /></div>
              <span className="small-label">{t("Manual setup key")}</span>
              <p className="secret" dir="ltr">{secret}</p>
            </div>
          )}
          <label>{t("Verification code")}
            <input name="code" className="otp-input" type="text" inputMode="numeric" autoComplete="one-time-code" dir="ltr" value={code} onChange={(e) => setCode(e.target.value)} required maxLength={6} minLength={6} />
          </label>
          <button className="button full-width" disabled={loading}>{loading ? t("Verifying...") : t("Verify and continue")}</button>
        </form>
      )}
    </AuthLayout>
  );
}
