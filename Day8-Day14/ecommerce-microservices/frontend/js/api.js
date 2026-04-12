/* ═══════════════════════════════════════════════════════════
   api.js — Centralized API Client
   Xử lý tất cả fetch calls, auth headers, error handling
   ═══════════════════════════════════════════════════════════ */

/**
 * API_BASE tự động detect môi trường:
 * - Docker Nginx (port 3000): dùng /api/ (proxy tới web:8000)
 * - Local dev trực tiếp: dùng http://localhost:8000/api/
 */
const API_BASE = (() => {
  const { hostname, port } = window.location;
  // Nếu đang chạy trên Nginx (port 3000) hoặc production → dùng relative path
  if (port === "3000" || port === "80" || port === "") {
    return "/api";
  }
  // Local dev mở trực tiếp file hoặc Django dev server
  return "http://localhost:8000/api";
})();

const api = {
  /** Gọi API với auto-attach JWT token */
  async request(endpoint, options = {}) {
    const token = localStorage.getItem("access_token");
    const headers = {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    };

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

      // Token hết hạn → tự refresh
      if (res.status === 401) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          headers.Authorization = `Bearer ${localStorage.getItem("access_token")}`;
          return fetch(`${API_BASE}${endpoint}`, { ...options, headers });
        } else {
          authStore.logout();
          navigate("login");
          return;
        }
      }

      return res;
    } catch (err) {
      console.error("API Error:", err);
      throw err;
    }
  },

  async get(endpoint, params = {}) {
    const qs = new URLSearchParams(params).toString();
    const url = qs ? `${endpoint}?${qs}` : endpoint;
    return this.request(url);
  },

  async post(endpoint, body) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  async put(endpoint, body) {
    return this.request(endpoint, {
      method: "PUT",
      body: JSON.stringify(body),
    });
  },

  async patch(endpoint, body) {
    return this.request(endpoint, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  },

  async delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  },

  async upload(endpoint, formData) {
    const token = localStorage.getItem("access_token");
    return fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
  },

  async refreshToken() {
    const refresh = localStorage.getItem("refresh_token");
    if (!refresh) return false;
    try {
      const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("access_token", data.access);
        return true;
      }
    } catch {}
    return false;
  },

  /** Helper: parse JSON hoặc trả về null khi lỗi */
  async parseJSON(res) {
    if (!res) return null;
    try { return await res.json(); } catch { return null; }
  },
};
