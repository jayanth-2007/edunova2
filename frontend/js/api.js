const API_BASE = "http://127.0.0.1:5000";

async function apiFetch(method, endpoint, body = null) {
  const opts = {
    method,
    headers: {
      "Content-Type": "application/json"
    },
    credentials: "include"
  };

  if (body) {
    opts.body = JSON.stringify(body);
  }

  const res = await fetch(`${API_BASE}${endpoint}`, opts);

  let data;
  try {
    data = await res.json();
  } catch (err) {
    throw new Error(`Server returned invalid JSON (${res.status})`);
  }

  if (!res.ok) {
    throw new Error(data.error || `HTTP ${res.status}`);
  }

  return data;
}

const apiGet = (ep) => apiFetch("GET", ep);
const apiPost = (ep, body) => apiFetch("POST", ep, body);

const EduNova = {
  setUser: (u) => localStorage.setItem("en_user", JSON.stringify(u)),
  getUser: () => JSON.parse(localStorage.getItem("en_user") || "null"),
  clear: () => localStorage.removeItem("en_user"),
  isLoggedIn: () => !!localStorage.getItem("en_user")
};

function requireAuth() {
  if (!EduNova.isLoggedIn()) {
    window.location.href = "index.html";
  }
}

function showAlert(id, msg, type = "danger") {
  const el = document.getElementById(id);
  if (!el) return;

  el.className = `alert alert-${type} show`;
  el.textContent = msg;

  setTimeout(() => {
    el.classList.remove("show");
  }, 5000);
}

function setBtn(id, html, disabled = false) {
  const btn = document.getElementById(id);
  if (!btn) return;

  btn.innerHTML = html;
  btn.disabled = disabled;
}