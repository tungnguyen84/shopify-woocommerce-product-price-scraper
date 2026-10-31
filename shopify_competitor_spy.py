#!/usr/bin/env python3
"""
Shopify Store Competitor Product, Price & Contact Spy Pro
Author: Tung Nguyen (@tungnguyen84)
Cloud Version: https://apify.com/tungnguyen84/shopify-store-product-contact-scraper
"""
import argparse
import csv
import json
import re
import urllib.request
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

def fetch_url(url, timeout=15):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def scrape_shopify_store(store_url, max_pages=5):
    if not store_url.startswith("http"):
        store_url = "https://" + store_url
    parsed = urlparse(store_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    domain = parsed.netloc.replace("www.", "")

    emails = set()
    try:
        home_html = fetch_url(origin)
        for e in EMAIL_RE.findall(home_html):
            el = e.lower()
            if not el.endswith((".png", ".jpg", ".gif", ".svg", ".webp", ".js", ".css")) and "shopify.com" not in el and "sentry.io" not in el:
                emails.add(el)
    except Exception:
        pass

    rows = []
    for page in range(1, max_pages + 1):
        try:
            raw = fetch_url(f"{origin}/products.json?limit=250&page={page}")
            data = json.loads(raw)
            products = data.get("products", [])
            if not products:
                break
            for p in products:
                v = (p.get("variants") or [{}])[0]
                img = (p.get("images") or [{}])[0].get("src", "")
                rows.append({
                    "store_domain": domain,
                    "product_id": p.get("id", ""),
                    "title": p.get("title", ""),
                    "vendor": p.get("vendor", ""),
                    "product_type": p.get("product_type", ""),
                    "price": v.get("price", ""),
                    "compare_at_price": v.get("compare_at_price", ""),
                    "in_stock": v.get("available", False),
                    "sku": v.get("sku", ""),
                    "variants_count": len(p.get("variants") or []),
                    "tags": ", ".join(p.get("tags") or []),
                    "product_url": f"{origin}/products/{p.get('handle', '')}",
                    "image_url": img,
                    "store_emails": "; ".join(sorted(emails)),
                })
        except Exception:
            break
    return rows

def main():
    parser = argparse.ArgumentParser(description="Shopify Competitor Product & Price Spy Pro")
    parser.add_argument("stores", nargs="*", default=["https://allbirds.com"], help="Shopify store URLs")
    parser.add_argument("--output", "-o", default="shopify_products_export.csv", help="Output CSV file")
    args = parser.parse_args()

    all_rows = []
    for s in args.stores:
        print(f"[*] Scraping Shopify store: {s} ...")
        r = scrape_shopify_store(s)
        print(f"    -> Extracted {len(r)} products.")
        all_rows.extend(r)

    if all_rows:
        fields = list(all_rows[0].keys())
        with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(all_rows)
        print(f"[+] Saved {len(all_rows)} products to {args.output}")

if __name__ == "__main__":
    main()
