/* ═══════════════════════════════════════════════════════════
   products.js — Product Listing, Detail, Search
   ═══════════════════════════════════════════════════════════ */

let searchDebounceTimer = null;
let currentPage = 1;

const EMOJI_MAP = {
  "Điện thoại": "📱", "Laptop": "💻", "Phụ kiện": "🎧",
  "Máy tính bảng": "📟", "Smartwatch": "⌚", "Loa & Âm thanh": "🔊",
};

function getProductEmoji(category) {
  return EMOJI_MAP[category] || "📦";
}

function formatPrice(amount) {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(amount);
}

/* ── Home page: Featured & Categories ── */
async function loadHomePage() {
  try {
    await Promise.all([loadFeaturedProducts(), loadCategories()]);
  } catch {
    const featuredGrid = document.getElementById("featuredGrid");
    const categoriesGrid = document.getElementById("categoriesGrid");
    if (featuredGrid) {
      featuredGrid.innerHTML = `<p style="color:var(--text-muted)">Không tải được sản phẩm nổi bật.</p>`;
    }
    if (categoriesGrid) {
      categoriesGrid.innerHTML = `<p style="color:var(--text-muted)">Không tải được danh mục.</p>`;
    }
  }
}

async function loadFeaturedProducts() {
  const res = await api.get("/inventory/products/featured/");
  const grid = document.getElementById("featuredGrid");
  if (!res || !res.ok) { grid.innerHTML = `<p style="color:var(--text-muted)">Không tải được sản phẩm.</p>`; return; }
  const payload = await api.parseJSON(res);
  const prods = Array.isArray(payload)
    ? payload
    : Array.isArray(payload?.results)
      ? payload.results
      : [];
  grid.innerHTML = prods.length ? prods.map(renderProductCard).join("") : `<p style="color:var(--text-muted)">Chưa có sản phẩm nổi bật.</p>`;
}

async function loadCategories() {
  const res = await api.get("/inventory/categories/");
  const grid = document.getElementById("categoriesGrid");
  if (!res || !res.ok) { grid.innerHTML = ""; return; }
  const payload = await api.parseJSON(res);
  const cats = Array.isArray(payload?.results)
    ? payload.results
    : Array.isArray(payload)
      ? payload
      : [];

  if (!cats.length) {
    grid.innerHTML = `<p style="color:var(--text-muted)">Chưa có danh mục.</p>`;
    return;
  }

  grid.innerHTML = cats.map(c => `
    <div class="category-card" onclick="filterByCategory(${c.id})">
      <div class="category-icon">${c.icon || "📦"}</div>
      <div class="category-name">${c.name}</div>
      <div class="category-count">${c.product_count} sản phẩm</div>
    </div>
  `).join("");
}

function filterByCategory(catId) {
  navigate("products");
  setTimeout(() => {
    document.getElementById("categoryFilter").value = catId;
    loadProducts();
  }, 100);
}

/* ── Products page ── */
async function loadProductsPage() {
  try {
    await loadCategoryFilter();
    await loadProducts();
  } catch {
    const grid = document.getElementById("productsGrid");
    if (grid) {
      grid.innerHTML = `<p style="color:var(--text-muted);grid-column:1/-1">Không tải được dữ liệu sản phẩm.</p>`;
    }
  }
}

async function loadCategoryFilter() {
  const res = await api.get("/inventory/categories/");
  if (!res || !res.ok) return;
  const payload = await api.parseJSON(res);
  const cats = Array.isArray(payload?.results)
    ? payload.results
    : Array.isArray(payload)
      ? payload
      : [];
  const select = document.getElementById("categoryFilter");
  select.innerHTML = `<option value="">Tất cả danh mục</option>` +
    cats.map(c => `<option value="${c.id}">${c.icon} ${c.name}</option>`).join("");
}

