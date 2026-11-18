# PlainMTD (working title) – MTD for Income Tax software directory, stage 1

Local-only static site. Nothing is deployed.

## Build & preview
    python3 build.py                      # writes ./dist (pure Python 3, no deps)
    cd dist && python3 -m http.server 8765 # preview at http://localhost:8765/
    python3 scripts/screenshots.py         # needs server running + playwright

## Data
- `data/raw/hmrc-products.json` – all products from HMRC's software finder (sole trader/landlord "view all" list), incl. every feature status. Refresh: `python3 scripts/scrape_hmrc.py` (needs a fresh `data/raw/hmrc-results.html` from the finder).
- `data/vendor-verified.json` – hand-checked prices, joint-property support and affiliate programme facts, each with a source URL and check date. Add facts here only with a source.
- `data/raw/pricing/*.txt` – rendered text of vendor pages used as evidence.
- `data/products.json` – merged output (generated).

## Affiliate links
`config/affiliates.json` maps product slug -> tracked URL. Empty = official site, no `rel=sponsored`. When filled, the button becomes `rel="sponsored nofollow noopener"`, gets an inline disclosure, and the disclosure page lists it automatically.

## Before launch (D)
- Choose brand/domain → `config/site.json` (`name`, `base_url`).
- Fill in About page, corrections email and privacy operator details (marked in yellow).

## Analytics & private stats (off until configured)
- Provider: GoatCounter (cookieless, free hosted service). Config: `config/analytics.json` – tracking only loads when `provider` and `site_id` are both set; until then `dist/` contains no analytics code at all.
- `src/analytics.js` (copied to dist only when on) sends: page views (GoatCounter's own script), outbound clicks `out:<aff|site|link>:<slug|host>:<page>` (product buttons carry `data-product`/`data-aff`), Start-here buttons `start:<preset>:<page>`, filter state `filter:<f1+f2>[:search]:<page>` (debounced 1.5s, search text never sent), engaged seconds `time:<s>:<page>`. Honours Do Not Track / Global Privacy Control and an opt-out button on /privacy/.
- Privacy page text switches automatically to describe exactly what is collected when analytics is on.
- Dashboard: `GOATCOUNTER_TOKEN=... python3 scripts/stats.py [--days 30 | --from YYYY-MM-DD --to YYYY-MM-DD]` -> `stats/index.html` (private, git-ignored, not in dist). Uses GoatCounter's CSV export API, which needs Settings → Data collection → "Individual pageviews" ON. `--csv file` reads a downloaded export; `--sample` writes `stats/sample.html` with FAKE, red-bannered numbers for layout checks only.
- Affiliate earnings: add real network-report rows to `stats/earnings.csv` (`date,network,product_slug,clicks,sales,commission_gbp`).
