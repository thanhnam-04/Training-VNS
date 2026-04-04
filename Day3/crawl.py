"""
Scraper xe ô tô từ oto.com.vn
Dùng Playwright để bypass Cloudflare/anti-bot

Cài đặt:
    pip install playwright beautifulsoup4 pandas
    playwright install chromium
"""

import asyncio
import random
import json
import re
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page

BASE_URL = "https://oto.com.vn"


# ──────────────────────────────────────────────
# PARSE HTML
# ──────────────────────────────────────────────
def parse_car_listings(html: str) -> list[dict]:
    """Parse danh sách xe từ HTML trang oto.com.vn."""
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.item-car.dev-item-car")
    results = []

    for card in cards:
        item = {}

        # --- Product ID & VIP type ---
        item["product_id"] = card.get("data-autoid", "")
        item["vip_type"]   = card.get("data-cuid", "")

        # --- Thông tin từ data-tinrao: "Brand.Model.Condition.ID.VipType" ---
        tinrao = card.get("data-tinrao", "")
        parts = tinrao.split(".")
        if len(parts) >= 3:
            item["brand"]     = parts[0]
            item["model"]     = parts[1]
            item["condition"] = parts[2]  # Xe mới / Xe cũ

        # --- Link ---
        link_tag = card.select_one("div.photo a")
        if link_tag:
            item["url"] = BASE_URL + link_tag.get("href", "")

        # --- Tên xe ---
        name_tag = card.select_one("span.car-name")
        item["car_name"] = name_tag.get_text(strip=True) if name_tag else ""

        # --- Giá ---
        price_tag = card.select_one("p.price")
        item["price"] = price_tag.get_text(strip=True) if price_tag else ""

        # --- Tags: nhiên liệu, hộp số, tình trạng ---
        tags = [li.get_text(strip=True) for li in card.select("ul.tag-list li")]
        item["fuel"]        = tags[0] if len(tags) > 0 else ""
        item["transmission"]= tags[1] if len(tags) > 1 else ""
        item["car_status"]  = tags[2] if len(tags) > 2 else ""

        # --- Người bán ---
        seller_tag = card.select_one("li.seller-name span.txt")
        item["seller_name"] = seller_tag.get_text(strip=True) if seller_tag else ""

        # --- Đại lý xác thực ---
        verify_tag = card.select_one("span.icon-verify")
        item["verified"] = verify_tag.get("data-value", "") if verify_tag else ""

        # --- Địa điểm ---
        loc_tag = card.select_one("li.seller-location")
        if loc_tag:
            item["location"] = loc_tag.get_text(strip=True).replace("", "").strip()

        # --- Số điện thoại ---
        phone_tag = card.select_one("li.seller-phone span.txt")
        if phone_tag:
            item["phone"] = phone_tag.get_text(strip=True).replace("", "").strip()

        # --- Thêm thông tin chi tiết từ data-call ---
        # Format: "Brand.Model.Condition.Origin.Year.Price.BodyType.Color.ListType.VipType.ID."
        call_tag = card.select_one("a.btn-call")
        if call_tag:
            call_data = call_tag.get("data-call", "").split(".")
            if len(call_data) >= 9:
                item["origin"]    = call_data[3]  # Trong nước / Nhập khẩu
                item["year"]      = call_data[4]
                item["body_type"] = call_data[6]
                item["color"]     = call_data[7]

        if item.get("product_id"):
            results.append(item)

    return results


# ──────────────────────────────────────────────
# PLAYWRIGHT SCRAPER
# ──────────────────────────────────────────────
async def scrape_page(page: Page, url: str, page_num: int) -> list[dict]:
    """Tải 1 trang và parse tin đăng."""
    # oto.com.vn dùng ?pi=N cho phân trang
    page_url = url if page_num == 1 else f"{url}?pi={page_num}"
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Cào trang {page_num}: {page_url}")

    await page.goto(page_url, wait_until="domcontentloaded", timeout=30_000)

    try:
        await page.wait_for_selector("div.item-car.dev-item-car", timeout=15_000)
    except Exception:
        print(f"  ⚠ Không tìm thấy xe ở trang {page_num}")
        return []

    # Cuộn để lazy-load
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
    await asyncio.sleep(random.uniform(1.0, 2.0))
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(random.uniform(1.0, 1.5))

    html = await page.content()
    items = parse_car_listings(html)
    print(f"  ✓ {len(items)} xe")
    return items


async def scrape_all(
    url: str = "https://oto.com.vn/mua-ban-xe",
    max_pages: int = 3,
    headless: bool = True,
    delay: tuple = (2.0, 4.0),
) -> list[dict]:
    all_items = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="vi-VN",
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = await context.new_page()

        for page_num in range(1, max_pages + 1):
            items = await scrape_page(page, url, page_num)
            if not items:
                break
            all_items.extend(items)
            if page_num < max_pages:
                t = random.uniform(*delay)
                print(f"  ⏳ Chờ {t:.1f}s...")
                await asyncio.sleep(t)

        await browser.close()

    return all_items


# ──────────────────────────────────────────────
# LƯU KẾT QUẢ
# ──────────────────────────────────────────────
def save_results(items: list[dict], prefix: str = "oto") -> None:
    if not items:
        print("⚠ Không có dữ liệu.")
        return

    df = pd.DataFrame(items)

    csv_file = f"{prefix}_data.csv"
    df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    print(f"\n✅ Đã lưu {len(df)} xe vào '{csv_file}'")

    json_file = f"{prefix}_data.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã lưu '{json_file}'")

    cols = ["brand", "model", "year", "price", "fuel", "body_type", "color", "location", "seller_name"]
    show = [c for c in cols if c in df.columns]
    print("\n=== PREVIEW (5 dòng đầu) ===")
    print(df[show].head().to_string())


# ──────────────────────────────────────────────
# CHẠY
# ──────────────────────────────────────────────
if __name__ == "__main__":
    items = asyncio.run(
        scrape_all(
            url="https://oto.com.vn/mua-ban-xe",   # đổi URL tùy ý
            max_pages=20,
            headless=True,    # False = hiện browser để debug
            delay=(2.5, 4.5),
        )
    )
    save_results(items)


# ──────────────────────────────────────────────
# CÁC URL MẪU
# ──────────────────────────────────────────────
# Tất cả xe mới:   https://oto.com.vn/mua-ban-xe-moi
# Xe cũ:           https://oto.com.vn/mua-ban-xe-cu
# VinFast:         https://oto.com.vn/mua-ban-xe-vinfast
# Toyota:          https://oto.com.vn/mua-ban-xe-toyota
# Hà Nội:          https://oto.com.vn/mua-ban-xe-ha-noi
# TP.HCM:          https://oto.com.vn/mua-ban-xe-tp-hcm
# SUV:             https://oto.com.vn/mua-ban-xe-suv
# Dưới 500 triệu:  https://oto.com.vn/mua-ban-xe/gia-xe-duoi-500-trieu