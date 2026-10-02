#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bot korumalı / JavaScript'le oluşan sayfayı yerel Playwright (Chromium) ile okur ve JSON basar.
Bağlama token yazmaz (MCP Playwright'ın aksine sonuç betiğe döner). Önce headless, olmazsa headed denenir.

İki kip:
  varsayılan   rakip içerik iskeleti: başlıklar ve paragraflar (arastirma.py kullanır)
  --liste      listeleme sayfası: render edilmiş tam HTML + gömülü durum JSON'u (window.__NUXT__,
               __NEXT_DATA__, __INITIAL_STATE__, __STATE__, __PRELOADED_STATE__); sayfa.py --pw kullanır.
               Çıktı büyük olduğu için --cikti dosyasına yazılır.

Kullanım:
    python3 pw_oku.py URL            # {"url","kaynak":"playwright","basliklar":[[H,metin]],"paragraflar":[...]}
    python3 pw_oku.py URL --liste --cikti /tmp/sayfa.json
"""
import json, sys

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
DURUM_JS = """()=>{for(const a of ['__NUXT__','__NEXT_DATA__','__INITIAL_STATE__','__STATE__','__PRELOADED_STATE__','__APOLLO_STATE__']){
  try{ if(window[a]){ const gor=new WeakSet();
    const s=JSON.stringify(window[a],(k,v)=>{ if(typeof v==='function') return undefined;
      if(typeof v==='object'&&v!==null){ if(gor.has(v)) return undefined; gor.add(v);} return v; });
    if(s && s.length<12000000) return s; } }catch(e){} } return null }"""


def oku(url, headless=True, liste=False):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled", "--disable-http2"])
        c = b.new_context(locale="tr-TR", viewport={"width": 1366, "height": 900}, user_agent=UA)
        pg = c.new_page()
        yanit = pg.goto(url, wait_until="domcontentloaded", timeout=45000)
        pg.wait_for_timeout(2500)
        for _ in range(4):                      # alttaki SEO metni ve ürün kartları kaydırınca yüklenir
            pg.mouse.wheel(0, 2500); pg.wait_for_timeout(500)
        if liste:
            d = {"html": pg.content(), "durum": pg.evaluate(DURUM_JS), "kod": yanit.status if yanit else None,
                 "son_url": pg.url}
        else:
            d = pg.evaluate("""()=>{const hs=[...document.querySelectorAll('h1,h2,h3,h4')].map(e=>[e.tagName,e.innerText.trim()]).filter(x=>x[1].length>3&&x[1].length<140);
              const ps=[...document.querySelectorAll('p')].map(e=>e.innerText.trim()).filter(x=>x.split(/\\s+/).length>=12);
              return {title:document.title,hs,ps}}""")
        b.close()
        return d


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    url = sys.argv[1]
    liste = "--liste" in sys.argv
    cikti = sys.argv[sys.argv.index("--cikti") + 1] if "--cikti" in sys.argv else None
    err = ""
    for hl in (True, False):
        try:
            d = oku(url, hl, liste)
            if liste:
                sonuc = {"url": url, "kaynak": "playwright", **d}
            else:
                sonuc = {"url": url, "kaynak": "playwright", "baslik_sayfa": d["title"], "basliklar": d["hs"],
                         "paragraflar": d["ps"][:80]}
            break
        except Exception as e:
            err = str(e)[:150]
    else:
        sonuc = {"url": url, "kaynak": "playwright", "hata": err}
    if cikti:
        json.dump(sonuc, open(cikti, "w", encoding="utf-8"), ensure_ascii=False)
        print(json.dumps({"url": url, "cikti": cikti, "hata": sonuc.get("hata")}, ensure_ascii=False))
    else:
        print(json.dumps(sonuc, ensure_ascii=False))
