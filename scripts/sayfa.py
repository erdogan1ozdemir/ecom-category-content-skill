#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bir listeleme (kategori / marka) sayfasının canlı kaydını okur: meta, mevcut SEO metni, ürün gamı.

Kayıt içeriğin gerçeklik zeminidir: metinde anılan alt kategori, marka, renk, materyal ve kalıp, sayfada
gerçekten filtrelenebilen değerlerden seçilir. Sayfada olmayan ürün tipi yazılmaz. Bulunamayan alan boş
kalır (uydurma yok); her alanın hangi yöntemle bulunduğu kayıttaki `yontem` sözlüğüne yazılır.

Platform adaptörleri (önce platform tespit edilir, bkz. references/platformlar.md):
  nextjs-boyner  __NEXT_DATA__ içindeki initialState (resolvedPage, getProducts, getFilters, getCloudLinking)
  nextjs / nuxt  __NEXT_DATA__ ya da __NUXT_DATA__ / window.__NUXT__ JSON'unda genel anahtar araması
  shopify        /collections/{handle}.json ve /collections/{handle}/products.json (ücretsiz JSON uçları)
  akinon         sayfa adresine ?format=json (pagination, facets, sorters, products)
  vtex           /api/catalog_system/pub/products/search ve /facets/search (denenir, olmazsa HTML)
  diğerleri      JSON-LD (BreadcrumbList, ItemList, Product) + HTML sezgisel (filtre blokları, ürün kartları,
                 sayfadaki uzun metin bloğu)
Hiçbiri yetmezse --pw ile yerel Playwright render edilmiş DOM'dan aynı sezgisel okuma yapılır.

Kullanım:
    python3 sayfa.py --marka flormar URL                     # özet (insan okur)
    python3 sayfa.py --marka flormar URL --cikti kayit.json  # tam kayıt (içerik HTML'i dahil)
    python3 sayfa.py --marka flormar URL --icerik            # mevcut içeriği düz metin olarak basar
    python3 sayfa.py --domain x.com.tr URL --gam             # kırılımların ürün sayısı ve örnek ürünleri (yavaş)
    python3 sayfa.py ... --pw                                # alanlar boş kalırsa Playwright ile render edip yeniden dene
