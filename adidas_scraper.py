import requests
import json
import csv
import time
import random
import re
from datetime import datetime

# ============================================================
#  ADIDAS PRODUCT SCRAPER  —  complete, ready to run
#  pip install requests
#  python adidas_scraper.py
# ============================================================

# ── CONFIG ──────────────────────────────────────────────────
BASE_URL          = "https://www.adidas.com/us/men-shoes"
API_URL           = "https://www.adidas.com/api/product-list/{ids}?sitePath=us"
TOTAL_PAGES       = 34          # ← start with 2 to test. change to 34 for full run
PRODUCTS_PER_PAGE = 48
BATCH_SIZE        = 8
OUTPUT_FILE       = "adidas_products.csv"

# ── HEADERS ─────────────────────────────────────────────────
HEADERS = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "referer": "https://www.adidas.com/us/men-shoes",
    "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
}

# ── COOKIES (from your cURL) ─────────────────────────────────
# If you get 403 errors, re-copy the cURL from DevTools and
# replace the values below with the fresh ones.
COOKIES = {
    "badab": "false",
    "x-browser-id": "c4b91c8b-d88b-40ad-abcd-730e8fc83b43",
    "mt.v": "5.052317592.1773424159913",
    "channelflow": "nonpaid|other|1776016160581",
    "channeloriginator": "nonpaid",
    "channelcloser": "nonpaid",
    "_fbp": "fb.1.1773424163023.274032942247962066",
    "coveo_visitorId": "09949c5e-9db7-4fbb-8f99-246c3ea236d1",
    "_gcl_au": "1.1.1055725547.1773424164",
    "_ga": "GA1.1.671320926.1773424164",
    "geo_ip": "39.35.170.181",
    "geo_country": "PK",
    "onesite_country": "US",
    "adidas_country": "us",
    "gl-feat-enable": "CHECKOUT_PAGES_ENABLED",
    "x-session-id": "35fd9bac-31cd-413d-996f-693acd320f39",
    "x-site-locale": "en_US",
    "x-original-host": "www.adidas.com",
    "x-environment": "production",
    "x-commerce-next-id": "175bae89-c205-42fc-9df2-7c4e958751af",
}

# ── FALLBACK IDs (from your cURL — always works for API test) ─
FALLBACK_IDS = [
    "HQ2285","IH9314","KD1499","JL3812",
    "JV8467","IH4172","KD1497","KD8307",
]


# ════════════════════════════════════════════════════════════
#  STEP 1 — COLLECT PRODUCT IDs FROM LISTING PAGES
# ════════════════════════════════════════════════════════════

def get_ids_from_page(start: int) -> list:
    """
    Fetch one listing page and try 3 different methods to find IDs.
    Method A: regex on href links  →  /us/shoe-name/HQ2285.html
    Method B: __NEXT_DATA__ JSON   →  Next.js embeds all data in HTML
    Method C: data attributes      →  data-product-id="HQ2285"
    """
    url = f"{BASE_URL}?start={start}" if start > 0 else BASE_URL

    try:
        resp = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=20)

        if resp.status_code != 200:
            print(f"    [!] HTTP {resp.status_code} for start={start}")
            return []

        html = resp.text
        ids  = []

        # ── Method A: href pattern ───────────────────────────
        ids += re.findall(r'/[a-z0-9\-]+/([A-Z]{2}[A-Z0-9]{4})\.html', html)

        # ── Method B: __NEXT_DATA__ embedded JSON ────────────
        if not ids:
            nd = re.search(
                r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                html, re.DOTALL
            )
            if nd:
                try:
                    nd_str = nd.group(1)
                    ids += re.findall(r'"productId"\s*:\s*"([A-Z]{2}[A-Z0-9]{4})"', nd_str)
                    ids += re.findall(r'"id"\s*:\s*"([A-Z]{2}[A-Z0-9]{4})"', nd_str)
                except Exception:
                    pass

        # ── Method C: data attributes ────────────────────────
        if not ids:
            ids += re.findall(r'data-product-id="([A-Z]{2}[A-Z0-9]{4})"', html)
            ids += re.findall(r'data-model-id="([A-Z]{2}[A-Z0-9]{4})"', html)

        # Deduplicate preserving order
        seen, unique = set(), []
        for pid in ids:
            if pid not in seen:
                seen.add(pid)
                unique.append(pid)
        return unique

    except Exception as e:
        print(f"    [!] Exception on start={start}: {e}")
        return []


