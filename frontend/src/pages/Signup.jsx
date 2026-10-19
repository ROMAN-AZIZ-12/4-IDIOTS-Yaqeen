import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { decodeJwt } from "../utils";

export default function Signup() {
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
    <div className="card">
      <h1>Borrower sign up</h1>
      {error && <p className="error">{error}</p>}
      <form onSubmit={handleSubmit}>
        <label>Full name
          <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
        </label>
        <label>Email
          <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        </label>
        <label>Password
          <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={8} />
        </label>
        <button disabled={loading}>{loading ? "Creating account..." : "Sign up"}</button>
      </form>
      <p>Already have an account? <a href="/login">Log in</a></p>
    </div>
  );
}
