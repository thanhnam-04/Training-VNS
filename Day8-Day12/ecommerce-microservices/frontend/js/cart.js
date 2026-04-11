/* ═══════════════════════════════════════════════════════════
   cart.js — Cart State & Actions
   ═══════════════════════════════════════════════════════════ */

const cartStore = {
  cart: null,

  async loadCart() {
    if (!authStore.isLoggedIn()) { this.updateBadge(0); return; }
    const res = await api.get("/cart/");
    if (res && res.ok) {
      this.cart = await api.parseJSON(res);
      this.updateBadge(this.cart.total_items || 0);
    }
  },

  updateBadge(count) {
    const badge = document.getElementById("cartBadge");
    if (count > 0) {
      badge.textContent = count;
      badge.style.display = "grid";
    } else {
      badge.style.display = "none";
    }
  },

  async addToCart(productId, quantity = 1) {
    if (!authStore.isLoggedIn()) {
      showToast("Vui lòng đăng nhập để thêm vào giỏ.", "error");
      navigate("login");
      return;
    }
    const res = await api.post("/cart/add/", { product_id: productId, quantity });
    if (res && res.ok) {
      this.cart = await api.parseJSON(res);
      this.updateBadge(this.cart.total_items || 0);
      showToast("Đã thêm vào giỏ hàng! 🛍️", "success");
      return true;
    } else {
      const data = await api.parseJSON(res);
      showToast(data?.product_id?.[0] || "Lỗi thêm vào giỏ.", "error");
      return false;
    }
  },

  async updateItem(itemId, quantity) {
    const res = await api.put(`/cart/items/${itemId}/`, { quantity });
    if (res && res.ok) {
      this.cart = await api.parseJSON(res);
      this.updateBadge(this.cart.total_items || 0);
      renderCart();
    }
  },

  async removeItem(itemId) {
    const res = await api.delete(`/cart/items/${itemId}/remove/`);
    if (res && res.ok) {
      this.cart = await api.parseJSON(res);
      this.updateBadge(this.cart.total_items || 0);
      renderCart();
      showToast("Đã xóa khỏi giỏ hàng.", "info");
    }
  },

  async clearCart() {
    const res = await api.delete("/cart/clear/");
    if (res && res.ok) {
      this.cart = null;
      this.updateBadge(0);
    }
  },
};

function renderCart() {
  const container = document.getElementById("cartLayout");
  const cart = cartStore.cart;

  if (!authStore.isLoggedIn()) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <div class="empty-icon">🔐</div>
        <div class="empty-title">Vui lòng đăng nhập</div>
        <div class="empty-desc">Đăng nhập để xem giỏ hàng của bạn</div>
        <br/><button class="btn btn-primary" onclick="navigate('login')">Đăng nhập</button>
      </div>`;
    return;
  }

  if (!cart || !cart.items || cart.items.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <div class="empty-icon">🛍️</div>
        <div class="empty-title">Giỏ hàng trống</div>
        <div class="empty-desc">Thêm sản phẩm vào giỏ để tiếp tục mua sắm</div>
        <br/><button class="btn btn-primary" onclick="navigate('products')">Mua sắm ngay</button>
      </div>`;
    return;
  }

  const itemsHTML = cart.items.map(item => `
    <div class="cart-item" id="cart-item-${item.id}">
      <div class="cart-item-image">
        ${item.product.image_url
          ? `<img src="${item.product.image_url}" alt="${item.product.name}" />`
          : getProductEmoji(item.product.category_name)}
      </div>
      <div>
        <div class="cart-item-name">${item.product.name}</div>
        <div class="cart-item-price">${formatPrice(item.product.price)}</div>
        <div class="qty-controls">
          <button class="qty-btn" onclick="cartStore.updateItem(${item.id}, ${item.quantity - 1})" ${item.quantity <= 1 ? "disabled" : ""}>−</button>
          <span class="qty-display">${item.quantity}</span>
          <button class="qty-btn" onclick="cartStore.updateItem(${item.id}, ${item.quantity + 1})">+</button>
        </div>
      </div>
      <div style="text-align:right">
        <div style="font-weight:800;color:var(--accent-light)">${formatPrice(item.subtotal)}</div>
        <button class="btn btn-danger btn-sm" style="margin-top:8px" onclick="cartStore.removeItem(${item.id})">🗑️</button>
      </div>
    </div>
  `).join("");

  const summaryHTML = `
    <div class="cart-summary">
      <h3 style="font-weight:700;margin-bottom:16px">Tóm tắt</h3>
      <div class="order-row"><span>Tạm tính (${cart.total_items} sp)</span><span>${formatPrice(cart.total_price)}</span></div>
      <div class="order-row"><span>Phí giao hàng</span><span>30.000 ₫</span></div>
      <div class="order-row total"><span>Tổng cộng</span><span>${formatPrice(Number(cart.total_price) + 30000)}</span></div>
      <button class="btn btn-primary btn-full btn-lg" style="margin-top:16px" onclick="navigate('checkout')">
        💳 Thanh toán ngay
      </button>
      <button class="btn btn-ghost btn-full" style="margin-top:8px" onclick="navigate('products')">
        ← Tiếp tục mua sắm
      </button>
    </div>`;

  container.innerHTML = `<div id="cartContent">${itemsHTML}</div>${summaryHTML}`;
}

