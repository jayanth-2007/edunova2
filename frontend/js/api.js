const API = "http://localhost:5000/api";

async function apiFetch(method, endpoint, body = null) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
    credentials: "include"
  };
  if (body) opts.body = JSON.stringify(body);
  const res  = await fetch(`${API}${endpoint}`, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Something went wrong");
  return data;
}

const apiGet  = (ep)       => apiFetch("GET",  ep);
const apiPost = (ep, body) => apiFetch("POST", ep, body);

// Session helpers (no JWT — using Flask session + localStorage for name)
const EduNova = {
  setUser: (u) => localStorage.setItem("en_user", JSON.stringify(u)),
  getUser: ()  => JSON.parse(localStorage.getItem("en_user") || "null"),
  clear:   ()  => localStorage.removeItem("en_user"),
  isLoggedIn: () => !!localStorage.getItem("en_user")
};

function requireAuth() {
  if (!EduNova.isLoggedIn()) window.location.href = "index.html";
}

function showAlert(id, msg, type = "danger") {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = `alert alert-${type} show`;
  el.textContent = msg;
  setTimeout(() => el.classList.remove("show"), 5000);
}

function setBtn(id, html, disabled = false) {
  const b = document.getElementById(id);
  if (!b) return;
  b.innerHTML  = html;
  b.disabled   = disabled;
}
