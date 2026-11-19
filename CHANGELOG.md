# Changelog: pages added

Nightly routine adds one original page per run. Newest first.

- 2026-11-19 · Site brand set to MTD Software Compare. Canonical URL is https://mtdsoftwarecompare.co.uk. The build writes a GitHub Pages CNAME file. The domain is not live yet.
- 2026-11-19 · /guides/jointly-owned-property-mtd/ · "Jointly owned property and Making Tax Digital: what you report, and how software handles it". Sourced from GOV.UK (keep digital records, send quarterly updates, qualifying income). New `joint_table`/`joint_n` guide tokens in build.py list software with a provider-sourced joint-ownership statement. Linked from /do-i-need-mtd/, the free MTD software guide, product pages' joint-property fact, and the methodology page; guides index and sitemap pick it up automatically.
- 2026-11-18 · /guides/free-mtd-software/ · Unverified free-version products now sit at the bottom of the product list, in muted grey, with an accessible pop-up (“We haven't verified this one yet”) before following a link. Without JavaScript the links work as normal.
- 2026-11-18 · /guides/free-mtd-software/ · "Free MTD software for Income Tax: what's really free, and the catches". Also added the guides system (data/guides/*.html with JSON meta + {{tokens}} from build.py), /guides/ index, "Guides" nav/footer links, Article + FAQPage + Breadcrumb structured data, sitemap entries, and links from the homepage free section, /do-i-need-mtd/ and every free-version product page.
