from playwright.sync_api import sync_playwright
import os
os.makedirs('/workspace/mtd-site/screenshots',exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch()
    for name,url,vp,full in [('homepage-desktop','http://localhost:8765/',(1366,900),False),('homepage-desktop-full','http://localhost:8765/',(1366,900),True),
                             ('homepage-mobile','http://localhost:8765/',(390,844),False),('product-xero-desktop','http://localhost:8765/software/xero/',(1366,900),True),
                             ('product-xero-mobile','http://localhost:8765/software/xero/',(390,844),False),('guide-do-i-need-mtd','http://localhost:8765/do-i-need-mtd/',(1366,900),False),
                             ('homepage-filtered-landlord-free','http://localhost:8765/?f=free&f=uk_property#directory',(1366,900),False)]:
        pg=b.new_page(viewport={'width':vp[0],'height':vp[1]}); errs=[]
        pg.on('pageerror',lambda e: errs.append(str(e))); pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
        pg.goto(url); pg.wait_for_timeout(800)
        if not full and 'filtered' not in name: pg.evaluate('window.scrollTo(0,0)')
        if full:
            pg.screenshot(path=f'/workspace/mtd-site/screenshots/{name}.png',full_page=True,clip=None)
        else:
            pg.screenshot(path=f'/workspace/mtd-site/screenshots/{name}.png')
        print(name, pg.inner_text('#count') if pg.query_selector('#count') else '', errs)
        pg.close()
    b.close()