async function loadCartPage() {
  await cartStore.loadCart();
  renderCart();
}

async function submitCheckout() {
  if (!authStore.isLoggedIn()) { navigate("login"); return; }
  if (!cartStore.cart || !cartStore.cart.items || cartStore.cart.items.length === 0) {
    showToast("Giỏ hàng trống, vui lòng thêm sản phẩm trước khi thanh toán.", "error");
    navigate("products");
    return;
  }

  const name = document.getElementById("shippingName").value;
  const phone = document.getElementById("shippingPhone").value;
  const address = document.getElementById("shippingAddress").value;
  if (!name || !phone || !address) {
    showToast("Vui lòng điền đầy đủ thông tin giao hàng.", "error");
    return;
  }

  const paymentMethod = document.querySelector("input[name='paymentMethod']:checked")?.value || "cod";
  const btn = document.getElementById("placeOrderBtn");
  btn.disabled = true;
  btn.textContent = "Đang đặt hàng...";

  try {
    const res = await api.post("/orders/checkout/", {
      shipping_name: name,
      shipping_phone: phone,
      shipping_address: address,
      payment_method: paymentMethod,
      note: document.getElementById("orderNote").value,
    });
    const data = await api.parseJSON(res);
    if (res && res.ok) {
      cartStore.cart = null;
      cartStore.updateBadge(0);
      showToast(`Đặt hàng thành công! Mã đơn: #${data.order_number} 🎉`, "success");
      navigate("orders");
    } else {
      showToast(data?.error || "Đặt hàng thất bại.", "error");
    }
  } finally {
    btn.disabled = false;
    btn.textContent = "✅ Đặt hàng ngay";
  }
}

function loadCheckoutPage() {
  const cart = cartStore.cart;
  const el = document.getElementById("checkoutSummary");
  const placeOrderBtn = document.getElementById("placeOrderBtn");
  if (!cart || !cart.items?.length) {
    el.innerHTML = `<p style="color:var(--text-muted)">Giỏ hàng trống.</p>`;
    if (placeOrderBtn) {
      placeOrderBtn.disabled = true;
      placeOrderBtn.textContent = "Giỏ hàng trống";
    }
    return;
  }

  if (placeOrderBtn) {
    placeOrderBtn.disabled = false;
    placeOrderBtn.textContent = "✅ Đặt hàng ngay";
  }

  // Pre-fill from user profile
  if (authStore.user) {
    document.getElementById("shippingName").value = authStore.user.full_name || "";
    document.getElementById("shippingPhone").value = authStore.user.phone || "";
    document.getElementById("shippingAddress").value = authStore.user.address || "";
  }

  const items = cart.items.map(i => `
    <div class="order-row">
      <span>${i.product.name} x${i.quantity}</span>
      <span>${formatPrice(i.subtotal)}</span>
    </div>
  `).join("");

  el.innerHTML = `
    ${items}
    <div class="order-row"><span>Phí giao</span><span>30.000 ₫</span></div>
    <div class="order-row total">
      <span>Tổng cộng</span>
      <span>${formatPrice(Number(cart.total_price) + 30000)}</span>
    </div>
  `;
}
