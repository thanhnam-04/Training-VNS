/* ═══════════════════════════════════════════════════════════
   auth.js — Authentication State & Actions
   ═══════════════════════════════════════════════════════════ */

/** Mở Django Admin — URL phụ thuộc môi trường */
function openAdmin() {
  const { port } = window.location;
  const adminBase = (port === "3000" || port === "80" || port === "")
    ? "/admin/"
    : "http://localhost:8000/admin/";
  window.open(adminBase, "_blank");
}

const authStore = {
  user: null,

  init() {
    const saved = localStorage.getItem("user");
    if (saved) this.user = JSON.parse(saved);
    this.updateUI();
  },

  setUser(userData, accessToken, refreshToken) {
    this.user = userData;
    localStorage.setItem("user", JSON.stringify(userData));
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    this.updateUI();
  },

  logout() {
    this.user = null;
    localStorage.removeItem("user");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    this.updateUI();
    navigate("home");
    showToast("Đã đăng xuất.", "info");
  },

  isLoggedIn() { return !!this.user; },

  updateUI() {
    const loggedIn = this.isLoggedIn();
    document.getElementById("authButtons").style.display = loggedIn ? "none" : "flex";
    document.getElementById("userMenu").style.display = loggedIn ? "block" : "none";
    document.getElementById("ordersNavLink").style.display = loggedIn ? "inline-flex" : "none";

    if (loggedIn && this.user) {
      const initial = (this.user.full_name || this.user.email || "U")[0].toUpperCase();
      document.getElementById("userInitial").textContent = initial;
      document.getElementById("dropdownName").textContent = this.user.full_name || this.user.username;
      document.getElementById("dropdownEmail").textContent = this.user.email;
      if (this.user.is_staff) {
        document.getElementById("adminLink").style.display = "flex";
      }
    }
  },
};

async function submitLogin(event) {
  if (event) event.preventDefault();
  const btn = document.getElementById("loginSubmitBtn");
  const errorEl = document.getElementById("loginError");
  const email = document.getElementById("loginEmail").value;
  const password = document.getElementById("loginPassword").value;

  btn.disabled = true;
  btn.textContent = "Đang đăng nhập...";
  errorEl.style.display = "none";

  try {
    const res = await api.post("/auth/login/", { email, password });
    const data = await api.parseJSON(res);

    if (res.ok) {
      authStore.setUser(data.user, data.access, data.refresh);
      showToast(`Chào mừng ${data.user.full_name || data.user.username}! 👋`, "success");
      navigate("home");
      await cartStore.loadCart();
    } else {
      const msg = data?.detail || data?.non_field_errors?.[0] || "Email hoặc mật khẩu sai.";
      errorEl.textContent = msg;
      errorEl.style.display = "block";
    }
  } catch {
    errorEl.textContent = "Không thể kết nối server.";
    errorEl.style.display = "block";
  } finally {
    btn.disabled = false;
    btn.textContent = "Đăng nhập";
  }
}

async function submitRegister(event) {
  if (event) event.preventDefault();
  const btn = document.getElementById("registerSubmitBtn");
  const errorEl = document.getElementById("registerError");

  const password = document.getElementById("regPassword").value;
  const password2 = document.getElementById("regPassword2").value;

  if (password !== password2) {
    errorEl.textContent = "Mật khẩu xác nhận không khớp.";
    errorEl.style.display = "block";
    return;
  }

  btn.disabled = true;
  btn.textContent = "Đang đăng ký...";
  errorEl.style.display = "none";

  try {
    const res = await api.post("/auth/register/", {
      username: document.getElementById("regUsername").value,
      email: document.getElementById("regEmail").value,
      first_name: document.getElementById("regFirstName").value,
      last_name: document.getElementById("regLastName").value,
      phone: document.getElementById("regPhone").value,
      password,
      password2,
    });
    const data = await api.parseJSON(res);

    if (res.ok) {
      authStore.setUser(data.user, data.access, data.refresh);
      showToast("Đăng ký thành công! 🎉", "success");
      navigate("home");
    } else {
      const errors = Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`);
      errorEl.textContent = errors.join(" | ");
      errorEl.style.display = "block";
    }
  } catch {
    errorEl.textContent = "Không thể kết nối server.";
    errorEl.style.display = "block";
  } finally {
    btn.disabled = false;
    btn.textContent = "Tạo tài khoản";
  }
}

async function logout() {
  const refresh = localStorage.getItem("refresh_token");
  if (refresh) {
    await api.post("/auth/logout/", { refresh }).catch(() => {});
  }
  authStore.logout();
  document.getElementById("userDropdown").classList.remove("open");
}

async function loadProfile() {
  const res = await api.get("/auth/profile/");
  if (!res || !res.ok) return;
  const user = await api.parseJSON(res);
  authStore.user = user;

  document.getElementById("profileAvatarLarge").textContent = (user.full_name || user.email)[0].toUpperCase();
  document.getElementById("profileName").textContent = user.full_name || user.username;
  document.getElementById("profileEmail").textContent = user.email;
  document.getElementById("profileFirstName").value = user.first_name || "";
  document.getElementById("profileLastName").value = user.last_name || "";
  document.getElementById("profilePhone").value = user.phone || "";
  document.getElementById("profileAddress").value = user.address || "";

  const badges = document.getElementById("profileBadges");
  badges.innerHTML = "";
  if (user.is_staff) badges.innerHTML += `<span class="badge badge-featured">⚙️ Admin</span>`;
  if (user.is_verified) badges.innerHTML += `<span class="badge" style="background:rgba(16,185,129,0.2);color:#34d399">✅ Verified</span>`;
}

async function updateProfile(event) {
  if (event) event.preventDefault();
  const res = await api.patch("/auth/profile/", {
    first_name: document.getElementById("profileFirstName").value,
    last_name: document.getElementById("profileLastName").value,
    phone: document.getElementById("profilePhone").value,
    address: document.getElementById("profileAddress").value,
  });
  if (res && res.ok) {
    const user = await api.parseJSON(res);
    authStore.user = user;
    localStorage.setItem("user", JSON.stringify(user));
    authStore.updateUI();
    showToast("Cập nhật hồ sơ thành công! ✅", "success");
  } else {
    showToast("Cập nhật thất bại.", "error");
  }
}

function togglePassword(inputId) {
  const input = document.getElementById(inputId);
  input.type = input.type === "password" ? "text" : "password";
}

function toggleUserDropdown() {
  document.getElementById("userDropdown").classList.toggle("open");
}

document.addEventListener("click", (e) => {
  const menu = document.getElementById("userMenu");
  if (menu && !menu.contains(e.target)) {
    document.getElementById("userDropdown").classList.remove("open");
  }
});
