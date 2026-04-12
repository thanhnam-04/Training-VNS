/* ═══════════════════════════════════════════════════════════
   orders.js — Order History & Detail
   ═══════════════════════════════════════════════════════════ */

const STATUS_MAP = {
  pending:    { label: "Chờ xác nhận", css: "status-pending" },
  confirmed:  { label: "Đã xác nhận",  css: "status-confirmed" },
  processing: { label: "Đang xử lý",   css: "status-processing" },
  shipped:    { label: "Đang giao",     css: "status-shipped" },
  delivered:  { label: "Đã giao",       css: "status-delivered" },
  cancelled:  { label: "Đã hủy",        css: "status-cancelled" },
};

async function loadOrdersPage() {
  if (!authStore.isLoggedIn()) {
    document.getElementById("ordersContent").innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🔐</div>
        <div class="empty-title">Vui lòng đăng nhập</div>
        <button class="btn btn-primary" onclick="navigate('login')" style="margin-top:16px">Đăng nhập</button>
      </div>`;
    return;
  }

  const container = document.getElementById("ordersContent");
  container.innerHTML = `<div class="spinner"></div>`;

  const res = await api.get("/orders/");
  if (!res || !res.ok) {
    container.innerHTML = `<p style="color:var(--danger)">Lỗi tải đơn hàng.</p>`;
    return;
  }

  const data = await api.parseJSON(res);
  const orders = data.results || data;

  if (!orders.length) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📭</div>
        <div class="empty-title">Chưa có đơn hàng nào</div>
        <div class="empty-desc">Mua sắm ngay để có đơn hàng đầu tiên!</div>
        <br/><button class="btn btn-primary" onclick="navigate('products')">Mua sắm ngay</button>
      </div>`;
    return;
  }

  container.innerHTML = orders.map(renderOrderCard).join("");
}

function renderOrderCard(order) {
  const status = STATUS_MAP[order.status] || { label: order.status, css: "status-pending" };
  const date = new Date(order.created_at).toLocaleDateString("vi-VN", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });

  const items = order.items.slice(0, 3).map(i => `
    <div style="display:flex;justify-content:space-between;font-size:0.875rem;padding:8px 0;border-bottom:1px solid var(--border)">
      <span style="color:var(--text-secondary)">${i.product_name} <span style="color:var(--text-muted)">x${i.quantity}</span></span>
      <span style="font-weight:600">${formatPrice(i.subtotal)}</span>
    </div>
  `).join("");

  const moreItems = order.items.length > 3 ? `<p style="font-size:0.8rem;color:var(--text-muted);margin-top:8px">+${order.items.length - 3} sản phẩm khác...</p>` : "";

  return `
    <div class="order-card">
      <div class="order-card-header">
        <div>
          <div class="order-number">Đơn #${order.order_number}</div>
          <div class="order-date">${date}</div>
        </div>
        <div style="display:flex;align-items:center;gap:12px">
          <span class="status-badge ${status.css}">${status.label}</span>
          ${order.is_paid ? `<span class="badge" style="background:rgba(16,185,129,0.2);color:#34d399;padding:4px 10px;border-radius:999px;font-size:0.75rem;font-weight:700">✅ Đã thanh toán</span>` : ""}
        </div>
      </div>
      <div class="order-card-body">
        <div style="margin-bottom:12px">${items}${moreItems}</div>
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
          <div style="font-size:0.875rem;color:var(--text-secondary)">
            📍 ${order.shipping_address}<br/>
            💳 ${order.payment_display}
          </div>
          <div style="text-align:right">
            <div style="font-size:0.8rem;color:var(--text-muted)">Tổng cộng</div>
            <div style="font-size:1.2rem;font-weight:800;color:var(--accent-light)">${formatPrice(order.total_amount)}</div>
          </div>
        </div>
      </div>
    </div>`;
}
