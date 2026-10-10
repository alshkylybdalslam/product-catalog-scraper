"""
Product Catalog Scraper — demo project
======================================
Scrapes product data (title, price, rating, availability) from a
scraping-friendly practice store and exports it to CSV.

Built as a portfolio sample: polite by design (retries, rate limiting,
clear output), dependency-light, and runnable in one command.

Target site: books.toscrape.com — a site explicitly built for scraping
practice, so this demo is safe to run and show publicly.

Usage:
    python scraper.py                    # scrape 3 pages -> output/books.csv
    python scraper.py --pages 10         # scrape 10 pages
    python scraper.py --output my.csv    # custom output file
    python scraper.py --delay 1.5        # slower, extra polite
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "http://books.toscrape.com/"
PAGE_URL = BASE_URL + "catalogue/page-{}.html"

USER_AGENT = (
    "PortfolioDemoScraper/1.0 (+educational demo; contact: your-email@example.com)"
)

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}

CSV_COLUMNS = ["title", "price", "rating", "availability", "url"]


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Product:
    title: str
    price: str          # kept as string ("£51.77") to preserve currency symbol
    rating: int         # 1–5
    availability: str   # e.g. "In stock (22 available)"
    url: str


# ---------------------------------------------------------------------------
# HTTP session with retry/backoff
# ---------------------------------------------------------------------------


def build_session() -> requests.Session:
    """Create a session that retries transient failures automatically."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def fetch(session: requests.Session, url: str, delay: float) -> BeautifulSoup:
    """Fetch a URL, respect the delay, and parse it."""
    time.sleep(delay)
    response = session.get(url, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_page(soup: BeautifulSoup) -> list[Product]:
    """Extract every product on one catalogue page."""
    products: list[Product] = []

    for pod in soup.select("article.product_pod"):
        anchor = pod.select_one("h3 a")
        rating_el = pod.select_one("p.star-rating")
        price_el = pod.select_one("p.price_color")
        avail_el = pod.select_one("p.instock")

        # Rating lives in a CSS class like "star-rating Three"
        rating_words = (
            rating_el.get("class", []) if rating_el else []
        )
        rating = next(
            (RATING_MAP[w] for w in rating_words if w in RATING_MAP), 0
        )

        products.append(
            Product(
                title=anchor.get("title", "").strip() if anchor else "",
                price=price_el.get_text(strip=True) if price_el else "",
                rating=rating,
                availability=avail_el.get_text(" ", strip=True) if avail_el else "",
                url=requests.compat.urljoin(BASE_URL, anchor["href"]) if anchor else "",
            )
        )

    return products


def find_next_page(soup: BeautifulSoup) -> str | None:
    """Return the absolute URL of the next catalogue page, or None."""
    next_li = soup.select_one("li.next a")
    if not next_li or not next_li.get("href"):
        return None
    return requests.compat.urljoin(PAGE_URL.format(1), next_li["href"])


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def write_csv(products: list[Product], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for p in products:
            writer.writerow(
                {
                    "title": p.title,
                    "price": p.price,
                    "rating": p.rating,
                    "availability": p.availability,
                    "url": p.url,
                }
            )


def print_summary(products: list[Product]) -> None:
    if not products:
        print("No products collected.")
        return

    prices = []
    for p in products:
        digits = "".join(c for c in p.price if c.isdigit() or c == ".")
        try:
            prices.append(float(digits))
        except ValueError:
            pass

    ratings = [p.rating for p in products if p.rating]

    print("\n---- Summary ----")
    print(f"  Products scraped : {len(products)}")
    if prices:
        print(f"  Price range      : £{min(prices):.2f} – £{max(prices):.2f}")
        print(f"  Average price    : £{sum(prices) / len(prices):.2f}")
    if ratings:
        print(f"  Average rating   : {sum(ratings) / len(ratings):.1f} / 5")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def scrape(pages: int, delay: float) -> list[Product]:
    session = build_session()
    products: list[Product] = []
    url: str | None = PAGE_URL.format(1)
    page_num = 0

    while url and page_num < pages:
        page_num += 1
        print(f"  Fetching page {page_num}... ", end="", flush=True)
        try:
            soup = fetch(session, url, delay)
        except requests.RequestException as exc:
            print(f"failed ({exc})")
            break

        batch = parse_page(soup)
        products.extend(batch)
        print(f"{len(batch)} products")

        url = find_next_page(soup)

    return products


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape product data from books.toscrape.com into a CSV."
    )
    parser.add_argument(
        "--pages", type=int, default=3,
        help="number of catalogue pages to scrape (default: 3)",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("output/books.csv"),
        help="output CSV path (default: output/books.csv)",
    )
    parser.add_argument(
        "--delay", type=float, default=0.8,
        help="seconds to wait between requests (default: 0.8)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    # Windows consoles default to cp1252, which breaks on £ and other symbols.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args(argv if argv is not None else sys.argv[1:])

    print(f"Scraping up to {args.pages} page(s) from {BASE_URL}")
    products = scrape(args.pages, args.delay)

    if not products:
        print("Nothing collected — check your connection and try again.")
        return 1

    write_csv(products, args.output)
    print(f"\n  Saved {len(products)} rows -> {args.output}")
    print_summary(products)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
