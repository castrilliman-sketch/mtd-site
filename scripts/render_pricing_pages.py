import sys,re,json
from playwright.sync_api import sync_playwright
urls=json.load(open(sys.argv[1]))
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(locale='en-GB',user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36',viewport={'width':1366,'height':900})
    for key,u in urls.items():
        pg=ctx.new_page()
        try:
            pg.goto(u,timeout=45000,wait_until='domcontentloaded'); pg.wait_for_timeout(4000)
            t=pg.inner_text('body')
            open(f'data/raw/pricing/{key}.txt','w').write(pg.url+'\n'+t)
            print(key,'OK',len(t),pg.url,flush=True)
        except Exception as e: print(key,'ERR',str(e)[:100],flush=True)
        pg.close()
    b.close()
