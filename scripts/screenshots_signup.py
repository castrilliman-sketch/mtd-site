"""Screenshots of the email sign-up (homepage section + /free-mtd-kit/), desktop and mobile.
Needs: python3 -m http.server 8765 --directory dist  (running) + playwright.
Usage: python3 scripts/screenshots_signup.py [suffix]   e.g. suffix "-live-preview" after building with a test email config."""
import sys, os
from playwright.sync_api import sync_playwright
suf = sys.argv[1] if len(sys.argv) > 1 else ''
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'screenshots')
U = 'http://localhost:8765'
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, url, vp, sel, full in [
        ('signup-homepage-desktop', '/', (1366, 900), '#kit-home', False),
        ('signup-homepage-mobile', '/', (390, 844), '#kit-home', False),
        ('kit-landing-desktop', '/free-mtd-kit/', (1366, 900), None, False),
        ('kit-landing-desktop-full', '/free-mtd-kit/', (1366, 900), None, True),
        ('kit-landing-mobile', '/free-mtd-kit/', (390, 844), None, False),
        ('kit-landing-mobile-full', '/free-mtd-kit/', (390, 844), None, True),
        ('signup-inline-guide-desktop', '/do-i-need-mtd/', (1366, 900), '#kit-inline', False),
        ('signup-inline-product-mobile', '/software/xero/', (390, 844), '#kit-inline', False)]:
        pg = b.new_page(viewport={'width': vp[0], 'height': vp[1]}, device_scale_factor=1); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pg.goto(U + url); pg.wait_for_timeout(600)
        path = f'{OUT}/{name}{suf}.png'
        if sel:
            el = pg.query_selector(sel); el.scroll_into_view_if_needed(); pg.wait_for_timeout(200)
            if vp[0] < 500: pg.screenshot(path=path, full_page=False, clip=None) if False else el.screenshot(path=path)
            else: el.screenshot(path=path)
        else:
            pg.screenshot(path=path, full_page=full)
        print(name + suf, 'errors:', errs)
        pg.close()
    b.close()