async function loadProducts(page = currentPage) {
  const grid = document.getElementById("productsGrid");
  grid.innerHTML = Array(8).fill(`<div class="skeleton-card"></div>`).join("");

  const params = {
    page,
    ordering: document.getElementById("sortFilter")?.value || "-created_at",
  };

  const search = document.getElementById("searchInput")?.value;
  if (search) params.search = search;

  const cat = document.getElementById("categoryFilter")?.value;
  if (cat) params.category = cat;

  const stock = document.getElementById("stockFilter")?.value;
  if (stock) params.in_stock = stock;

  const res = await api.get("/inventory/products/", params);
  if (!res || !res.ok) {
    grid.innerHTML = `<p style="color:var(--text-muted);grid-column:1/-1">Lỗi tải sản phẩm.</p>`;
    return;
  }

  const data = await api.parseJSON(res);
  const products = Array.isArray(data?.results)
    ? data.results
    : Array.isArray(data)
      ? data
      : [];

  if (products.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <div class="empty-icon">🔍</div>
        <div class="empty-title">Không tìm thấy sản phẩm</div>
        <div class="empty-desc">Thử tìm kiếm với từ khóa khác</div>
      </div>`;
    document.getElementById("pagination").innerHTML = "";
    return;
  }

  grid.innerHTML = products.map(renderProductCard).join("");
  const totalCount = typeof data?.count === "number" ? data.count : products.length;
  renderPagination(totalCount, data?.next || null, data?.previous || null, page);
}

function renderProductCard(p) {
  const emojiOrImg = p.image_url
    ? `<img src="${p.image_url}" alt="${p.name}" loading="lazy" />`
    : getProductEmoji(p.category_name);

  const badges = [];
  if (p.is_featured) badges.push(`<span class="badge badge-featured">⭐ Nổi bật</span>`);
  if (p.status === "out_of_stock") badges.push(`<span class="badge badge-out">Hết hàng</span>`);
  else if (p.is_low_stock) badges.push(`<span class="badge badge-low-stock">Sắp hết</span>`);

  const outOfStock = p.status === "out_of_stock";

  return `
    <div class="product-card" onclick="viewProduct(${p.id})">
      <div class="product-image">
        ${emojiOrImg}
        <div class="product-badges">${badges.join("")}</div>
      </div>
      <div class="product-body">
        <div class="product-category">${p.category_name || ""}</div>
        <div class="product-name">${p.name}</div>
        <div class="product-price">${formatPrice(p.price)}</div>
        <div class="product-stock ${p.is_low_stock ? 'low' : ''}">
          ${outOfStock ? "🔴 Hết hàng" : p.is_low_stock ? `⚠️ Còn ${p.stock}` : `✅ Còn hàng`}
        </div>
      </div>
      <div class="product-actions">
        <button class="btn btn-primary btn-sm" style="flex:1" 
          onclick="event.stopPropagation(); cartStore.addToCart(${p.id})"
          ${outOfStock ? "disabled" : ""}>
          🛍️ Thêm giỏ
        </button>
        <button class="btn btn-ghost btn-sm" onclick="event.stopPropagation(); viewProduct(${p.id})">
          👁
        </button>
      </div>
    </div>`;
}

function renderPagination(count, next, prev, current) {
  if (!count) return;
  const pageSize = 12;
  const totalPages = Math.ceil(count / pageSize);
  if (totalPages <= 1) { document.getElementById("pagination").innerHTML = ""; return; }

  let btns = "";
  if (prev) btns += `<button class="page-btn" onclick="loadProducts(${current - 1})">←</button>`;
  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || Math.abs(i - current) <= 2) {
      btns += `<button class="page-btn ${i === current ? 'active' : ''}" onclick="loadProducts(${i})">${i}</button>`;
    } else if (Math.abs(i - current) === 3) {
      btns += `<span style="color:var(--text-muted);padding:0 4px">…</span>`;
    }
  }
  if (next) btns += `<button class="page-btn" onclick="loadProducts(${current + 1})">→</button>`;
  document.getElementById("pagination").innerHTML = btns;
  currentPage = current;
}

async function viewProduct(productId) {
  navigate("product-detail");
  const container = document.getElementById("productDetailContent");
  container.innerHTML = `<div class="spinner"></div>`;

  const res = await api.get(`/inventory/products/${productId}/`);
  if (!res || !res.ok) {
    container.innerHTML = `<p style="color:var(--danger)">Không tải được sản phẩm.</p>`;
    return;
  }

  const p = await api.parseJSON(res);
  const imgHTML = p.image_url
    ? `<img src="${p.image_url}" alt="${p.name}" />`
    : getProductEmoji(p.category?.name);

  container.innerHTML = `
    <div class="product-detail-layout">
      <div class="product-detail-image">${imgHTML}</div>
      <div>
        <div class="product-category" style="font-size:0.85rem;color:var(--accent-light);font-weight:600;margin-bottom:8px">
          ${p.category?.icon || "📦"} ${p.category?.name || ""}
        </div>
        <h1 style="font-size:1.75rem;font-weight:800;line-height:1.3">${p.name}</h1>
        <p style="color:var(--text-muted);font-size:0.85rem;margin-top:4px">SKU: ${p.sku}</p>
        <div class="product-detail-price">${formatPrice(p.price)}</div>
        ${p.cost_price ? `<p style="color:var(--text-muted);font-size:0.8rem">Biên lợi nhuận: ${p.profit_margin}%</p>` : ""}
        <div class="product-tags">
          ${(p.tags || []).map(t => `<span class="product-tag">${t.name}</span>`).join("")}
        </div>
        <p class="product-detail-desc">${p.description || "Sản phẩm chính hãng, bảo hành 12 tháng."}</p>
        <div style="margin-top:20px;padding:16px;background:var(--bg-glass);border-radius:var(--radius);border:1px solid var(--border)">
          <div style="font-size:0.875rem;color:var(--text-secondary)">
            📦 Tồn kho: <strong style="color:${p.stock === 0 ? 'var(--danger)' : p.is_low_stock ? 'var(--warning)' : 'var(--success)'}">${p.stock === 0 ? "Hết hàng" : p.stock + " sản phẩm"}</strong>
          </div>
          ${p.supplier ? `<div style="font-size:0.875rem;color:var(--text-secondary);margin-top:6px">🏭 Nhà cung cấp: ${p.supplier.name}</div>` : ""}
        </div>
        <div style="display:flex;gap:12px;margin-top:24px">
          <button class="btn btn-primary btn-lg" style="flex:1"
            onclick="cartStore.addToCart(${p.id})"
            ${p.status === "out_of_stock" ? "disabled" : ""}>
            🛍️ Thêm vào giỏ hàng
          </button>
          <button class="btn btn-ghost btn-lg" onclick="navigate('cart')">🛒 Xem giỏ</button>
        </div>
      </div>
    </div>`;
}

function scrollToFeatured() {
  document.getElementById("featuredSection")?.scrollIntoView({ behavior: "smooth" });
}

function debounceSearch() {
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(loadProducts, 400);
}
