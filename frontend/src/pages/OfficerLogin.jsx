import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { api } from "../api";

export default function OfficerLogin() {
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
    <div className="card">
      <h1>Officer login</h1>
      {error && <p className="error">{error}</p>}
      {!pendingToken ? (
        <form onSubmit={login}>
          <label>Email
            <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </label>
          <label>Password
            <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          </label>
          <button disabled={loading}>{loading ? "Checking..." : "Continue"}</button>
        </form>
      ) : (
        <form onSubmit={verify}>
          {setupUri && (
            <div className="totp-setup">
              <p>Scan this QR code with your authenticator app, then enter the 6-digit code.</p>
              <QRCodeSVG value={setupUri} size={180} />
              <p className="secret">{secret}</p>
            </div>
          )}
          {!setupUri && <p>Enter the 6-digit code from your authenticator app.</p>}
          <label>Code
            <input value={code} onChange={(e) => setCode(e.target.value)} required maxLength={6} minLength={6} />
          </label>
          <button disabled={loading}>{loading ? "Verifying..." : "Verify"}</button>
        </form>
      )}
    </div>
  );
}
