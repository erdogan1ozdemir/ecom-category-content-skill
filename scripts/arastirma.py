#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bir kategori sayfası için brief araştırmasını tek seferde toplar ve JSON dosyasına yazar.

Pazar ve dil marka profilinden gelir (ayar.json: location_code, language_code, ulke; varsayılan Türkiye/Türkçe).

Topladıkları:
  1. Google SERP (mobil) - ilk 10 organik, PAA soruları, ilgili aramalar, AI Overview ve kaynakları,
     markanın sitesinin bu kelimede sıralanan sayfası; ayrıca "{kelime} nasıl seçilir" bilgi
     niyetli SERP'i (PAA ve AI Overview kategori kelimesinde çıkmasa da burada çıkar) ve Google
     otomatik tamamlama önerileri (soru ve uzun kuyruk fikirleri)
  2. Kelime kümesi - ana kelimeyi taşıyan öneriler + ilişkili kelimeler, 12 aylık hacim ve aylık dağılım;
     soru kalıpları ve uzun kuyruk ayrı listelenir
  3. İlk 5 rakip sayfanın içeriği - başlıklar, kelime sayısı, SSS soruları, iç link sayısı
  4. Sitenin kelime haritası - ana kelimeyi taşıyan sorgularda sitenin HANGİ sayfası sıralanıyor
     (cannibalization haritasının SERP tarafı; GSC tarafı gsc MCP ile ayrıca çekilir)

Kullanım:
    python3 arastirma.py --marka boyner "kadın mont" --url https://www.boyner.com.tr/kadin-mont-x-g3731-c23896554 --cikti $T/arastirma.json
    python3 arastirma.py --marka flormar "fondöten" --cikti x.json --ek "likit fondöten"     # ek tohum kelimeler
    python3 arastirma.py --marka X "..." --harita harita.json   # GSC/SEOmonitor'dan derlenen harita: DataForSEO haritası çekilmez

