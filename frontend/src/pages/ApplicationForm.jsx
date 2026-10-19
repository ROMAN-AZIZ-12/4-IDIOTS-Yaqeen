import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function ApplicationForm() {
  const [banks, setBanks] = useState([]);
  const [form, setForm] = useState({ bank_id: "", amount_pkr: "", purpose: "", business_type: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    api.banks().then(setBanks).catch(() => setError("Could not load banks"));
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
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
    <div className="card">
      <h1>New loan application</h1>
      {error && <p className="error">{error}</p>}
      <form onSubmit={handleSubmit}>
        <label>Bank
          <select value={form.bank_id} onChange={(e) => setForm({ ...form, bank_id: e.target.value })} required>
            <option value="">Select a bank</option>
            {banks.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        </label>
        <label>Amount (PKR)
          <input type="number" min="1" step="0.01" value={form.amount_pkr} onChange={(e) => setForm({ ...form, amount_pkr: e.target.value })} required />
        </label>
        <label>Purpose
          <input value={form.purpose} onChange={(e) => setForm({ ...form, purpose: e.target.value })} required />
        </label>
        <label>Business type
          <input value={form.business_type} onChange={(e) => setForm({ ...form, business_type: e.target.value })} required />
        </label>
        <button disabled={loading}>{loading ? "Creating..." : "Continue to documents"}</button>
      </form>
    </div>
  );
}
