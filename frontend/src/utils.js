export function decodeJwt(token) {
  try {
    const payload = token.split(".")[1];
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json);
  } catch {
    return null;
  }
}

export function getUser() {
  const token = localStorage.getItem("access_token");
  if (!token) return null;
  const payload = decodeJwt(token);
  if (!payload || payload.exp * 1000 < Date.now()) {
    localStorage.removeItem("access_token");
    return null;
  }
  return { userId: payload.sub, role: payload.role, bankId: payload.bank_id };
}

export function formatCurrency(amount) {
  return `PKR ${Number(amount).toLocaleString("en-PK", { minimumFractionDigits: 2 })}`;
}