def collect_all_ids(total_pages: int) -> list:
    all_ids, seen = [], set()

    print(f"\n{'='*58}")
    print(f"  STEP 1  —  Listing pages  ({total_pages} pages)")
    print(f"{'='*58}")

    for page_num in range(total_pages):
        start   = page_num * PRODUCTS_PER_PAGE
        print(f"  Page {page_num+1}/{total_pages}  start={start}", end="  ")

        ids     = get_ids_from_page(start)
        new_ids = [i for i in ids if i not in seen]
        all_ids.extend(new_ids)
        seen.update(new_ids)
        print(f"→  {len(new_ids)} new  |  total: {len(all_ids)}")

        if page_num < total_pages - 1:
            time.sleep(random.uniform(2.5, 5.0))

    print(f"\n  Unique IDs collected: {len(all_ids)}")
    return all_ids


# ════════════════════════════════════════════════════════════
#  STEP 2 — FETCH PRODUCT DATA FROM API IN BATCHES
# ════════════════════════════════════════════════════════════

def fetch_batch(ids: list) -> list:
    url = API_URL.format(ids=",".join(ids))
    try:
        resp = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=20)
        if resp.status_code != 200:
            print(f"    [!] API HTTP {resp.status_code}")
            return []
        return resp.json()
    except Exception as e:
        print(f"    [!] API error: {e}")
        return []


def fetch_all_products(all_ids: list) -> list:
    batches      = [all_ids[i:i+BATCH_SIZE] for i in range(0, len(all_ids), BATCH_SIZE)]
    all_products = []

    print(f"\n{'='*58}")
    print(f"  STEP 2  —  API calls  ({len(batches)} batches of {BATCH_SIZE})")
    print(f"{'='*58}")

    for i, batch in enumerate(batches):
        label = ",".join(batch[:3]) + ("..." if len(batch) > 3 else "")
        print(f"  Batch {i+1}/{len(batches)}  [{label}]", end="  ")

        products = fetch_batch(batch)
        all_products.extend(products)
        print(f"→  {len(products)} products  |  total: {len(all_products)}")

        if i < len(batches) - 1:
            time.sleep(random.uniform(1.5, 3.5))

    print(f"\n  Products from API: {len(all_products)}")
    return all_products


# ════════════════════════════════════════════════════════════
#  STEP 3 — PARSE FIELDS FROM EACH PRODUCT JSON
# ════════════════════════════════════════════════════════════