"""
import argparse, html, json, os, re, subprocess, sys, tempfile, time
from collections import Counter
from urllib.parse import urlsplit, urljoin, quote, parse_qsl, urlencode
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, dom
from ortak import url_coz, istek, getir_json, kumeler, duz

KIRLI = {"", "-", "belirtilmemis", "belirtilmemiş", "diger", "diğer", "other"}
ATLA_BOYNER = {"categories", "marka", "satici", "priceFilter", "urunPuani", "trueFalseFilter", "cinsiyet"}

PLATFORM_IMZA = [("nextjs", r"__NEXT_DATA__|/_next/static"), ("nuxt", r"__NUXT__|/_nuxt/|__NUXT_DATA__"),
                 ("shopify", r"cdn\.shopify\.com|Shopify\.theme|myshopify\.com"),
                 ("akinon", r"akinoncloud|static_omnishop|akinon"), ("vtex", r"vteximg|vtexassets|vtex\.render|__RUNTIME__|vtexcommerce"),
                 ("ticimax", r"ticimax"), ("magento", r"Magento_|mage/cookies|text/x-magento-init"),
                 ("sfcc", r"demandware|/on/demandware\.|dwvar_"), ("ideasoft", r"ideasoft"), ("tsoft", r"tsoft\.com|T-Soft"),
                 ("woocommerce", r"woocommerce"), ("inveon", r"InvUtility|inveon")]


def metne(h):
    h = re.sub(r"<(br|/p|/div|/h\d|/li)[^>]*>", "\n", h or "", flags=re.I)
    return re.sub(r"[ \t\xa0]+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def icerik_analizi(c):
    c = c or ""
    duz_ = metne(c)
    basliklar = [(t.upper(), metne(x)) for t, x in re.findall(r"<(h[1-6])[^>]*>(.*?)</\1>", c, re.S | re.I)]
    linkler = [(metne(a), html.unescape(u)) for u, a in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', c, re.S | re.I)]
    linkler = [(a, u) for a, u in linkler if a]
    return {"kelime": len(duz_.split()), "basliklar": basliklar, "linkler": linkler,
            "liste": len(re.findall(r"<(ul|ol)\b", c, re.I)), "tablo": len(re.findall(r"<table\b", c, re.I)),
            "soru_baslik": sum(1 for _, b in basliklar if b.rstrip().endswith("?")),
            "sss": bool(re.search(r"sık\w* sorulan|sıkça sorulan|\bSSS\b", duz_, re.I)),
            "siz": len(re.findall(r"\w+(?:abilirsiniz|ebilirsiniz|sınız|siniz|sunuz|sünüz)\b|\bsiz(?:e|i|in)?\b", duz_, re.I)),
            "sen": len(re.findall(r"\w+(?:abilirsin|ebilirsin|malısın|melisin)\b|\bsen(?:i|in|e)?\b|\bsana\b", duz_, re.I)),
            "metin": duz_}


def platform_tespit(h):
    bas = h[:3000000] if h else ""
    return [ad for ad, d in PLATFORM_IMZA if re.search(d, bas)]


def bos_kayit(url):
    return {"url": url, "platform": None, "sayfa_tipi": None, "durum": None, "yonlendirme": None, "title": None,
            "html_title": None, "description": None, "h1": None, "canonical": None, "canonical_kendisi": None,
            "index": None, "meta_robots": None, "icerik_html": "", "breadcrumb": [], "urun_sayisi": None,
            "ornek_urunler": [], "alt_kategoriler": [], "kardes_kategoriler": [], "markalar": [], "cinsiyetler": [], "filtreler": {},
            "fiyat_filtresi": None, "secenek_filtreleri": [], "hizli_filtreler": [], "siralama": [],
            "link_bulutu": [], "yontem": {}, "uyarilar": []}


def ata(k, alan, deger, yontem, ustune=False):
    """Alanı yalnız boşsa doldurur ve yöntemi kaydeder (ilk güvenilir kaynak kazanır)."""
    if deger in (None, "", [], {}) or (k.get(alan) not in (None, "", [], {}) and not ustune):
        return False
    if alan in k.get("_kesin", ()) and not ustune:
        return False
    k[alan] = deger
    k["yontem"][alan] = yontem
    return True


def mutlak(u, taban):
    if not u:
        return u
    return urljoin(taban, html.unescape(u.strip()))


# --- HTML temel alanlar ve JSON-LD -----------------------------------------------------------------

def jsonld(h):
    out = []
    for m in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', h or "", re.S | re.I):
        try:
            v = json.loads(m.strip().rstrip(";"))
        except Exception:
            try:
                v = json.loads(re.sub(r"[\x00-\x1f]", " ", m.strip()))
            except Exception:
                continue
        yigin = v if isinstance(v, list) else [v]
        for x in yigin:
            if isinstance(x, dict) and "@graph" in x:
                out += [g for g in x["@graph"] if isinstance(g, dict)]
            elif isinstance(x, dict):
                out.append(x)
    return out


def _tip_ld(x):
    t = x.get("@type")
    return t if isinstance(t, list) else [t]


def html_temel(h, k, kok, taban):
    t = re.search(r"<title[^>]*>(.*?)</title>", h, re.S | re.I)
    ata(k, "html_title", t and html.unescape(re.sub(r"\s+", " ", t.group(1))).strip(), "html")
    ata(k, "title", k.get("html_title"), "html")
    for m in kok.bul("meta"):
        ad = (m.nit.get("name") or m.nit.get("property") or "").lower()
        if ad == "description":
            ata(k, "description", html.unescape(m.nit.get("content") or "").strip(), "html")
        elif ad == "robots":
            ata(k, "meta_robots", m.nit.get("content"), "html")
    for l in kok.bul("link"):
        if "canonical" in (l.nit.get("rel") or "").lower():
            ata(k, "canonical", mutlak(l.nit.get("href"), taban), "html"); break
    h1 = kok.ilk("h1")
    ata(k, "h1", h1 and h1.metin(), "html")
    ld = jsonld(h)
    for x in ld:
        tip = _tip_ld(x)
        if "BreadcrumbList" in tip:
            bc = []
            for e in x.get("itemListElement") or []:
                it = e.get("item") if isinstance(e.get("item"), dict) else {}
                ad = e.get("name") or it.get("name")
                u = (e.get("item") if isinstance(e.get("item"), str) else it.get("@id") or it.get("url")) or e.get("url")
                if ad:
                    bc.append((html.unescape(str(ad)).strip(), mutlak(u, taban) if u else None))
            ata(k, "breadcrumb", bc, "json-ld:BreadcrumbList")
        if "ItemList" in tip or "CollectionPage" in tip or "OfferCatalog" in tip:
            sayi = x.get("numberOfItems")
            if isinstance(sayi, (int, str)) and str(sayi).isdigit() and int(sayi) > 0:
                ata(k, "urun_sayisi", int(sayi), "json-ld:numberOfItems")
            adlar = []
            for e in x.get("itemListElement") or []:
                it = e.get("item") if isinstance(e, dict) and isinstance(e.get("item"), dict) else e
                if isinstance(it, dict) and it.get("name"):
                    adlar.append(html.unescape(str(it["name"])).strip())
            ata(k, "ornek_urunler", adlar[:12], "json-ld:ItemList")
    urunler = [x for x in ld if "Product" in _tip_ld(x) and x.get("name")]
    if len(urunler) >= 3:
        def marka(x):
            b = x.get("brand")
            return (b.get("name") if isinstance(b, dict) else b) or ""
        ata(k, "ornek_urunler", [(f"{marka(x)} · " if marka(x) else "") + html.unescape(x["name"]) for x in urunler[:12]],
            "json-ld:Product")
    if not k.get("breadcrumb"):
        ata(k, "breadcrumb", html_breadcrumb(kok, taban), "html:breadcrumb")


def html_breadcrumb(kok, taban):
    """En çok öğe taşıyan geçerli breadcrumb listesi; javascript: bağlantılı (sıralama vb.) bloklar elenir."""
    adaylar = list(kok.bul(sinif=r"breadcrumb")) + list(kok.bul(kimlik=r"breadcrumb")) + \
        list(kok.bul(nit={"aria-label": r"breadcrumb|içerik yolu"}))
    en_iyi = []
    for bc in adaylar:
        ogeler = [li for li in bc.bul("li") if li.ust is bc or (li.ust is not None and li.ust.ust is bc)]
        if not ogeler:
            continue
        out, gecersiz = [], False
        for li in ogeler:
            a = li.ilk("a")
            href = a.nit.get("href") if a is not None else None
            if href and href.lower().startswith("javascript"):
                gecersiz = True; break
            t = li.metin().strip(" >/›»")
            if not t and href and urlsplit(mutlak(href, taban)).path in ("", "/"):
                t = "Anasayfa"
            if t:
                out.append((t, mutlak(href, taban) if href and href != "#" else None))
        if not gecersiz and len(out) > len(en_iyi):
            en_iyi = out
    return en_iyi


# --- HTML sezgisel: filtre blokları, ürün kartları, SEO metni --------------------------------------

DEGER_SINIF = r"(filter|facet|refine|filtre)\w*[-_]*(item|option|value|label|choice|link|tag|list-item)|checkbox|swatch|attribute-item"
BASLIK_SINIF = r"title|header|head\b|heading|name|baslik|legend|label-group|toggle"
SAYI_SINIF = r"count|quantity|qty|adet|number|badge"


def _deger_metni(e):
    parca = []

    def gez(d):
        for c in d.cocuk:
            if isinstance(c, str):
                parca.append(c)
            elif c.etiket not in dom.GORUNMEZ and not re.search(SAYI_SINIF, c.sinif(), re.I):
                gez(c)
    gez(e)
    t = re.sub(r"\s+", " ", html.unescape(" ".join(parca))).strip()
    t = re.sub(r"\s*\(?\s*\d[\d.]*\s*\)?\s*$", "", t) if not re.fullmatch(r"[\d\s.,-]+(cm|ml|mm|gr|kg)?", t) else t
    t = re.sub(r"^(.+?) \1$", r"\1", t)          # renk kutucuğunda ad iki kez yazılı: "Siyah Siyah"
    return t.strip(" -·|")


def _degerler(d):
    gorulen, out = set(), []
    for e in d.bul(("label", "li", "a", "option", "button", "span", "div")):
        s = e.sinif()
        girdi = e.ilk("input", nit={"type": r"checkbox|radio"}) is not None or e.etiket == "option"
        if not (girdi or re.search(DEGER_SINIF, s, re.I) or (e.etiket == "a" and re.search(r"[?&](filter|f|q|attr|spec|price|fiyat)|filtre", e.nit.get("href") or "", re.I))):
            continue
        if e.etiket in ("span", "div") and not re.search(DEGER_SINIF, s, re.I):
            continue
        t = _deger_metni(e)
        if not t or len(t) > 60 or t.lower() in KIRLI or t in gorulen:
            continue
        a = e if e.etiket == "a" else e.ilk("a")
        gorulen.add(t)
        out.append((t, a.nit.get("href") if a is not None else None))
    return out


def _baslik_aday(e):
    if e is None or isinstance(e, str):
        return None
    if e.etiket in ("h2", "h3", "h4", "h5", "h6", "legend", "summary", "dt", "strong") or \
            (e.etiket in ("button", "span", "div", "p", "a") and re.search(BASLIK_SINIF, e.sinif(), re.I)):
        t = e.metin()
        if 1 < len(t) <= 40 and not re.fullmatch(r"[\d\s.,()+-]+", t):
            return re.sub(r"\s*[+\-−▾▼]\s*$", "", t).strip()
    return None


def _nit_baslik(e):
    for ad in ("heading", "data-title", "data-name", "data-filter-name", "data-spec-attr-name", "data-facet-name",
               "data-facet", "title", "aria-label"):
        v = (e.nit.get(ad) or "").strip()
        if 1 < len(v) <= 40 and not re.search(r"^(filtre|filter|filters|kapat|close)$", v, re.I):
            return v
    return None


def _onceki_baslik(e, deger_metinleri):
    """e'nin önceki kardeşlerinde (en yakından geriye) başlık arar. Script/stil atlanır; değer taşıyan bir
    kardeşe (başka bir filtre grubu) gelince durulur: yoksa bir önceki grubun başlığı alınır."""
    if e.ust is None:
        return None
    kardes = [c for c in e.ust.cocuk if isinstance(c, dom.Dugum)]
    i = kardes.index(e) if e in kardes else -1
    for ok in reversed(kardes[:max(i, 0)]):
        if ok.etiket in dom.GORUNMEZ:
            continue
        if ok.ilk("input") is not None or len(_degerler(ok)) >= 2:
            return None
        b = _baslik_aday(ok)
        if not b:
            ic = ok.ilk(sinif=BASLIK_SINIF) or ok.ilk(("h2", "h3", "h4", "h5", "legend", "strong"))
            b = _baslik_aday(ic)
        if b and b not in deger_metinleri:
            return b
        if ok.metin():
            return None
    return None


def _grup_basligi(d, deger_metinleri):
    seviye = d
    for derinlik in range(4):
        if seviye is None:
            break
        b = _nit_baslik(seviye)
        if b:
            return b
        if derinlik == 0:
            for e in seviye.bul():
                b = _baslik_aday(e)
                if b and b not in deger_metinleri:
                    return b
                if e.ilk("input") is not None or e.etiket in ("li", "label"):
                    break
        b = _onceki_baslik(seviye, deger_metinleri)
        if b:
            return b
        seviye = seviye.ust
    return None


def filtre_gruplari(kok):
    adaylar = []
    for d in kok.bul(sinif=r"filter|facet|refine|filtre"):
        if re.search(r"selected|secili|applied|active-filter|clear|temizle|sorter|sort", d.sinif(), re.I):
            continue
        deg = _degerler(d)
        if len(deg) >= 2:
            adaylar.append((d, deg))
    kume_ = {id(d) for d, _ in adaylar}
    # en içteki gruplar kalır: başka bir adayın atası olan aday (tüm filtre paneli) atılır
    ata_idleri = set()
    for d, _ in adaylar:
        for a in d.atalar():
            if id(a) in kume_:
                ata_idleri.add(id(a))
    ic = [(d, deg) for d, deg in adaylar if id(d) not in ata_idleri]
    gruplar, gorulen = [], set()
    for d, deg in ic:
        b = _grup_basligi(d, {t for t, _ in deg})
        if not b or b.lower() in gorulen:
            continue
        gorulen.add(b.lower())
        gruplar.append((b, deg[:40]))
    return gruplar


def _grup_esle(k, baslik, degerler, taban, yontem):
    bd = duz(baslik)
    linkli = [(t, mutlak(u, taban)) for t, u in degerler if u and not u.startswith("javascript")]
    if re.search(r"\b(kategori\w*|category|categories|urun tipi|urun turu|alt kategori)\b", bd):
        if len(linkli) >= max(2, len(degerler) // 2):
            ata(k, "alt_kategoriler", linkli, yontem)
        else:
            k["filtreler"].setdefault(baslik, [t for t, _ in degerler]); k["yontem"].setdefault("filtreler", yontem)
    elif re.search(r"\b(marka\w*|brand\w*|tasarimci|designer|vendor)\b", bd):
        ata(k, "markalar", [(t, mutlak(u, taban) if u else None) for t, u in degerler], yontem)
    elif re.search(r"\b(fiyat\w*|price|tutar)\b", bd):
        ata(k, "fiyat_filtresi", True, yontem)
    elif re.search(r"\b(stok\w*|stock|availability|in stock|kargo)\b", bd) and re.search(r"stok|stock", bd):
        return
    elif re.search(r"\b(cinsiyet|gender)\b", bd):
        ata(k, "cinsiyetler", [t for t, _ in degerler], yontem)
    elif re.search(r"\b(sirala\w*|sort|siralama|order)\b", bd) or \
            sum(bool(re.search(r"(?i)önerilen|en çok satan|düşükten|yüksekten|artan fiyat|azalan fiyat|a-z|z-a|yeniden eskiye|eskiden yeniye|en yeni", t)) for t, _ in degerler) >= 2:
        ata(k, "siralama", [t for t, _ in degerler], yontem)
    else:
        if baslik not in k["filtreler"]:
            k["filtreler"][baslik] = [t for t, _ in degerler]
            k["yontem"].setdefault("filtreler", yontem)


KART = (r"product[-_]?(item|card|box|tile|grid-item|list-item|wrapper|container)\b|productcard|product-list-item|"
        r"prd-item|urun-kart|item-product|grid-product|card-product|productItem|product-miniature|ProductCard")
AD_SINIF = r"(product|item|prd|urun|card)[-_]*(name|title|ad)\b|\bname\b|\btitle\b"
SEO_SINIF = (r"seo|category[-_]?(desc|text|content|info|bottom|footer)|collection[-_]*(desc|content|text)|list__footer-content|"
             r"kategori[-_]?(aciklama|metin|icerik|yazi)|aciklama|description|\brte\b|cms-?content|bottom[-_]?(content|text|desc)|"
             r"catalog[-_]?desc|text-?content|content-?text|category-?about|listing-?(text|content)")


def _footer_mu(d):
    for a in [d] + list(d.atalar()):
        if a.etiket in ("footer", "header", "nav") or re.search(r"(^|\s)(site-|page-|main-)?footer(\s|$)|(^|\s)header(\s|$)", a.sinif(), re.I):
            return True
    return False


def _kelime(d):
    return sum(len(e.metin().split()) for e in d.bul(("p", "h2", "h3", "h4", "li")) if not e.ilk(("p", "li")))


def seo_metni(kok):
    adaylar = []
    for d in kok.bul(sinif=SEO_SINIF):
        if _footer_mu(d) or d.ilk(sinif=KART) is not None:
            continue
        w = _kelime(d)
        if w >= 80:
            adaylar.append((w, d, "html:" + (d.sinif() or d.kimlik())[:40]))
    if not adaylar:
        for d in kok.bul(("div", "section", "article")):
            if _footer_mu(d) or d.ilk(sinif=KART) is not None:
                continue
            w = sum(len(p.metin().split()) for p in d.bul("p"))
            if w >= 150:
                adaylar.append((w, d, "html:en-uzun-metin-blogu"))
    if not adaylar:
        return None, None
    enbuyuk = max(w for w, _, _ in adaylar)
    # tüm metni taşıyan en dar kapsayıcı: kelimelerin %85'ini tutan en derin aday
    uygun = [(len(list(d.atalar())), w, d, y) for w, d, y in adaylar if w >= 0.85 * enbuyuk]
    _, w, d, y = max(uygun, key=lambda x: x[0])
    return d, y


SAYI_DESEN = [r"(\d{1,3}(?:[.,]\d{3})+|\d+)\s+(?:adet\s+)?ürün\s+(?:bulundu|listeleniyor|listelendi|görüntüleniyor|var|mevcut)",
              r"(\d{1,3}(?:[.,]\d{3})+|\d+)\s+üründen", r"(\d{1,3}(?:[.,]\d{3})+|\d+)\s+ürünün\s+\d+", r"toplam\s+(\d{1,3}(?:[.,]\d{3})+|\d+)\s+ürün",
              r"(\d{1,3}(?:[.,]\d{3})+|\d+)\s+sonuç", r"\((\d{1,3}(?:[.,]\d{3})+|\d+)\s+ürün\)",
              r"(\d{1,3}(?:[.,]\d{3})+|\d+)\s+(?:products|items|results)\b", r"(\d{1,3}(?:[.,]\d{3})+|\d+)\s+ürün\b(?![eüa])"]


def html_sezgisel(h, k, kok, taban, sayfa_url):
    """Platformdan bağımsız okuma. Yalnız boş alanları doldurur; JSON adaptörünün kesin alanlarına dokunmaz."""
    # filtreler
    if "filtreler" not in k.get("_kesin", ()):
        for b, deg in filtre_gruplari(kok):
            _grup_esle(k, b, deg, taban, "html:filtre-blogu")
    # ürün kartları
    if not k.get("ornek_urunler"):
        adlar = []
        for kart in kok.bul(sinif=KART):
            if kart.ust is not None and any(re.search(KART, a.sinif(), re.I) for a in list(kart.atalar())[:3]):
                continue
            ad = next((e.metin() for e in kart.bul(sinif=AD_SINIF) if 3 < len(e.metin()) < 150), None)
            if not ad:
                img = kart.ilk("img")
                ad = img is not None and img.nit.get("alt")
            mk = kart.ilk(sinif=r"brand|marka")
            if ad and ad not in adlar:
                adlar.append(((mk.metin() + " · ") if mk is not None and mk.metin() and mk.metin() not in ad else "") + ad)
        ata(k, "ornek_urunler", adlar[:12], "html:urun-karti")
    # ürün sayısı (sayfada görünen)
    govde = kok.ilk("body") or kok
    metin = govde.metin()
    for d in SAYI_DESEN:
        m = re.search(d, metin, re.I)
        if m and int(re.sub(r"\D", "", m.group(1)) or 0) > 0:
            n = int(re.sub(r"\D", "", m.group(1)))
            k["sayfada_gorunen_urun_sayisi"] = n
            ata(k, "urun_sayisi", n, "html:metin")
            break
    # SEO metni
    if "icerik_html" not in k.get("_kesin", ()) and not k.get("icerik_html"):
        d, y = seo_metni(kok)
        if d is not None:
            ata(k, "icerik_html", d.ic_html(), y)
    # sıralama
    if not k.get("siralama"):
        s = kok.ilk("select", nit={"name": r"sort|order|sirala"}) or kok.ilk(sinif=r"sort|sirala|sorter")
        if s is not None:
            sec = [o.metin() for o in s.bul(("option", "li", "a", "label")) if 1 < len(o.metin()) < 40]
            ata(k, "siralama", list(dict.fromkeys(sec))[:12], "html:siralama")
    # alt kategoriler: kategori menüsündeki ya da yolu bu sayfanın altında kalan linkler
    p = url_coz(sayfa_url) or {}
    yol = urlsplit(sayfa_url).path.rstrip("/")
    if not k.get("alt_kategoriler") and "alt_kategoriler" not in k.get("_kesin", ()):
        aday, gorulen = [], set()
        bolge = list(kok.bul(sinif=r"categor|kategori|sub-?cat|alt-?kat|side-?nav|sidebar|category-?list|subcategor"))
        for b in bolge:
            if _footer_mu(b):
                continue
            for a, u in b.linkler():
                pu = url_coz(mutlak(u, taban))
                if pu and ortak.liste_mi(pu) and not pu["q"] and pu["tip"] != "arama" and \
                        not ortak.ayni_adres(pu["url"], p.get("url")) and pu["url"] not in gorulen and a.strip() and \
                        not (yol and yol.startswith(urlsplit(pu["url"]).path.rstrip("/") + "/")):
                    gorulen.add(pu["url"]); aday.append((a.strip(), pu["url"]))
        if not aday and yol:
            for a, u in kok.linkler():
                mu = mutlak(u, taban)
                py = urlsplit(mu).path.rstrip("/")
                pu = url_coz(mu)
                if pu and py.startswith(yol + "/") and ortak.liste_mi(pu) and pu["url"] not in gorulen and a.strip():
                    gorulen.add(pu["url"]); aday.append((a.strip(), pu["url"]))
        ata(k, "alt_kategoriler", aday[:40], "html:kategori-menusu" if bolge else "html:alt-yol")
    if not k.get("markalar") and "markalar" not in k.get("_kesin", ()):
        mk = []
        for a, u in kok.linkler():
            pu = url_coz(mutlak(u, taban))
            if pu and pu["tip"].startswith("marka") and a.strip() and (a.strip(), pu["url"]) not in mk:
                mk.append((a.strip(), pu["url"]))
        ata(k, "markalar", mk[:60], "html:marka-linkleri")
    if not k.get("link_bulutu"):
        lb = []
        for b in kok.bul(sinif=r"(tag|link|seo)[-_]?cloud|populer|popular-?search|related-?search|ilgili-?arama|seo-?links|tag-?list"):
            lb += [(a.strip(), mutlak(u, taban)) for a, u in b.linkler() if a.strip()]
        ata(k, "link_bulutu", list(dict.fromkeys(lb))[:60], "html:link-bulutu")


# --- JSON tarama (Next.js / Nuxt / gömülü durum) ---------------------------------------------------

AD_ANAHTAR = ("name", "Name", "title", "Title", "productName", "ProductName", "displayName", "DisplayName", "label", "Label")
DEGER_ANAHTAR = ("values", "Values", "attributes", "Attributes", "options", "Options", "items", "Items", "choices",
                 "facetValues", "buckets", "terms", "children", "Children", "data")
SAYI_ANAHTAR = ("totalCount", "TotalCount", "total_count", "totalProductCount", "productCount", "ProductCount",
                "totalResults", "nbHits", "totalItems", "total_products", "productsCount", "products_count", "numberOfItems")
URL_ANAHTAR = ("url", "Url", "URL", "link", "Link", "href", "path", "slug", "SpecialLink", "absolute_url", "seoUrl")


def _ad(x):
    for a in AD_ANAHTAR:
        v = x.get(a)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _url(x):
    for a in URL_ANAHTAR:
        v = x.get(a)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def json_tara(veri, k, etiket, taban):
    bulgu = {"urun": [], "filtre": [], "sayi": [], "bc": [], "metin": []}

    def gez(o, anahtar, derinlik):
        if derinlik > 16:
            return
        if isinstance(o, dict):
            for a, v in o.items():
                if a in SAYI_ANAHTAR and isinstance(v, (int, float)) and v > 0:
                    bulgu["sayi"].append((SAYI_ANAHTAR.index(a), int(v), a))
                if "breadcrumb" in a.lower() and isinstance(v, list):
                    bc = [(_ad(x), _url(x)) for x in v if isinstance(x, dict) and _ad(x)]
                    if bc:
                        bulgu["bc"].append(bc)
                if isinstance(v, str) and len(v) > 300 and re.search(r"<p\b|</h[23]>", v) and \
                        re.search(r"content|desc|seo|text|html|body|aciklama|icerik", a, re.I):
                    bulgu["metin"].append((len(v), a, v))
                gez(v, a, derinlik + 1)
        elif isinstance(o, list) and o:
            sozluk = [x for x in o[:200] if isinstance(x, dict)]
            if len(sozluk) >= 3 and len(sozluk) >= 0.8 * min(len(o), 200):
                adli = [x for x in sozluk if _ad(x)]
                fiyatli = [x for x in sozluk if any(re.search(r"price|fiyat|amount", kk, re.I) for kk in x)]
                if len(adli) >= 0.6 * len(sozluk) and len(fiyatli) >= 0.5 * len(sozluk):
                    bulgu["urun"].append((anahtar, sozluk))
            if len(sozluk) >= 2:
                grup = []
                for x in sozluk:
                    ad = _ad(x)
                    vals = next((x[d] for d in DEGER_ANAHTAR if isinstance(x.get(d), list) and x[d]
                                 and isinstance(x[d][0], dict) and _ad(x[d][0])), None)
                    if ad and vals and not any(re.search(r"price|fiyat", kk, re.I) for kk in x if kk not in ("name", "Name")):
                        grup.append((ad, [(_ad(v), _url(v), v.get("quantity") or v.get("Quantity") or v.get("count") or v.get("Count")) for v in vals if _ad(v)]))
                if len(grup) >= 2:
                    bulgu["filtre"].append(grup)
            for x in o[:200]:
                gez(x, anahtar, derinlik + 1)
    gez(veri, "", 0)
    if bulgu["urun"]:
        _, liste = max(bulgu["urun"], key=lambda x: len(x[1]))

        def marka(x):
            b = x.get("brand") or x.get("Brand") or x.get("vendor") or x.get("manufacturer")
            return (b.get("name") or b.get("Name")) if isinstance(b, dict) else (b if isinstance(b, str) else "")
        ata(k, "ornek_urunler", [(f"{marka(x)} · " if marka(x) else "") + _ad(x) for x in liste if _ad(x)][:12], etiket + ":urun-listesi")
    if bulgu["sayi"]:
        oncelik, n, a = min(bulgu["sayi"])
        ata(k, "urun_sayisi", n, f"{etiket}:{a}")
    if bulgu["bc"]:
        ata(k, "breadcrumb", [(a, mutlak(u, taban) if u else None) for a, u in max(bulgu["bc"], key=len)], etiket + ":breadcrumb")
    if bulgu["filtre"]:
        grup = max(bulgu["filtre"], key=len)
        for ad, vals in grup:
            _grup_esle(k, ad, [(t, u) for t, u, _ in vals], taban, etiket + ":filtre")
    if bulgu["metin"]:
        _, a, v = max(bulgu["metin"])
        ata(k, "icerik_html", v, f"{etiket}:{a}")
    return bool(bulgu["urun"] or bulgu["filtre"])


def devalue_coz(dizi):
    """Nuxt 3 __NUXT_DATA__ (devalue) dizisini nesneye çevirir."""
    bellek = {}

    def c(i, yol=()):
        if not isinstance(i, int) or i < 0 or i >= len(dizi):
            return i
        if i in bellek:
            return bellek[i]
        if i in yol:
            return None
        v = dizi[i]
        if isinstance(v, list):
            if v and isinstance(v[0], str) and v[0] in ("Reactive", "ShallowReactive", "Ref", "ShallowRef", "EmptyRef", "NuxtError"):
                r = c(v[1], yol + (i,)) if len(v) > 1 else None
            elif v and isinstance(v[0], str) and v[0] in ("Set", "Map", "Date", "Object", "BigInt", "RegExp", "null"):
                r = [c(x, yol + (i,)) for x in v[1:]]
            else:
                r = [c(x, yol + (i,)) for x in v]
        elif isinstance(v, dict):
            r = {kk: c(x, yol + (i,)) for kk, x in v.items()}
        else:
            r = v
        bellek[i] = r
        return r
    return c(0)


# --- platform adaptörleri --------------------------------------------------------------------------

def boyner_nextjs(nd, k, taban):
    """Boyner (örnek adaptör): __NEXT_DATA__ props.pageProps.initialState yapısı."""
    try:
        st = nd["props"]["pageProps"]["initialState"]
        rp = st["filters"]["resolvedPage"] or {}
    except (KeyError, TypeError):
        return False
    site = ortak.site()
    k["_kesin"] = {"title", "description", "h1", "canonical", "index", "icerik_html", "breadcrumb", "urun_sayisi",
                   "ornek_urunler", "alt_kategoriler", "markalar", "filtreler", "fiyat_filtresi", "siralama", "link_bulutu"}
    k.update({"sayfa_tipi": rp.get("PageType"), "durum": rp.get("StatusCode") or k.get("durum"),
              "yonlendirme": rp.get("RedirectUrl"), "title": rp.get("Title"), "description": rp.get("Description"),
              "h1": rp.get("H1"), "canonical": rp.get("CanonicalUrl"), "index": rp.get("MetaRobots"),
              "icerik_html": rp.get("Content") or ""})
    for a in ("title", "description", "h1", "canonical", "index", "icerik_html"):
        k["yontem"][a] = "nextjs-boyner:resolvedPage"
    for anahtar, v in (st.get("dsListingSearchService", {}).get("queries") or {}).items():
        d = v.get("data") or {}
        if anahtar.startswith("getProducts"):
            k["breadcrumb"] = [(b["Title"], site + b["Url"]) for b in d.get("Breadcrumbs") or []]
            k["urun_sayisi"] = d.get("TotalCount")
            urun = d.get("Products") or []
            k["ornek_urunler"] = [f"{u.get('Brand')} · {u.get('Title')}" for u in urun[:12]]
            for a in ("breadcrumb", "urun_sayisi", "ornek_urunler"):
                k["yontem"][a] = "nextjs-boyner:getProducts"
        elif anahtar.startswith("getFilters"):
            k["urun_sayisi"] = k.get("urun_sayisi") or d.get("TotalCount")
            k["filtreler"] = {}
            for f in d.get("Filters") or []:
                deger = [(a.get("DisplayName"), a.get("SpecialLink")) for a in f.get("Attributes") or []]
                if f["Name"] == "categories":
                    k["alt_kategoriler"] = [(ad, site + l) for ad, l in deger if l]
                elif f["Name"] == "marka":
                    k["markalar"] = [(ad, site + l) for ad, l in deger if l]
                elif f["Name"] == "cinsiyet":
                    k["cinsiyetler"] = [ad for ad, _ in deger]
                elif f["Name"] == "priceFilter":
                    k["fiyat_filtresi"] = True          # içerikte "fiyat aralığı filtresi" yalnız bu True ise anılır
                elif f["Name"] == "trueFalseFilter":
                    k["secenek_filtreleri"] = [ad for ad, _ in deger]      # Kargo Bedava, Yarın Kargoda...
                elif f["Name"] not in ATLA_BOYNER:
                    k["filtreler"][f.get("DisplayName")] = [ad for ad, _ in deger
                                                            if (ad or "").strip().lower() not in KIRLI][:40]
            k["hizli_filtreler"] = [a.get("DisplayName") for a in d.get("FastFilterAttributes") or []]
            k["siralama"] = [o.get("DisplayName") or o.get("Name") for o in d.get("OrderOptions") or [] if isinstance(o, dict)]
            for a in ("filtreler", "alt_kategoriler", "markalar", "fiyat_filtresi", "siralama"):
                k["yontem"][a] = "nextjs-boyner:getFilters"
    for anahtar, v in (st.get("dsSharedService", {}).get("queries") or {}).items():
        if anahtar.startswith("getCloudLinking") and v.get("data"):
            k["link_bulutu"] = [(c["Title"], site + c["Link"]) for grup in v["data"] for c in grup.get("CloudLinking") or []]
            k["yontem"]["link_bulutu"] = "nextjs-boyner:getCloudLinking"
    return True


def nextjs(h, k, taban):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    if not m:
        return False
    try:
        nd = json.loads(m.group(1))
    except Exception:
        return False
    if boyner_nextjs(nd, k, taban):
        k["platform_adaptoru"] = "nextjs-boyner"
        return True
    k["platform_adaptoru"] = "nextjs"
    return json_tara(nd.get("props") or nd, k, "nextjs", taban)


def nuxt(h, k, taban):
    m = re.search(r'<script[^>]+id="__NUXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    veri = None
    if m:
        try:
            veri = devalue_coz(json.loads(m.group(1)))
        except Exception:
            veri = None
    if veri is None:
        m = re.search(r"window\.__NUXT__\s*=\s*(\{.*?\})\s*;?\s*</script>", h, re.S)
        if m:
            try:
                veri = json.loads(m.group(1))
            except Exception:
                k["uyarilar"].append("window.__NUXT__ bir JavaScript fonksiyonu; JSON olarak okunamadı (--pw ile render edilebilir)")
    if veri is None:
        return False
    k["platform_adaptoru"] = "nuxt"
    return json_tara(veri, k, "nuxt", taban)


ETIKET_HARIC = re.compile(r"^(feed-|yuzde_|tum_urunler|\d+$|[a-z_]+_[a-z_]+$)|_|^\W|\W$|^[a-z0-9]{10,}$|^[A-Z0-9]{2,4}$")


def shopify(k, tam, taban):
    m = re.search(r"/collections/([^/?#]+)", urlsplit(tam).path)
    if not m:
        return False
    origin = "{0.scheme}://{0.netloc}".format(urlsplit(tam))
    tutamac = m.group(1)
    c = getir_json(f"{origin}/collections/{tutamac}.json")
    if not c or "collection" not in c:
        k["uyarilar"].append("Shopify koleksiyon JSON'u okunamadı")
        return False
    col = c["collection"]
    k["platform_adaptoru"] = "shopify"
    ata(k, "urun_sayisi", col.get("products_count"), "shopify-json:products_count")
    if col.get("body_html") and len(metne(col["body_html"]).split()) >= 40:
        k["shopify_aciklama_html"] = col["body_html"]
    urunler = []
    for sayfa in (1, 2):
        pj = getir_json(f"{origin}/collections/{tutamac}/products.json?limit=250&page={sayfa}")
        part = (pj or {}).get("products") or []
        urunler += part
        if len(part) < 250:
            break
    if not urunler:
        return True
    tip = Counter((u.get("product_type") or "").split(">")[-1].strip() for u in urunler if u.get("product_type"))
    satici = Counter(u.get("vendor") for u in urunler if u.get("vendor"))
    etiket = Counter(t.strip().strip('"[]') for u in urunler for t in (u.get("tags") or []) if not ETIKET_HARIC.search(t.strip()))
    secenek = {}
    for u in urunler:
        for o in u.get("options") or []:
            if o.get("name") and o["name"].lower() not in ("title", "başlık"):
                secenek.setdefault(o["name"], Counter()).update(o.get("values") or [])
    ata(k, "ornek_urunler", [f"{u.get('vendor')} · {u.get('title')}" for u in urunler[:12]], "shopify-json:products")
    ata(k, "markalar", [(v, f"{origin}/collections/vendors?q={quote(v)}") for v, _ in satici.most_common(40)], "shopify-json:vendor")
    k["gam_json"] = {"ornek_sayisi": len(urunler), "urun_tipi": tip.most_common(25), "etiket": etiket.most_common(30),
                     "secenek": {a: c_.most_common(20) for a, c_ in secenek.items()}}
    k["yontem"]["gam_json"] = f"shopify-json:products ({len(urunler)} ürün örneği)"
    return True


def akinon(k, tam, taban):
    ayrac = "&" if "?" in tam else "?"
    j = getir_json(tam + ayrac + "format=json")
    if not isinstance(j, dict) or "facets" not in j:
        k["uyarilar"].append("Akinon ?format=json ucu yanıt vermedi; HTML okundu")
        return False
    k["platform_adaptoru"] = "akinon"
    k["_kesin"] = {"filtreler", "alt_kategoriler", "markalar", "siralama", "fiyat_filtresi"}
    tc = (j.get("pagination") or {}).get("total_count")
    ata(k, "urun_sayisi", tc, "akinon-json:pagination.total_count")

    def temiz(u):
        if not u:
            return None
        p = urlsplit(mutlak(u, taban))
        q = [(a, b) for a, b in parse_qsl(p.query) if a != "format"]
        return f"{p.scheme}://{p.netloc}{p.path}" + ("?" + urlencode(q) if q else "")
    for f in j.get("facets") or []:
        ad = f.get("name") or f.get("key")
        sec = ((f.get("data") or {}).get("choices")) or []
        degerler = [(c.get("label"), temiz(c.get("url"))) for c in sec if c.get("label") and not c.get("is_selected")]
        key = (f.get("key") or "") + " " + (f.get("widget_type") or "")
        if re.search(r"in_stock|stock|stok", key):
            continue
        if re.search(r"categor", key):
            # kategori ağacı: seçili kategorinin altındaki daha derin seçenekler alt kategori, aynı derinliktekiler kardeş
            secili = next((i for i, c in enumerate(sec) if c.get("is_selected")), None)
            alt, kardes = [], []
            if secili is not None:
                d0 = sec[secili].get("depth") or 0
                for c in sec[secili + 1:]:
                    if (c.get("depth") or 0) <= d0:
                        break
                    alt.append((c.get("label"), temiz(c.get("url"))))
                kardes = [(c.get("label"), temiz(c.get("url"))) for c in sec
                          if (c.get("depth") or 0) == d0 and not c.get("is_selected") and not c.get("is_parent_of_selection")]
            else:
                alt = [(t, u) for t, u in degerler if u]
            k["alt_kategoriler"] = [(t, u) for t, u in alt if u]
            k["kardes_kategoriler"] = [(t, u) for t, u in kardes if u]
            k["yontem"]["alt_kategoriler"] = k["yontem"]["kardes_kategoriler"] = "akinon-json:facets (depth)"
        elif re.search(r"brand|marka", key + " " + duz(ad)):
            k["markalar"] = degerler; k["yontem"]["markalar"] = "akinon-json:facets"
        elif re.search(r"price|fiyat", key + " " + duz(ad)):
            k["fiyat_filtresi"] = True; k["yontem"]["fiyat_filtresi"] = "akinon-json:facets"
        else:
            k["filtreler"][ad] = [t for t, _ in degerler if (t or "").strip().lower() not in KIRLI][:40]
            k["yontem"]["filtreler"] = "akinon-json:facets"
    k["siralama"] = [s.get("label") for s in j.get("sorters") or [] if s.get("label")]
    k["yontem"]["siralama"] = "akinon-json:sorters"
    ata(k, "ornek_urunler", list(dict.fromkeys(p.get("name") for p in j.get("products") or [] if p.get("name")))[:12],
        "akinon-json:products")
    return True


def vtex(k, tam, taban):
    p = urlsplit(tam)
    origin = f"{p.scheme}://{p.netloc}"
    seg = [s for s in p.path.split("/") if s]
    if not seg:
        return False
    harita = ",".join(["c"] * len(seg))
    r = istek(f"{origin}/api/catalog_system/pub/products/search{p.path}?map={harita}&_from=0&_to=11", 40,
              ("Accept: application/json",))
    try:
        urunler = json.loads(r["govde"])
    except Exception:
        urunler = None
    if not isinstance(urunler, list):
        k["uyarilar"].append("VTEX katalog API yanıt vermedi; HTML okundu")
        return False
    k["platform_adaptoru"] = "vtex"
    toplam = re.search(r"/(\d+)$", r["basliklar"].get("resources") or "")
    ata(k, "urun_sayisi", toplam and int(toplam.group(1)), "vtex-api:resources")
    ata(k, "ornek_urunler", [f"{u.get('brand')} · {u.get('productName')}" for u in urunler[:12]], "vtex-api:products")
    f = getir_json(f"{origin}/api/catalog_system/pub/facets/search{p.path}?map={harita}")
    if isinstance(f, dict):
        ata(k, "markalar", [(b.get("Name"), mutlak(b.get("Link"), taban)) for b in f.get("Brands") or []], "vtex-api:facets")
        agac = (f.get("CategoriesTrees") or [{}])[0].get("Children") or []
        ata(k, "alt_kategoriler", [(c.get("Name"), mutlak(c.get("Link"), taban)) for c in agac], "vtex-api:facets")
        for ad, vals in (f.get("SpecificationFilters") or {}).items():
            k["filtreler"][ad] = [v.get("Name") for v in vals][:40]
        if f.get("PriceRanges"):
            ata(k, "fiyat_filtresi", True, "vtex-api:facets")
    return True


# --- ana okuma -------------------------------------------------------------------------------------

def pw_render(url):
    """Yerel Playwright ile render edilmiş HTML ve gömülü durum JSON'u (bağlama token yazmaz)."""
    fd, yol = tempfile.mkstemp(suffix=".json"); os.close(fd)
    try:
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pw_oku.py"), url,
                        "--liste", "--cikti", yol], capture_output=True, text=True, timeout=200)
        return json.load(open(yol, encoding="utf-8"))
    except Exception as e:
        return {"hata": str(e)[:150]}
    finally:
        os.unlink(yol)