DataForSEO kimliği ~/.claude.json içindeki dfs-mcp yapılandırmasından okunur; depoda kimlik tutulmaz.
Sonuçlar 30 gün önbellekte tutulur (~/.cache/ecom-kategori-icerik/dfs/); --yeni ile atlanır.
"""
import argparse, base64, html, json, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak
from ortak import getir, duz, kumeler

DFS = "https://api.dataforseo.com"
SORU = re.compile(r"\b(nasil|nedir|ne|neden|nicin|hangi|hangisi|kac|kaca|mi|mu|midir|nerede|nereden|kim|"
                  r"ne zaman|olur mu|olmali|farki|arasindaki)\b")


def kimlik():
    cfg = json.load(open(os.path.expanduser("~/.claude.json")))
    env = cfg["mcpServers"]["dfs-mcp"]["env"]
    return base64.b64encode(f"{env['DATAFORSEO_USERNAME']}:{env['DATAFORSEO_PASSWORD']}".encode()).decode()


ONBELLEK_GUN = 30
LOC = lambda: ortak.AYAR.get("location_code") or 2792
DIL = lambda: ortak.AYAR.get("language_code") or "tr"
YENI = False        # --yeni: önbelleği atla


def post(yol, govde, auth, saniye=180):
    """DataForSEO isteği; aynı istek 30 gün boyunca önbellekten gelir (aynı SERP/kelime tekrar ücretlendirilmez)."""
    import hashlib
    anahtar = hashlib.md5((yol + json.dumps(govde, sort_keys=True, ensure_ascii=False)).encode()).hexdigest()
    dosya = ortak.genel_onbellek("dfs", f"{anahtar}.json")
    if not YENI and os.path.exists(dosya) and time.time() - os.path.getmtime(dosya) < ONBELLEK_GUN * 86400:
        d = json.load(open(dosya))
        d["cost"] = 0          # önbellekten geldi
        return d
    d = _post(yol, govde, auth, saniye)
    if (d.get("tasks") or [{}])[0].get("status_code") == 20000:
        os.makedirs(os.path.dirname(dosya), exist_ok=True)
        json.dump(d, open(dosya, "w"), ensure_ascii=False)
    return d


def _post(yol, govde, auth, saniye=180):
    import tempfile
    fd, f = tempfile.mkstemp(prefix="dfs_ecom_", suffix=".json")   # paralel çalışmada çakışmasın
    with os.fdopen(fd, "w") as fh:
        json.dump(govde, fh, ensure_ascii=False)
    r = subprocess.run(["curl", "-sS", "-m", str(saniye), "-X", "POST", DFS + yol,
                        "-H", f"Authorization: Basic {auth}", "-H", "Content-Type: application/json",
                        "--data-binary", f"@{f}"], capture_output=True, text=True)
    os.unlink(f)
    if r.returncode != 0:
        raise SystemExit(f"curl hatası: {r.stderr[:300]}")
    d = json.loads(r.stdout)
    t = (d.get("tasks") or [{}])[0]
    if t.get("status_code") not in (20000, None):
        print(f"UYARI {yol}: {t.get('status_code')} {t.get('status_message')}", file=sys.stderr)
    return d


def sonuc(res):
    r = (res.get("tasks") or [{}])[0].get("result") or [{}]
    return r[0] or {}


def serp(kw, auth, cihaz="mobile"):
    res = post("/v3/serp/google/organic/live/advanced",
               [{"keyword": kw, "location_code": LOC(), "language_code": DIL(), "device": cihaz, "depth": 30,
                 "people_also_ask_click_depth": 2, "load_async_ai_overview": True}], auth)
    items = sonuc(res).get("items") or []
    if not items:
        print(f"UYARI: '{kw}' için SERP boş döndü", file=sys.stderr)
    organik = [{"sira": i.get("rank_group"), "domain": i.get("domain"),
                "url": re.sub(r"[?&]srsltid=[^&]*", "", i.get("url") or ""),
                "baslik": i.get("title"), "aciklama": i.get("description")} for i in items if i["type"] == "organic"]
    aio = next((i for i in items if i["type"] == "ai_overview"), None)
    return {
        "kelime": kw,
        "organik": organik[:10],
        "site": [o for o in organik if ortak.AYAR["domain"] in (o["domain"] or "")],
        "paa": [q.get("title") for i in items if i["type"] == "people_also_ask" for q in i.get("items") or []],
        "ilgili_aramalar": sorted({q for i in items if i["type"] == "related_searches" for q in i.get("items") or []}
                                  | {q.get("title") for i in items if i["type"] == "people_also_search"
                                     for q in i.get("items") or [] if isinstance(q, dict) and q.get("title")}),
        "ai_overview": None if not aio else {
            "metin": " ".join((x.get("text") or "") for x in aio.get("items") or [])[:1500],
            "kaynaklar": [r.get("domain") for r in aio.get("references") or []]},
        "serp_ogeleri": sorted({i["type"] for i in items}),
        "maliyet": res.get("cost"),
    }


def kelimeler(tohumlar, auth, limit=250):
    """Öneriler (tohumu içeren) + ilişkili kelimeler; hacme göre sıralı, soru ve uzun kuyruk işaretli."""
    havuz, maliyet = {}, 0

    def ekle(kw, ki):
        h = (ki or {}).get("search_volume") or 0
        if h < 10 or kw in havuz:
            return
        ay = {f"{m['year']}-{m['month']:02d}": m["search_volume"] for m in (ki.get("monthly_searches") or [])}
        son3 = sorted(ay.items())[-3:]
        havuz[kw] = {"kelime": kw, "hacim": h, "son3_ort": round(sum(v or 0 for _, v in son3) / max(1, len(son3))),
                     "zirve_ay": max(ay, key=lambda k: ay[k] or 0) if ay else None,
                     "soru": bool(SORU.search(duz(kw))), "kelime_sayisi": len(kw.split())}

    for t in tohumlar:
        r = post("/v3/dataforseo_labs/google/keyword_suggestions/live",
                 [{"keyword": t, "location_code": LOC(), "language_code": DIL(), "limit": limit,
                   "include_seed_keyword": True, "order_by": ["keyword_info.search_volume,desc"]}], auth)
        maliyet += r.get("cost") or 0
        s = sonuc(r)
        if s.get("seed_keyword_data"):
            ekle(t, s["seed_keyword_data"].get("keyword_info"))
        for it in s.get("items") or []:
            ekle(it["keyword"], it.get("keyword_info"))
        time.sleep(1)
        r = post("/v3/dataforseo_labs/google/related_keywords/live",
                 [{"keyword": t, "location_code": LOC(), "language_code": DIL(), "depth": 1, "limit": 100}], auth)
        maliyet += r.get("cost") or 0
        for it in sonuc(r).get("items") or []:
            kd = it.get("keyword_data") or {}
            ekle(kd.get("keyword"), kd.get("keyword_info"))
        time.sleep(1)
    liste = sorted(havuz.values(), key=lambda x: -x["hacim"])
    return {"liste": liste, "sorular": [k for k in liste if k["soru"]],
            "uzun_kuyruk": [k for k in liste if k["kelime_sayisi"] >= 3 and not k["soru"]], "maliyet": maliyet}


SORU_KALIP = ["{k} nasıl", "{k} hangi", "hangi {k}", "{k} ne", "{k} kaç", "{k} mı", "{k} mi", "en iyi {k}",
              "{k} neden", "{k} ile", "{k} için", "{k} nasıl seçilir", "{k} nasıl kombinlenir", "{k} nasıl yıkanır",
              "{k} beden", "{k} fark"]


def otomatik_tamamlama(tohumlar):
    """Google arama önerileri (ücretsiz). Kategori kelimelerinde PAA çoğu zaman çıkmaz; soru ve uzun
    kuyruk fikirlerinin asıl kaynağı budur. Hacim taşımaz, hacim için kelime kümesine bakılır."""
    from urllib.parse import quote
    out = {}
    for t in tohumlar:
        for kalip in SORU_KALIP:
            q = kalip.format(k=t)
            ham = getir(f"https://suggestqueries.google.com/complete/search?client=firefox&hl={DIL()}&gl={ortak.AYAR.get('ulke') or 'tr'}&q=" + quote(q),
                        saniye=15, deneme=1)
            try:
                for o in json.loads(ham)[1]:
                    out.setdefault(o, q)
            except Exception:
                pass
            time.sleep(0.3)
    return [{"oneri": o, "kalip": k, "soru": bool(SORU.search(duz(o)))} for o, k in out.items()]


def site_haritasi(tohum, auth, limit=300):
    """Tohumu taşıyan sorgularda sitenin sıralanan sayfası. Aynı niyette iki farklı site URL'si
    görünüyorsa cannibalization adayıdır; kelime -> URL eşlemesi brief'teki sahiplik tablosuna girer."""
    res = post("/v3/dataforseo_labs/google/ranked_keywords/live",
               [{"target": ortak.AYAR["domain"], "location_code": LOC(), "language_code": DIL(), "limit": limit,
                 "filters": [["keyword_data.keyword", "like", f"%{tohum}%"]],
                 "order_by": ["keyword_data.keyword_info.search_volume,desc"]}], auth)
    out = []
    for it in sonuc(res).get("items") or []:
        kd, se = it.get("keyword_data") or {}, (it.get("ranked_serp_element") or {}).get("serp_item") or {}
        out.append({"kelime": kd.get("keyword"), "hacim": (kd.get("keyword_info") or {}).get("search_volume"),
                    "sira": se.get("rank_group"), "url": se.get("url")})
    return {"liste": out, "maliyet": res.get("cost")}