def extract_fields(p: dict) -> dict:
    attr    = p.get("attribute_list", {})
    pricing = p.get("pricing_information", {})
    desc    = p.get("product_description", {})

    # ── Prices ───────────────────────────────────────────────
    current_price  = pricing.get("currentPrice") or pricing.get("standard_price", "")
    original_price = pricing.get("standard_price", "")
    sale_price     = pricing.get("sale_price", "")
    discount       = ""
    for pi in p.get("price_information", []):
        if pi.get("type") == "original" and pi.get("discount_percentage"):
            discount = f"{abs(pi['discount_percentage'])}% off"
            break

    # ── Sizes ────────────────────────────────────────────────
    variations = p.get("variation_list", [])
    sizes      = " | ".join([v.get("size", "") for v in variations if v.get("size")])

    # ── Image ────────────────────────────────────────────────
    plp       = p.get("product_listing_assets", [])
    image_url = plp[0].get("image_url", "") if plp else ""
    if not image_url:
        vl        = p.get("view_list", [])
        image_url = vl[0].get("image_url", "") if vl else ""

    # ── Product URL ──────────────────────────────────────────
    canonical   = p.get("meta_data", {}).get("canonical", "")
    product_url = f"https:{canonical}" if canonical.startswith("//") else canonical

    # ── Features / USPs ──────────────────────────────────────
    usps = " | ".join([u.strip() for u in desc.get("usps", []) if u.strip()])

    # ── Color variant count ───────────────────────────────────
    color_variants = sum(
        1 for x in p.get("product_link_list", [])
        if x.get("type") == "color-variation"
    )

    # ── Badge (Best Seller, New, Selling Fast, etc.) ──────────
    badge = ""
    for x in p.get("product_link_list", []):
        if x.get("productId") == p.get("id") and x.get("badge_text"):
            badge = x["badge_text"]
            break

    return {
        "product_id":      p.get("id", ""),
        "name":            p.get("name", "").strip(),
        "brand":           attr.get("brand", ""),
        "category":        attr.get("category", ""),
        "product_type":    (attr.get("productType") or [""])[0],
        "gender":          attr.get("gender", ""),
        "sport":           ", ".join(attr.get("sport", [])),
        "sport_sub":       ", ".join(attr.get("sportSub", [])),
        "color":           attr.get("color", ""),
        "search_color":    attr.get("search_color", ""),
        "color_variants":  color_variants,
        "badge":           badge,
        "current_price":   current_price,
        "original_price":  original_price,
        "sale_price":      sale_price,
        "discount":        discount,
        "on_sale":         attr.get("sale", False),
        "is_outlet":       attr.get("outlet", False),
        "is_orderable":    attr.get("is_orderable", True),
        "sizes_available": sizes,
        "num_sizes":       len(variations),
        "base_material":   ", ".join(attr.get("base_material", [])),
        "product_fit":     ", ".join(attr.get("productfit", [])),
        "closure":         ", ".join(attr.get("closure", [])),
        "surface":         ", ".join(attr.get("surface", [])),
        "subtitle":        desc.get("subtitle", "").replace("\n", " ").strip(),
        "description":     desc.get("text", "").replace("\n", " ").strip(),
        "usps":            usps,
        "image_url":       image_url,
        "product_url":     product_url,
        "model_number":    p.get("model_number", ""),
        "base_model":      p.get("base_model_number", ""),
        "scraped_at":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ════════════════════════════════════════════════════════════
#  STEP 4 — SAVE TO CSV
# ════════════════════════════════════════════════════════════

def save_csv(rows: list, filename: str):
    if not rows:
        print("  [!] No rows to save.")
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved  {len(rows)} rows  →  {filename}")


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

def main():
    print("\n" + "="*58)
    print("  ADIDAS SCRAPER")
    print(f"  URL    : {BASE_URL}")
    print(f"  Pages  : {TOTAL_PAGES}  (~{TOTAL_PAGES*PRODUCTS_PER_PAGE} products)")
    print(f"  Output : {OUTPUT_FILE}")
    print("="*58)

    # ── Step 1 ───────────────────────────────────────────────
    all_ids = collect_all_ids(TOTAL_PAGES)

    if not all_ids:
        print("\n  [!] Listing page returned 0 IDs (page is JS-rendered).")
        print(f"  [!] Using {len(FALLBACK_IDS)} hardcoded fallback IDs to test API.")
        all_ids = FALLBACK_IDS

    # ── Step 2 ───────────────────────────────────────────────
    raw = fetch_all_products(all_ids)

    if not raw:
        print("\n  [ERROR] API returned 0 products.")
        print("  Cookies may be expired. Steps to fix:")
        print("  1. Open adidas.com in Chrome")
        print("  2. DevTools → Network → Fetch/XHR → reload page")
        print("  3. Find a product-list request → right-click → Copy as cURL")
        print("  4. Paste new cookie values into the COOKIES dict at top of script")
        return

    # ── Step 3 ───────────────────────────────────────────────
    print(f"\n{'='*58}")
    print(f"  STEP 3  —  Parsing {len(raw)} products")
    print(f"{'='*58}")

    rows = []
    for p in raw:
        try:
            rows.append(extract_fields(p))
        except Exception as e:
            print(f"  [!] Parse error  {p.get('id','?')}:  {e}")

    print(f"  Parsed: {len(rows)} products")

    # ── Step 4 ───────────────────────────────────────────────
    print(f"\n{'='*58}")
    print(f"  STEP 4  —  Saving CSV")
    print(f"{'='*58}")
    save_csv(rows, OUTPUT_FILE)

    # ── Summary ──────────────────────────────────────────────
    on_sale  = sum(1 for r in rows if r["on_sale"])
    outlet   = sum(1 for r in rows if r["is_outlet"])
    shoes    = sum(1 for r in rows if r["category"] == "Shoes")
    clothing = sum(1 for r in rows if r["category"] == "Clothing")

    print(f"\n{'='*58}")
    print(f"  DONE")
    print(f"  Total    : {len(rows)}")
    print(f"  Shoes    : {shoes}")
    print(f"  Clothing : {clothing}")
    print(f"  On sale  : {on_sale}")
    print(f"  Outlet   : {outlet}")
    print(f"  File     : {OUTPUT_FILE}")
    print(f"{'='*58}\n")


if __name__ == "__main__":
    main()