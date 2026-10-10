# Product Catalog Scraper

> An open-source project by **Cartdock** — automation & scraping for e-commerce teams.

A clean, production-style web scraper that exports e-commerce product data
(title, price, rating, availability) to CSV.

**Built as a portfolio demonstration** — it targets
[browse.toscrape.com](http://browse.toscrape.com/) / `books.toscrape.com`,
a site specifically created for scraping practice, so the demo is polite,
legal, and safe to run publicly.

## What it demonstrates

- ✅ Session reuse with automatic retry + exponential backoff (429/5xx)
- ✅ Rate limiting — configurable delay between requests (being a good citizen)
- ✅ Structured parsing with BeautifulSoup (CSS selectors, defensive `.select_one`)
- ✅ Typed data model with `dataclasses`
- ✅ CLI arguments via `argparse`
- ✅ CSV export with proper `utf-8` encoding
- ✅ Clean exit codes and a summary report

## Quick start

```bash
git clone <your-repo-url>
cd demo-scraper

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate    # macOS/Linux

pip install -r requirements.txt

python scraper.py
```

Output:

```
Scraping up to 3 page(s) from http://books.toscrape.com/
  Fetching page 1… 20 products
  Fetching page 2… 20 products
  Fetching page 3… 20 products

  Saved 60 rows → output/books.csv

──── Summary ────
  Products scraped : 60
  Price range      : £10.00 – £59.99
  Average price    : £38.63
  Average rating   : 3.9 / 5
```

## CLI options

| Flag | Default | Description |
|---|---|---|
| `--pages N` | `3` | Number of catalogue pages to scrape |
| `--output PATH` | `output/books.csv` | Where to write the CSV |
| `--delay SECONDS` | `0.8` | Pause between requests |

## Sample output

| title | price | rating | availability |
|---|---|---|---|
| A Light in the Attic | £51.77 | 3 | In stock (22 available) |
| Tipping the Velvet | £53.74 | 1 | In stock (20 available) |
| Soumission | £50.10 | 1 | In stock (20 available) |

## Extending this into real client work

This same architecture scales to real projects:

1. **Swap the target** — parse any store's product/search pages
2. **Schedule it** — run daily via `cron` / GitHub Actions and diff prices
3. **Store it** — replace the CSV writer with PostgreSQL or Google Sheets
4. **Alert on changes** — email/Slack when a competitor changes a price
5. **JS-heavy sites** — swap `requests` for Playwright (same parse logic)

## Ethics & legality

Only scrape sites whose `robots.txt` and Terms of Service permit it, keep
request rates low, identify your crawler in the User-Agent, and never
republish copyrighted content. This demo targets a site built for practice.

## License

MIT — use it, learn from it, build on it.