def oku(url, pw=False):
    p = url_coz(url)
    tam = p["url"] if p else url
    k = bos_kayit(tam)
    k["tip"] = p and p["tip"]
    r = istek(tam)
    h = r["govde"]
    k["durum"] = r["kod"]
    if not ortak.ayni_adres(r["son_url"], tam):
        k["yonlendirme"] = r["son_url"]
    if ortak.cloudflare_mi(h) or not h:
        k["hata"] = "sayfa okunamadı (Cloudflare doğrulaması ya da boş yanıt)"
        if not pw:
            return _son(k, p)
        rr = pw_render(tam)
        if rr.get("hata") or not rr.get("html"):
            return _son(k, p)
        h = rr["html"]; k.pop("hata", None); k["yontem"]["okuma"] = "playwright"
    taban = r["son_url"] or tam
    k["platform"] = platform_tespit(h)
    x_robots = r["basliklar"].get("x-robots-tag")
    if x_robots:
        k["meta_robots"] = x_robots
    plat = k["platform"]
    tamam = False
    if "nextjs" in plat:
        tamam = nextjs(h, k, taban)
    if not tamam and "nuxt" in plat:
        tamam = nuxt(h, k, taban)
    if "shopify" in plat:
        tamam = shopify(k, tam, taban) or tamam
    if not tamam and "akinon" in plat:
        tamam = akinon(k, tam, taban)
    if not tamam and "vtex" in plat:
        tamam = vtex(k, tam, taban)
    kok = dom.ayristir(h)
    html_temel(h, k, kok, taban)
    html_sezgisel(h, k, kok, taban, tam)
    if k.get("shopify_aciklama_html") and len(metne(k["shopify_aciklama_html"]).split()) > len(metne(k["icerik_html"]).split()):
        k["icerik_html"] = k.pop("shopify_aciklama_html"); k["yontem"]["icerik_html"] = "shopify-json:body_html"
    if pw and any(k.get(a) in (None, "", [], {}) for a in ("filtreler", "ornek_urunler", "icerik_html", "urun_sayisi")):
        rr = pw_render(tam)
        if rr.get("html"):
            kok2 = dom.ayristir(rr["html"])
            if rr.get("durum"):
                try:
                    json_tara(json.loads(rr["durum"]), k, "playwright-durum", taban)
                except Exception:
                    pass
            html_temel(rr["html"], k, kok2, taban)
            html_sezgisel(rr["html"], k, kok2, taban, tam)
            k["yontem"]["okuma"] = "playwright (render edilmiş DOM)"
    return _son(k, p)


