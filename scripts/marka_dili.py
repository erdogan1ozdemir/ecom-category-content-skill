#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Marka dili profili için örnek metin toplar ve ölçer (Faz 0). Profili bu betik YAZMAZ: model çıktıyı okuyup
`markalar/{slug}/profil.md` taslağını kurar, ekibe doğrulatır.

Öncelik sırası (kullanıcı kararı): (a) markanın mevcut kategori sayfası metinleri, (b) ürün açıklamaları,
(c) blog. Envanterden N kategori sayfası (mevcut SEO metni olanlar), N ürün sayfası, N blog yazısı okunur.

Ölçülenler (kaynak türüne göre ayrı ve toplu):
  hitap      siz / sen / biz sayımı (fiil ekleri ve zamirler; yaklaşık)
  cümle      ortalama cümle ve paragraf uzunluğu, ünlem ve emoji yoğunluğu (1.000 kelimede)
  kip        "-mektedir / -maktadır" ve geniş zaman payı; birinci çoğul
  terim      İngilizce görünümlü kelime oranı ve en sık örnekler (elle bakılır)
  kalıp      "kategori", "ürün grubu", "parça" kullanımı; tipik CTA'lar; sık iki-üç kelimelik kalıplar,
             sık cümle açılışları; marka adının yazım biçimleri (VitrA / Vitra gibi)
  örnek      her kaynaktan ilk paragraflar (ton için okunur)
Metin yoksa ya da yetersizse (ör. kategori metni olmayan site) çıktıda "yeterli": false ve nedeni yazılır;
o durumda profil rakiplerin dilinden türetilir (bkz. references/marka-profili.md).

Kullanım:
    python3 marka_dili.py --marka flormar --cikti $T/dil.json
    python3 marka_dili.py --domain derimod.com.tr --kategori 8 --urun 6 --blog 4 --tara 25
