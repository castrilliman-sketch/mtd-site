import re,html,json,time,urllib.request,http.cookiejar,datetime
BASE='https://www.tax.service.gov.uk'
s=open('data/raw/hmrc-results.html').read()
blocks=re.findall(r'<div id="software-vendor-\d+">(.*?)</p>\s*</div>',s,re.S)
cj=http.cookiejar.CookieJar(); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders=[('User-Agent','Mozilla/5.0 (research; local directory build)')]
def clean(x): return html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',x))).strip()
out=[]
for b in blocks:
    name=clean(re.search(r'<h3[^>]*>(.*?)</h3>',b,re.S).group(1))
    rows={clean(k):clean(v) for k,v in re.findall(r'<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>',b,re.S)}
    pid=re.search(r'productId=(\d+)',b).group(1)
    url=f'{BASE}/find-making-tax-digital-income-tax-software/product-details?productId={pid}'
    try:
        p=op.open(url,timeout=30).read().decode()
    except Exception as e:
        print('ERR',name,e); p=''
    m=p[p.find('<main'):p.find('</main>')]
    site=re.search(r'<a [^>]*href="(https?://[^"]+)"[^>]*>\s*Explore this software',m)
    feats={}
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>',m,re.S):
        cells=[clean(c) for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>',tr,re.S)]
        if len(cells)==2 and cells[1] in ('Ready now','In development','Not included'): feats[cells[0]]=cells[1]
    spec={clean(k):clean(v) for k,v in re.findall(r'<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>',m,re.S)}
    out.append(dict(name=name,hmrc_product_id=pid,hmrc_url=url,summary=rows,website=site.group(1) if site else None,features=feats,specs=spec))
    print(len(out),name,len(feats),site.group(1) if site else None,flush=True)
    time.sleep(0.6)
json.dump(dict(source='https://www.tax.service.gov.uk/find-making-tax-digital-income-tax-software/',retrieved=datetime.date.today().isoformat(),count=len(out),products=out),open('data/raw/hmrc-products.json','w'),indent=1)