def sayfa_icerigi_js(url, auth):
    r = post("/v3/on_page/content_parsing/live", [{"url": url, "enable_javascript": True}], auth, 120)
    it = (sonuc(r).get("items") or [{}])[0] or {}
    pc = (it.get("page_content") or {})
    bas, metin = [], []
    for blok in (pc.get("main_topic") or []) + (pc.get("secondary_topic") or []):
        if blok.get("h_title"):
            bas.append((f"H{blok.get('level') or '?'}", blok["h_title"]))
        metin += [x.get("text") or "" for x in blok.get("primary_content") or []]
        metin += [x.get("text") or "" for x in blok.get("secondary_content") or []]
    metin = [m for m in metin if len(m.split()) >= 12]
    if not (bas or metin):
        return None
    t = " ".join(metin)
    return {"url": url, "kaynak": "dataforseo", "kelime": len(t.split()), "basliklar": bas[:60],
            "sorular": [b for _, b in bas if b.strip().endswith("?")][:30], "ozet": t[:1200]}


def sayfa_icerigi_jina(url):
    """Yedek 1 (ücretsiz): r.jina.ai okuyucusu sayfayı tarayıcıda çalıştırıp markdown döndürür. JavaScript ile
    oluşan ve doğrudan indirmede boş gelen rakip sayfalarda (ör. lcw) çalışır; bot korumalı sayfalar yine boş kalır."""
    # tarayıcı User-Agent'ı gönderilmez: jina tarayıcı gibi görünen istekleri Cloudflare doğrulamasına yönlendiriyor
    h = subprocess.run(["curl", "-sSL", "-m", "60", "-H", "Accept: text/plain", "https://r.jina.ai/" + url],
                       capture_output=True, text=True).stdout
    if not h or len(h.split()) < 150 or "Just a moment" in h[:500]:
        return None
    bas = [(f"H{len(m.group(1))}", m.group(2).strip()) for m in re.finditer(r"^(#{1,4})\s+(.+)$", h, re.M)]
    bas = [(t, b) for t, b in bas if 3 < len(b) < 140]
    par = [p.strip() for p in h.split("\n") if len(p.split()) >= 12 and not p.lstrip().startswith(("[", "!", "|", "*"))]
    return {"url": url, "kaynak": "jina", "kelime": sum(len(p.split()) for p in par), "paragraf": len(par),
            "basliklar": bas[:60], "sorular": [b for _, b in bas if b.endswith("?")][:30], "ozet": " ".join(par)[:1200]}