"""
import argparse, html, json, os, re, statistics, sys
from collections import Counter
from urllib.parse import urlsplit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, dom, envanter, sayfa
from ortak import duz

SIZ = re.compile(r"\b\w+(?:abilirsiniz|ebilirsiniz|malısınız|melisiniz|ıyorsunuz|iyorsunuz|uyorsunuz|üyorsunuz|"
                 r"acaksınız|eceksiniz|ınız|iniz|unuz|ünüz)\b|\b(?:siz|sizi|sizin|size|sizde|sizden|sizler)\b", re.I)
SEN = re.compile(r"\b\w+(?:abilirsin|ebilirsin|malısın|melisin|ıyorsun|iyorsun|uyorsun|üyorsun|acaksın|eceksin)\b|"
                 r"\b(?:sen|seni|senin|sana|sende|senden)\b", re.I)
BIZ = re.compile(r"\b\w+(?:ıyoruz|iyoruz|uyoruz|üyoruz|acağız|eceğiz|abiliriz|ebiliriz)\b|\b(?:biz|bizi|bizim|bize|bizden)\b", re.I)
MEKTEDIR = re.compile(r"\b\w+(?:mektedir|maktadır|mektedirler|maktadırlar)\b", re.I)
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")
CTA = re.compile(r"(?i)\bhemen\b|keşfet\w*|incele\w*|göz at\w*|satın al\w*|sepete ekle\w*|alışverişe başla\w*|"
                 r"kaçırma\w*|tıkla\w*|sipariş ver\w*|fırsatı yakala\w*|stoklarla sınırlı|sizi bekliyor|seni bekliyor")
INGILIZCE = {"the", "and", "for", "with", "new", "collection", "look", "style", "skin", "care", "matte", "glow", "lip",
             "eye", "face", "nail", "color", "colour", "fit", "slim", "regular", "oversize", "basic", "premium", "sale",
             "outlet", "denim", "jeans", "shirt", "t-shirt", "sneaker", "sneakers", "boots", "bag", "home", "kids",
             "baby", "sport", "active", "outdoor", "smart", "casual", "classic", "limited", "edition", "best", "seller",
             "online", "shop", "trend", "trendy", "must", "have", "makeup", "make", "up", "primer", "highlighter",
             "contour", "concealer", "foundation", "mascara", "liner", "blush", "bronzer", "serum", "cream", "gel",
             "tone", "nude", "pink", "black", "white", "gold", "silver", "wireless", "bluetooth", "smartphone"}
DURAK = set("ve ile bir bu da de için olarak gibi en çok daha her ya veya ki ne mi mı mu mü olan olur ise "
            "kadar sonra önce ancak hem sizin size sen sana senin biz bizim o onu onun şu tüm bütün".split())


def cumleler(metin):
    return [c.strip() for c in re.split(r"(?<=[.!?])\s+", metin) if len(c.split()) >= 3]


def olc(metin):
    kelime = metin.split()
    n = max(1, len(kelime))
    cum = cumleler(metin)
    kucuk = [duz(w) for w in kelime]
    ing = [w for w, d in zip(kelime, kucuk) if d in INGILIZCE or (re.search(r"[qwx]", d) and len(d) > 2)]
    return {"kelime": len(kelime), "cumle": len(cum),
            "ort_cumle_kelime": round(statistics.mean([len(c.split()) for c in cum]), 1) if cum else None,
            "siz": len(SIZ.findall(metin)), "sen": len(SEN.findall(metin)), "biz": len(BIZ.findall(metin)),
            "mektedir": len(MEKTEDIR.findall(metin)),
            "unlem_1000": round(metin.count("!") / n * 1000, 1), "emoji": len(EMOJI.findall(metin)),
            "ingilizce_oran": round(len(ing) / n * 100, 1), "ingilizce_ornek": Counter(w.strip(".,;:!?()").lower() for w in ing).most_common(15),
            "kategori_kelimesi": len(re.findall(r"(?i)\bkategori\w*", metin)),
            "urun_grubu": len(re.findall(r"(?i)ürün grub\w*", metin)), "parca": len(re.findall(r"(?i)\bparça\w*", metin)),
            "cta": Counter(m.group(0).lower() for m in CTA.finditer(metin)).most_common(10)}


def kaliplar(metinler):
    iki, uc, acilis = Counter(), Counter(), Counter()
    for m in metinler:
        for c in cumleler(m):
            t = [w.strip(".,;:!?()\"'“”").lower() for w in c.split()]
            if len(t) >= 2:
                acilis[" ".join(t[:2])] += 1
            for i in range(len(t) - 1):
                if t[i] not in DURAK and t[i + 1] not in DURAK and len(t[i]) > 2 and len(t[i + 1]) > 2:
                    iki[t[i] + " " + t[i + 1]] += 1
                if i < len(t) - 2 and t[i] not in DURAK and t[i + 2] not in DURAK:
                    uc[" ".join(t[i:i + 3])] += 1
    return {"iki_kelime": [x for x in iki.most_common(25) if x[1] >= 2],
            "uc_kelime": [x for x in uc.most_common(15) if x[1] >= 2],
            "cumle_acilisi": [x for x in acilis.most_common(12) if x[1] >= 2]}


def ilk_paragraflar(metin, n=2):
    par = [p.strip() for p in re.split(r"\n+", metin) if len(p.split()) >= 15]
    return [p[:600] for p in par[:n]]


def urun_aciklamasi(url):
    r = ortak.istek(url)
    h = r["govde"]
    if not h or ortak.cloudflare_mi(h):
        return None, "okunamadı"
    for x in sayfa.jsonld(h):
        if "Product" in sayfa._tip_ld(x) and isinstance(x.get("description"), str) and len(x["description"].split()) >= 15:
            return sayfa.metne(x["description"]), "json-ld:Product.description"
    kok = dom.ayristir(h)
    aday = []
    for d in kok.bul(sinif=r"description|aciklama|product-?detail|product-?info|urun-?detay|product__description|rte|tab-?content"):
        if sayfa._footer_mu(d):
            continue
        t = d.metin("\n")
        if len(t.split()) >= 15:
            aday.append((len(t.split()), t))
    if aday:
        return min(aday)[1] if len(aday) > 1 and min(aday)[0] >= 40 else max(aday)[1], "html:aciklama-blogu"
    m = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', h, re.I)
    return (html.unescape(m.group(1)), "meta description (yalnız kısa açıklama)") if m else (None, "açıklama bulunamadı")


def blog_metni(url):
    r = ortak.istek(url)
    h = r["govde"]
    if not h or ortak.cloudflare_mi(h):
        return None, "okunamadı"
    kok = dom.ayristir(h)
    art = kok.ilk("article") or kok.ilk(sinif=r"article|post-?content|blog-?content|entry-content|rte")
    if art is not None and len(art.metin().split()) >= 80:
        return art.metin("\n"), "html:article"
    d, y = sayfa.seo_metni(kok)
    return (d.metin("\n"), y) if d is not None else (None, "metin bulunamadı")


def esit_aralik(liste, n):
    if len(liste) <= n:
        return liste
    adim = len(liste) / n
    return [liste[int(i * adim)] for i in range(n)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ortak.arguman_ekle(ap)
    ap.add_argument("--kategori", type=int, default=8, help="metni olan kaç kategori sayfası toplanır")
    ap.add_argument("--tara", type=int, default=25, help="metin aramak için en çok kaç kategori sayfası okunur")
    ap.add_argument("--urun", type=int, default=6)
    ap.add_argument("--blog", type=int, default=4)
    ap.add_argument("--url", nargs="*", default=[], help="envanter yerine bu kategori adresleri okunur")
    ap.add_argument("--cikti")
    a = ap.parse_args()
    ortak.ayar_args(a)
    ham = envanter.ham_yukle()
    sayfalar = ham["sayfalar"]
    ornekler = {"kategori": [], "urun": [], "blog": []}

    # (a) kategori metinleri: ana kategori ve cinsiyet + kategori sayfaları, envanter boyunca eşit aralıklı
    adaylar = a.url or [s["url"] for s in esit_aralik(
        sorted([s for s in sayfalar if s["tip"] in ("kategori", "cinsiyet_kategori") and not s.get("q")],
               key=lambda s: (len(s["url"]), s["url"])), a.tara)]
    okunan = 0
    for u in adaylar:
        if len(ornekler["kategori"]) >= a.kategori:
            break
        k = sayfa.oku(u)
        okunan += 1
        if k.get("hata"):
            ornekler["kategori"].append({"url": u, "hata": k["hata"]}); continue
        m = (k.get("icerik") or {}).get("metin") or ""
        if len(m.split()) >= 80:
            ornekler["kategori"].append({"url": u, "h1": k.get("h1"), "title": k.get("title"), "kaynak": k["yontem"].get("icerik_html"),
                                         "basliklar": [b for _, b in (k["icerik"].get("basliklar") or [])][:12], "metin": m})
    ornekler["kategori"] = [x for x in ornekler["kategori"] if x.get("metin")]
    # (b) ürün açıklamaları
    for u in esit_aralik((ham.get("urun") or {}).get("ornek") or [], a.urun):
        m, y = urun_aciklamasi(u)
        if m and len(m.split()) >= 15:
            ornekler["urun"].append({"url": u, "kaynak": y, "metin": m})
    # (c) blog
    for s in esit_aralik([s for s in sayfalar if s["tip"] == "icerik"], a.blog):
        m, y = blog_metni(s["url"])
        if m and len(m.split()) >= 80:
            ornekler["blog"].append({"url": s["url"], "kaynak": y, "metin": m})

    sonuc = {"domain": ortak.AYAR.get("domain"), "marka": ortak.AYAR.get("marka"), "okunan_kategori": okunan,
             "kaynaklar": {}, "toplam": None}
    tum = []
    for tur, liste in ornekler.items():
        metinler = [x["metin"] for x in liste]
        tum += metinler
        sonuc["kaynaklar"][tur] = {
            "adet": len(liste), "olcum": olc("\n".join(metinler)) if metinler else None,
            "kalip": kaliplar(metinler) if metinler else None,
            "ornekler": [{"url": x["url"], "kaynak": x.get("kaynak"), "h1": x.get("h1"), "basliklar": x.get("basliklar"),
                          "ilk_paragraflar": ilk_paragraflar(x["metin"])} for x in liste]}
    if tum:
        sonuc["toplam"] = olc("\n".join(tum))
        if ortak.AYAR.get("marka_adi"):
            ad = ortak.AYAR["marka_adi"]
            sonuc["marka_adi_yazimlari"] = Counter(m.group(0) for m in re.finditer(re.escape(ad), "\n".join(tum), re.I)).most_common()
    kat = sonuc["kaynaklar"]["kategori"]["adet"]
    sonuc["yeterli"] = kat >= 3 or (kat + sonuc["kaynaklar"]["urun"]["adet"] + sonuc["kaynaklar"]["blog"]["adet"]) >= 6
    if not sonuc["yeterli"]:
        sonuc["neden"] = (f"{okunan} kategori sayfasından {kat} tanesinde 80+ kelimelik metin var; ürün ve blog örneği "
                          f"{sonuc['kaynaklar']['urun']['adet'] + sonuc['kaynaklar']['blog']['adet']}. Profil rakiplerin dilinden türetilir.")
    if a.cikti:
        json.dump(sonuc, open(a.cikti, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"{sonuc['domain']} · kategori {kat}/{okunan} okunan sayfada metin · ürün {sonuc['kaynaklar']['urun']['adet']} · "
          f"blog {sonuc['kaynaklar']['blog']['adet']} · yeterli: {'evet' if sonuc['yeterli'] else 'HAYIR'}")
    if not sonuc["yeterli"]:
        print("  " + sonuc["neden"])
    for tur, v in sonuc["kaynaklar"].items():
        o = v["olcum"]
        if not o:
            continue
        hitap = max(("siz", o["siz"]), ("sen", o["sen"]), key=lambda x: x[1])
        print(f"\n[{tur}] {v['adet']} metin · {o['kelime']} kelime · ort. cümle {o['ort_cumle_kelime']} kelime")
        print(f"  hitap: siz {o['siz']} · sen {o['sen']} · biz {o['biz']}  -> baskın: {hitap[0] if hitap[1] else 'belirsiz'}")
        print(f"  -mektedir {o['mektedir']} · ünlem/1000 {o['unlem_1000']} · emoji {o['emoji']} · İngilizce görünümlü %{o['ingilizce_oran']}"
              f" ({', '.join(w for w, _ in o['ingilizce_ornek'][:8])})")
        print(f"  'kategori' {o['kategori_kelimesi']} · 'ürün grubu' {o['urun_grubu']} · 'parça' {o['parca']} · CTA: "
              + (", ".join(f"{c} ({n})" for c, n in o["cta"]) or "-"))
        if v["kalip"]:
            print("  sık kalıplar: " + ", ".join(f"{k} ({n})" for k, n in v["kalip"]["iki_kelime"][:12]))
            print("  cümle açılışları: " + ", ".join(f"{k} ({n})" for k, n in v["kalip"]["cumle_acilisi"][:8]))
        for x in v["ornekler"][:2]:
            print(f"  örnek · {x['url']}")
            for p in x["ilk_paragraflar"][:1]:
                print(f"    \"{p[:300]}\"")
    if sonuc.get("marka_adi_yazimlari"):
        print("\nMarka adı yazımları: " + ", ".join(f"{a_} ({n})" for a_, n in sonuc["marka_adi_yazimlari"]))
    if a.cikti:
        print(f"\nyazıldı: {a.cikti}")


if __name__ == "__main__":
    main()
