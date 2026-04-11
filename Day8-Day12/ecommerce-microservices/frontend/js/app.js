/* ═══════════════════════════════════════════════════════════
   app.js — SPA Router & App Init
   ═══════════════════════════════════════════════════════════ */

/* ── TOAST ── */
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  toast.innerHTML = `<span>${icons[type] || ""}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3200);
}

/* ── ROUTER ── */
const routes = {
  home:           { onEnter: loadHomePage },
  products:       { onEnter: loadProductsPage },
  "product-detail": {},
  cart:           { onEnter: loadCartPage },
  checkout:       { onEnter: loadCheckoutPage, requiresAuth: true },
  orders:         { onEnter: loadOrdersPage,   requiresAuth: true },
  login:          { onEnter: () => {}, redirectIfAuth: "home" },
  register:       { onEnter: () => {}, redirectIfAuth: "home" },
  profile:        { onEnter: loadProfile, requiresAuth: true },
};

function navigate(page) {
  const route = routes[page];
  if (!route) return;

  // Redirect nếu đã đăng nhập
  if (route.redirectIfAuth && authStore.isLoggedIn()) {
    navigate(route.redirectIfAuth);
    return;
  }

  // Yêu cầu đăng nhập
  if (route.requiresAuth && !authStore.isLoggedIn()) {
    showToast("Vui lòng đăng nhập.", "error");
    navigate("login");
    return;
  }

  // Ẩn tất cả pages
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));

  // Hiện page mới
  const pageEl = document.getElementById(`page-${page}`);
  if (!pageEl) return;
  pageEl.classList.add("active");

  // Update nav active state
  document.querySelectorAll(".nav-link").forEach(l => {
    l.classList.toggle("active", l.dataset.page === page);
  });

  // Scroll to top
  window.scrollTo({ top: 0, behavior: "smooth" });

  // Update URL hash
  window.location.hash = page;

  // Call onEnter hook
  if (route.onEnter) route.onEnter();
}

/* ── INIT ── */
async function initApp() {
  // Khởi tạo auth state từ localStorage
  authStore.init();

  // Load cart nếu đã đăng nhập
  if (authStore.isLoggedIn()) {
    await cartStore.loadCart();
  }

  // Router: đọc hash từ URL
  const hash = window.location.hash.replace("#", "");
  const startPage = routes[hash] ? hash : "home";
  navigate(startPage);
}

// Handle back/forward browser
window.addEventListener("hashchange", () => {
  const hash = window.location.hash.replace("#", "");
  if (routes[hash]) navigate(hash);
});

// Start app
document.addEventListener("DOMContentLoaded", initApp);