def sayfa_icerigi_playwright(url):
    """Yedek 2 (ücretsiz, yerel): bot korumalı sayfalar için Playwright. Pazar yeri kategori sayfalarında H2'ler
    ürün adıdır; 'sorular' ve 'basliklar' bu yüzden ürün adı gibi uzun başlıklar elenerek verilir."""
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pw_oku.py"), url],
                       capture_output=True, text=True, timeout=180)
    try:
        d = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return None
    if d.get("hata") or not d.get("basliklar"):
        return None
    par = d["paragraflar"]
    bas = [(h, b) for h, b in d["basliklar"] if len(b.split()) <= 9]
    return {"url": url, "kaynak": "playwright", "kelime": sum(len(p.split()) for p in par), "paragraf": len(par),
            "basliklar": bas[:60], "sorular": [b for _, b in bas if b.endswith("?")][:30], "ozet": " ".join(par)[:1200]}


def sayfa_icerigi(url, auth=None, _ikinci=False):
    """Rakip sayfanın içerik iskeleti. Önce doğrudan indirir; engellenirse ya da metin tarayıcıda
    oluşuyorsa DataForSEO içerik çözümlemesine düşer."""
    h = getir(url, saniye=30, deneme=1)
    kaynak = "dogrudan"
    if len(h) < 5000 or "Just a moment" in h[:800] or "captcha" in h[:3000].lower():
        # yedek sırası: 1) r.jina.ai (ücretsiz)  2) yerel Playwright (ücretsiz)  3) DataForSEO ayrıştırma (ücretli)
        return (sayfa_icerigi_jina(url) or sayfa_icerigi_playwright(url) or (auth and sayfa_icerigi_js(url, auth))
                or {"url": url, "kaynak": "okunamadi"})
    ham_h = h
    h2 = re.sub(r"<(script|style|noscript|svg|header|nav|footer)\b.*?</\1>", " ", h, flags=re.S | re.I)
    temiz = lambda x: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()
    bas = [(t.upper(), temiz(x)) for t, x in re.findall(r"<(h[1-4])[^>]*>(.*?)</\1>", h2, re.S | re.I)]
    bas = [(t, b) for t, b in bas if 3 < len(b) < 140]
    # SEO metni çoğunlukla en uzun paragraf kümesindedir; ürün kartlarını ayıklamak için <p> metinleri sayılır
    par = [temiz(x) for x in re.findall(r"<p[^>]*>(.*?)</p>", h2, re.S | re.I)]
    par = [x for x in par if len(x.split()) >= 12]
    sss = re.findall(r'"@type"\s*:\s*"Question"\s*,\s*"name"\s*:\s*"(.*?)"', h)
    if sum(len(x.split()) for x in par) < 150 and auth and not _ikinci:
        # metin tarayıcıda oluşuyor olabilir: JavaScript çalıştıran çözümlemeyle bir kez daha denenir
        r = sayfa_icerigi_js(url, auth)
        if r and r.get("kelime", 0) > sum(len(x.split()) for x in par):
            return r
    return {"url": url, "kaynak": kaynak, "title": temiz((re.search(r"<title[^>]*>(.*?)</title>", h, re.S) or [0, ""])[1]),
            "kelime": sum(len(x.split()) for x in par), "paragraf": len(par), "basliklar": bas[:60],
            "sorular": sorted(set([b for _, b in bas if b.strip().endswith("?")] + [html.unescape(s) for s in sss]))[:30],
            "faq_schema": bool(sss), "ozet": " ".join(par)[:1200]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ortak.arguman_ekle(ap)
    ap.add_argument("kelime", help="ana kelime, ör. 'kadın mont'")
    ap.add_argument("--cikti", required=True)
    ap.add_argument("--url", help="hedef sayfa adresi (SERP'te hangi sayfanın sıralandığıyla karşılaştırılır)")
    ap.add_argument("--ek", nargs="*", default=[], help="ek tohum kelimeler (eş anlamlı, üst kavram)")
    ap.add_argument("--rakip", type=int, default=5, help="içeriği okunacak rakip sayısı")
    ap.add_argument("--harita", help="site sıralama haritası JSON'u ([{kelime, hacim, sira, url}]); verilirse DataForSEO "
                                     "haritası çekilmez (SEOmonitor / GSC / Ahrefs'ten derlenmiş liste)")
    ap.add_argument("--yeni", action="store_true", help="30 günlük DataForSEO önbelleğini atla")
    a = ap.parse_args()
    ortak.ayar_args(a)

    global YENI
    YENI = a.yeni
    auth = kimlik()
    veri = {"kelime": a.kelime, "hedef_url": a.url, "tarih": time.strftime("%Y-%m-%d")}
    print("1/4 SERP, PAA ve AI Overview...", flush=True)
    veri["serp"] = serp(a.kelime, auth)
    print("2/4 kelime kümesi...", flush=True)
    veri["kelimeler"] = kelimeler([a.kelime] + a.ek, auth)
    print("   soru ve uzun kuyruk önerileri (otomatik tamamlama + bilgi niyetli SERP)...", flush=True)
    veri["oneriler"] = otomatik_tamamlama([a.kelime] + a.ek)
    veri["serp_bilgi"] = serp(a.kelime + " nasıl seçilir", auth, "desktop")
    if not veri["serp_bilgi"]["organik"]:          # DataForSEO ara sıra boş döner; bir kez yeniden denenir
        time.sleep(5)
        veri["serp_bilgi"] = serp(a.kelime + " nasıl seçilir", auth, "desktop")
    print("3/4 rakip sayfa içerikleri...", flush=True)
    rakipler = [o["url"] for o in veri["serp"]["organik"] if ortak.AYAR["domain"] not in (o["domain"] or "")][:a.rakip]
    veri["rakip_icerik"] = [sayfa_icerigi(u, auth) for u in rakipler]
    print("4/4 site kelime haritası...", flush=True)
    if a.harita:
        veri["site_haritasi"] = {"liste": json.load(open(a.harita, encoding="utf-8")), "maliyet": 0, "kaynak": "dış (SEOmonitor/GSC/Ahrefs)"}
    else:
        veri["site_haritasi"] = site_haritasi(a.kelime, auth)
    veri["domain"] = ortak.AYAR["domain"]
    json.dump(veri, open(a.cikti, "w"), ensure_ascii=False, indent=2)

    s, k = veri["serp"], veri["kelimeler"]
    ana = next((x for x in k["liste"] if x["kelime"] == a.kelime.lower()), None)
    print(f"\nyazıldı: {a.cikti}")
    print(f"  ana kelime hacmi: {ana and ana['hacim']} (son 3 ay ort. {ana and ana['son3_ort']}, zirve {ana and ana['zirve_ay']})")
    print(f"  kelime: {len(k['liste'])} · soru: {len(k['sorular'])} · uzun kuyruk: {len(k['uzun_kuyruk'])} · PAA: {len(s['paa'])}"
          f" (+{len(veri['serp_bilgi']['paa'])} bilgi niyetli) · öneri: {len(veri['oneriler'])}"
          f" · AI Overview: {'var' if s['ai_overview'] else 'yok'} / bilgi SERP: {'var' if veri['serp_bilgi']['ai_overview'] else 'yok'}")
    print("  SERP ilk 10: " + ", ".join(f"{o['sira']}.{o['domain']}" for o in s["organik"]))
    b = s["site"]
    print(f"  {ortak.AYAR['domain']}: " + (", ".join(f"{o['sira']}. {o['url']}" for o in b) if b else "ilk 30'da yok"))
    if a.url and b and not ortak.ayni_adres(b[0]["url"].split("?")[0], a.url.split("?")[0]):
        print("  DİKKAT: SERP'te sıralanan site sayfası hedef URL değil. Hedef teyit edilmeden içerik yazılmaz.")
    for r in veri["rakip_icerik"]:
        print(f"  rakip · {r['url'][:70]} · {r.get('kaynak')} · {r.get('kelime', '-')} kelime · {len(r.get('basliklar') or [])} başlık"
              f" · {len(r.get('sorular') or [])} soru")
    harita = {}
    for x in veri["site_haritasi"]["liste"]:
        harita.setdefault(x["url"], []).append(x["kelime"])
    print(f"  site haritası: {len(veri['site_haritasi']['liste'])} kelime, {len(harita)} farklı URL")


if __name__ == "__main__":
    main()