def _son(k, p):
    if k.get("canonical") is not None or not k.get("hata"):
        can = k.get("canonical")
        k["canonical_kendisi"] = (not can) or ortak.ayni_adres(can.split("?")[0], k["url"].split("?")[0])
    if k.get("index") is None and not k.get("hata"):
        k["index"] = "noindex" not in (k.get("meta_robots") or "").lower()
        k["yontem"].setdefault("index", "html:meta-robots" if k.get("meta_robots") else "varsayılan (meta robots yok)")
    k["icerik"] = icerik_analizi(k.get("icerik_html"))
    if p and p.get("g"):
        k["cinsiyet"] = ortak.cinsiyet_etiketi(p["g"])
    k.pop("_kesin", None)
    k["bos_alanlar"] = [a for a in ("h1", "breadcrumb", "urun_sayisi", "ornek_urunler", "alt_kategoriler", "markalar",
                                    "filtreler", "icerik_html") if k.get(a) in (None, "", [], {})]
    return k


def gam(k, n=12):
    """Ürün gamı özeti: en çok ürünü olan kırılımları (marka sayfasında alt kategoriler, kategori sayfasında
    markalar) tek tek okuyup ürün sayısını ve örnek ürün adlarını toplar. İçerik mevcut gamı anlatır;
    gamda ağırlığı olan öne alınır. İstekler arasında beklenir (ortak.istek en az 1,2 sn)."""
    marka_sayfasi = (k.get("tip") or "").startswith("marka") or k.get("sayfa_tipi") == "Brand"
    liste = (k.get("alt_kategoriler") if marka_sayfasi else k.get("markalar")) or k.get("alt_kategoriler") or []
    out = []
    for ad, u in [x for x in liste if x[1]][:n]:
        c = oku(u)
        if c.get("hata"):
            out.append({"ad": ad, "url": u, "hata": c["hata"]}); continue
        out.append({"ad": ad, "url": u, "urun": c.get("urun_sayisi"), "index": c.get("index"),
                    "canonical_kendisi": c.get("canonical_kendisi"), "ornek": c.get("ornek_urunler")})
    return sorted(out, key=lambda x: -(x.get("urun") or 0))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ortak.arguman_ekle(ap)
    ap.add_argument("url")
    ap.add_argument("--gam", type=int, nargs="?", const=12, default=0,
                    help="ilk N kırılımın (marka ya da alt kategori) ürün sayısını ve örnek ürünlerini topla (yavaş)")
    ap.add_argument("--cikti")
    ap.add_argument("--icerik", action="store_true")
    ap.add_argument("--pw", action="store_true", help="alanlar boş kalırsa yerel Playwright ile render edip yeniden oku")
    a = ap.parse_args()
    if not a.marka and not a.domain:
        a.domain = urlsplit(a.url).netloc
    ortak.ayar_args(a)
    k = oku(a.url, a.pw)
    if a.gam and not k.get("hata"):
        k["gam"] = gam(k, a.gam)
    if a.cikti:
        json.dump(k, open(a.cikti, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if k.get("hata"):
        sys.exit(k["hata"])
    if a.icerik:
        print(k["icerik"]["metin"] or "(sayfada içerik yok)"); return
    i = k["icerik"]
    y = k["yontem"]
    print(f"URL        : {k['url']}")
    print(f"Platform   : {', '.join(k['platform']) or '-'} · adaptör: {k.get('platform_adaptoru') or 'HTML sezgisel'}")
    print(f"Tip/durum  : {k.get('tip')} · {k['sayfa_tipi'] or '-'} · HTTP {k['durum']} · index={k['index']} · ürün: {k.get('urun_sayisi')}"
          f"  [{y.get('urun_sayisi', '-')}]" + (f" · sayfada görünen: {k['sayfada_gorunen_urun_sayisi']}" if k.get("sayfada_gorunen_urun_sayisi") not in (None, k.get("urun_sayisi")) else ""))
    if k.get("yonlendirme"):
        print(f"Yönlendirme: {k['yonlendirme']}")
    print(f"Canonical  : {k['canonical'] or '(yok)'}" + ("" if k["canonical_kendisi"] else "   <-- BAŞKA SAYFAYA İŞARET EDİYOR"))
    print(f"H1         : {k['h1']}\nTitle      : {k['title']}  | html: {k['html_title']}\nDescription: {k['description']}")
    print("Breadcrumb : " + " > ".join(b for b, _ in k.get("breadcrumb", [])) + f"  [{y.get('breadcrumb', '-')}]")
    print(f"İçerik     : {i['kelime']} kelime · {len(i['basliklar'])} başlık ({', '.join(sorted({t for t, _ in i['basliklar']})) or '-'})"
          f" · {len(i['linkler'])} link · liste {i['liste']} · tablo {i['tablo']} · soru başlık {i['soru_baslik']} · SSS {'var' if i['sss'] else 'yok'}"
          f" · hitap siz {i['siz']} / sen {i['sen']}  [{y.get('icerik_html', '-')}]")
    for t, b in i["basliklar"][:30]:
        print(f"   {t}: {b}")
    for a_, u in i["linkler"][:20]:
        print(f"   link: {a_} -> {u}")
    print(f"Fiyat filtresi: {'var' if k.get('fiyat_filtresi') else 'yok/bulunamadı'} · seçenek filtreleri: {', '.join(k.get('secenek_filtreleri') or []) or '-'}"
          f" · sıralama: {', '.join(x for x in (k.get('siralama') or []) if x) or '-'}")
    for x in k.get("gam") or []:
        print(f"Gam · {x['ad']}: {x.get('urun')} ürün · " + " | ".join((x.get('ornek') or [])[:4]))
    print("Örnek ürünler: " + " | ".join(k.get("ornek_urunler", [])[:6]) + f"  [{y.get('ornek_urunler', '-')}]")
    print("Alt kategoriler: " + ", ".join(ad for ad, _ in k.get("alt_kategoriler", [])) + f"  [{y.get('alt_kategoriler', '-')}]")
    if k.get("kardes_kategoriler"):
        print("Kardeş kategoriler: " + ", ".join(ad for ad, _ in k["kardes_kategoriler"]) + f"  [{y.get('kardes_kategoriler', '-')}]")
    print("Markalar (ilk 25): " + ", ".join(ad for ad, _ in k.get("markalar", [])[:25]) + f"  (toplam {len(k.get('markalar', []))})  [{y.get('markalar', '-')}]")
    for ad, deger in (k.get("filtreler") or {}).items():
        print(f"Filtre · {ad}: " + ", ".join(deger[:18]))
    if k.get("filtreler"):
        print(f"   [filtreler: {y.get('filtreler')}]")
    gj = k.get("gam_json")
    if gj:
        print(f"Ürün verisi ({gj['ornek_sayisi']} ürün): tip " + ", ".join(f"{a} ({n})" for a, n in gj["urun_tipi"][:10]))
        print("   etiket: " + ", ".join(f"{a} ({n})" for a, n in gj["etiket"][:15]))
        for a_, deg in gj["secenek"].items():
            print(f"   seçenek · {a_}: " + ", ".join(f"{d} ({n})" for d, n in deg[:12]))
    if k.get("link_bulutu"):
        print("Link bulutu: " + ", ".join(t for t, _ in k["link_bulutu"][:30]))
    for u in k.get("uyarilar") or []:
        print("UYARI:", u)
    if k["bos_alanlar"]:
        print("Boş kalan alanlar (bulunamadı, uydurulmaz): " + ", ".join(k["bos_alanlar"])
              + ("" if a.pw else "  -> gerekirse --pw ile render edilerek yeniden okunur"))


if __name__ == "__main__":
    main()
