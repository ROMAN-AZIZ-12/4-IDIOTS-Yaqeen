// Use the Vite proxy in local preview; deployments may provide an explicit API origin.
const API_URL = import.meta.env.VITE_API_URL || "";

function getToken() {
  return localStorage.getItem("access_token");
}

function setToken(token) {
  localStorage.setItem("access_token", token);
}

function removeToken() {
  localStorage.removeItem("access_token");
}

function errorMessage(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map(errorMessage).filter(Boolean).join("; ");
  if (detail && typeof detail === "object") {
    const message = errorMessage(detail.msg || detail.message || detail.detail);
    const field = Array.isArray(detail.loc) ? detail.loc.filter((part) => part !== "body").join(".") : "";
    return message && field ? `${field}: ${message}` : message;
  }
  return "";
}

async function request(path, options = {}) {
  const proxiedPath = API_URL ? path : (path.startsWith("/api/") ? path : `/api${path}`);
  const url = `${API_URL}${proxiedPath}`;
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...options.headers,
  };
  const token = options.overrideToken || getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
    // Fallback for proxies (e.g. the DevMarketplace preview) that strip the
    // standard Authorization header. The backend prefers Authorization and only
    // uses this header when Authorization is absent.
    headers["X-Yaqeen-Token"] = token;
  }
  const response = await fetch(url, { ...options, headers });
  let data = null;
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    data = await response.json();
  }
  if (!response.ok) {
    const detail = errorMessage(data?.detail) || errorMessage(data?.message) || `${response.status} error`;
    const err = new Error(detail);
    err.status = response.status;
    err.data = data;
    throw err;
  }
  return data;
}

export const api = {
  setToken,
  removeToken,
  getToken,

  signup: (body) => request("/auth/signup", { method: "POST", body: JSON.stringify(body) }),
  login: (body) => request("/auth/login", { method: "POST", body: JSON.stringify(body) }),
  setup2fa: (overrideToken) => request("/auth/2fa/setup", { method: "POST", overrideToken }),
  verify2fa: (body, overrideToken) => request("/auth/2fa/verify", { method: "POST", body: JSON.stringify(body), overrideToken }),

  banks: () => request("/banks"),

  createApplication: (body) => request("/applications", { method: "POST", body: JSON.stringify(body) }),
  listApplications: (status) => request(`/applications${status ? `?status_filter=${encodeURIComponent(status)}` : ""}`),
  getApplication: (id) => request(`/applications/${id}`),
  submitApplication: (id) => request(`/applications/${id}/submit`, { method: "POST" }),

  uploadDocument: (applicationId, docType, file) => {
    const form = new FormData();
    form.append("doc_type", docType);
    form.append("file", file);
    return request(`/applications/${applicationId}/documents`, { method: "POST", body: form });
  },
  documentUrl: (documentId) => request(`/documents/${documentId}/url`),

  makeDecision: (applicationId, body) => request(`/applications/${applicationId}/decision`, { method: "POST", body: JSON.stringify(body) }),
  retryApplication: (applicationId) => request(`/applications/${applicationId}/retry`, { method: "POST" }),
};
