# MTD Software Compare – MTD for Income Tax software directory

Static site for https://mtdsoftwarecompare.co.uk. The domain is not live yet; nothing has been published to it.

## Build & preview
    python3 build.py                      # writes ./dist (pure Python 3, no deps)
    python3 scripts/check_site.py dist    # JSON-LD parses, FAQ text visible, no personal emails (or pass the live base URL)
    cd dist && python3 -m http.server 8765 # preview at http://localhost:8765/
    python3 scripts/screenshots.py         # needs server running + playwright

## Data
- `data/raw/hmrc-products.json` – all products from HMRC's software finder (sole trader/landlord "view all" list), incl. every feature status. Refresh: `python3 scripts/scrape_hmrc.py` (needs a fresh `data/raw/hmrc-results.html` from the finder).
- `data/vendor-verified.json` – hand-checked prices, joint-property support and affiliate programme facts, each with a source URL and check date (`checked` overall; a product's own `price_checked` overrides it when re-checked later). Add facts here only with a source.
- `data/raw/pricing/*.txt` – rendered text of vendor pages used as evidence.
- `data/products.json` – merged output (generated).

## Search indexing of product pages (`config/indexing.json`)
New domain, so product pages are released to Google gradually instead of all 179 at once. Every `/software/<slug>/` page stays live and linked from the homepage; pages that aren't released get `<meta name="robots" content="noindex,follow">` and are left out of `sitemap.xml`.
- A product page is **indexable** if its slug is in `always_index` (the affiliate-programme products) or `release_for_indexing`, or if `auto_index_verified` is true and `data/vendor-verified.json` has a checked `price_text` + `price_source` + `price_note` for it.
- `hold_noindex` forces a page to noindex (overrides everything).
- To drip-feed more pages: add slugs (see `data/products.json`) to `release_for_indexing`, rebuild, push, then resubmit the sitemap in Search Console. Unknown slugs stop the build.
- All non-product pages (home, Do I need MTD?, methodology, guides, about, privacy, disclosure, Founders Blog, free kit) are always indexable; the kit confirmation pages and 404 are noindex. `build.py` prints the indexable/noindex counts.

## Search Console / Bing verification (`config/verification.json`)
If verifying by HTML tag instead of DNS, paste only the `content` value into `google_site_verification` and/or `bing_msvalidate`; the tag is added to the homepage `<head>` only. Leave empty when verified by DNS TXT record.

## Affiliate links
`config/affiliates.json` maps product slug -> tracked URL. Empty = official site, no `rel=sponsored`. When filled, the button becomes `rel="sponsored nofollow noopener"`, gets an inline disclosure, and the disclosure page lists it automatically.

## Before launch (D)
- Brand and canonical URL are set in `config/site.json` (`MTD Software Compare`, `https://mtdsoftwarecompare.co.uk`). Register the domain and point DNS before publishing.
- Public contact email is `customerservices@mtdsoftwarecompare.co.uk` in `config/site.json` (`contact_email`). The privacy page asks people to contact by email; to show a business postal address instead, add `"postal_address": "..."` to `config/site.json` (never a home address unless D chooses to). The About page and operator name (Daniel Wyatt) are in place.
- Founders Blog posts live in `data/blog/*.md` (YAML-like front matter + Markdown) and are built by `build.py`.

## Analytics & private stats (off until configured)
- Provider: GoatCounter (cookieless, free hosted service). Config: `config/analytics.json` – tracking only loads when `provider` and `site_id` are both set; until then `dist/` contains no analytics code at all.
- `src/analytics.js` (copied to dist only when on) sends: page views (GoatCounter's own script), outbound clicks `out:<aff|site|link>:<slug|host>:<page>` (product buttons carry `data-product`/`data-aff`), Start-here buttons `start:<preset>:<page>`, filter state `filter:<f1+f2>[:search]:<page>` (debounced 1.5s, search text never sent), engaged seconds `time:<s>:<page>`. Honours Do Not Track / Global Privacy Control and an opt-out button on /privacy/.
- Privacy page text switches automatically to describe exactly what is collected when analytics is on.
- Dashboard: `GOATCOUNTER_TOKEN=... python3 scripts/stats.py [--days 30 | --from YYYY-MM-DD --to YYYY-MM-DD]` -> `stats/index.html` (private, git-ignored, not in dist). Uses GoatCounter's CSV export API, which needs Settings → Data collection → "Individual pageviews" ON. `--csv file` reads a downloaded export; `--sample` writes `stats/sample.html` with FAKE, red-bannered numbers for layout checks only.
- Affiliate earnings: add real network-report rows to `stats/earnings.csv` (`date,network,product_slug,clicks,sales,commission_gbp`).

## Email list: Free MTD Ready Kit (off until configured)
- Lead magnet: `kit/mtd-ready-kit-2026-28.pdf` + `kit/mtd-deadlines-2026-28.ics`, generated from `data/deadlines.json` by `python3 scripts/make_kit.py` (needs playwright). Re-run after renaming the site.
- Config: `config/email.json` (provider-agnostic; recommended provider Brevo). Until `provider` and `form_action` are set, every form is replaced by an "Email us for the free kit" mailto link to `contact_email` (kit sent by hand, no list), and no sign-up JavaScript is published.
- Where the form appears: homepage section after Start here, inline box on the guide and every product page, landing page `/free-mtd-kit/`, plus `/free-mtd-kit/confirmed/` (kit download after double opt-in) and `/free-mtd-kit/check-your-inbox/` (no-JS fallback). Both are noindex.
- `src/signup.js` posts the form to the provider, shows a "check your inbox" message, and fires the analytics event `signup:<role>:<page>` (no personal data).
- Privacy page text switches automatically when the email list is on.
- Stats: the dashboard shows form submissions and conversion per page (GoatCounter) and, with `BREVO_API_KEY` + `list_id`, confirmed subscribers and roles from Brevo.
- Test a live-looking build without a real account: `MTD_EMAIL_CONFIG=/path/to/test.json python3 build.py`.
- Email drafts and the Brevo setup checklist: `emails/README.md`.
