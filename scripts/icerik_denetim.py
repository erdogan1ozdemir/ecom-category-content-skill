#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""İçerik JSON'unu teslimden önce denetler: yapı, link, kelime sahipliği, biçim, hitap ve SSS.

Neden betik: çok kategorili bir sitede en pahalı hata içeriğin başka bir sayfanın kelimesine oynamasıdır
ve bu, okuyarak en zor yakalanan hatadır. Betik başlıkları, anchor'ları ve SSS sorularını sahiplik
tablosuyla (sahiplik.py çıktısı) ve envanterle karşılaştırır; biçim ve hitap hatalarını da aynı turda toplar.

Metodoloji kuralları sabittir (fiyat / yıl / indirim yok, sahipli kelimeye başlık yok, link hedefi canlı ve
canonical, SSS answer-first). Biçim ve dil kuralları marka profilinden (markalar/{slug}/ayar.json) gelir:
  hitap                 "siz" ise "sen" kalıpları, "sen" ise "siz" kalıpları bulgu
  tablo                 false ise içerikte tablo bulgu
  h1_govdede            true ise gövde H1 ile açılır, false ise H1 yasak ve gövde paragrafla açılır
  kategori_kelimesi_yasak, parca_kurali, mektedir ("serbest" / "az" / "kacin"), birinci_cogul
  yasak_kalip           [{"desen", "ad", "seviye": "sorun" | "uyari"}]
  rakip_perakendeciler  + pazar yerleri; sitede satılan markalar muaf
  uzunluk, marka_uzunluk, link   bantlar ([min, max]; uzunluk null ise 750-3.000 çerçevesi); link_yasak_desenleri,
                        zayif_sahip_desenleri
  sss, sss_yanit        SSS soru sayısı bandı ([min, max] ya da null = araştırmada ne çıkarsa, en fazla ~12) ve
                        yanıt kelime bandı (varsayılan [30, 70]; bandın 10 kelime üstü bulgu)
Tek içerik için bant geçersiz kılınabilir: --uzunluk 750-1250 / --uzunluk yok, --sss 3-4 / --sss yok, ya da içerik
JSON'unda "uzunluk": [min, max] | null ve "sss_sayisi": [min, max] | null ("sss" alanı soru-yanıt listesidir).

Kullanım:
    python3 icerik_denetim.py --json icerik.json [--marka X]
    python3 icerik_denetim.py --json icerik.json --sahiplik sahiplik.json --arastirma arastirma.json --kayit kayit.json --canli

    --sahiplik    başlık / SSS / anchor'ları BAŞKA SAYFA kelimeleriyle karşılaştırır
    --arastirma   gövde uzunluğunu ilk 5 rakibin medyanıyla karşılaştırır
    --kayit       sayfa.py çıktısı; sayfada satılan markalar rakip adı taramasından muaf tutulur
    --canli       her link hedefini canlı okur: 200, canonical kendisi, index açık, ürün sayısı > 0

Marka verilmezse içerik JSON'undaki adresin alan adından profil bulunur. Bulgu varsa çıkış kodu 1 olur;
çıktı dosyaları üretilmeden önce çalıştırılır. "NOT:" satırları hata değil, okuyarak karar verilecek adaylardır.
"""
import argparse, json, os, re, statistics, sys
from urllib.parse import urlsplit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak
from ortak import kumeler, url_coz, duz as duzle

BICIM = [("—", "uzun tire"), ("–", "en tire"), (r"(?<=\S)  +(?=\S)", "çift boşluk"), ("®|™", "marka sembolü"),
         (r"[\U0001F300-\U0001FAFF☀-➿]", "emoji"), (r"\.\.(?!\.)", "çift nokta"), (r" ,| \.(?!\w)", "boşluk-noktalama"),
         (r"(?i)\b\d[\d.,]*\s*(TL|lira)\b|₺", "fiyat"), (r"(?i)%\s?\d+\s*(?:'?[ea]? varan )?indirim|\d+\s?%\s*indirim", "indirim oranı"),
         (r"\b20[2-3]\d\b", "yıl (zamana bağlı ifade)")]
SEN_DESEN = r"(?i)\b\w+(?:abilirsin|ebilirsin|malısın|melisin)\b|\bsenin\b|\bsana\b"
SIZ_DESEN = r"(?i)\b\w+(?:abilirsiniz|ebilirsiniz|malısınız|melisiniz)\b|\bsizin\b|\bsize\b"
UYARI_DESEN = [
    (r"(?i)\bbu sezon\b|\bbu yıl\b|\bgeçtiğimiz\b|\bson yıllarda\b|\byakında\b|\bşu sıralar\b", "zamana bağlı ifade"),
    (r"(?i)vazgeçilmez|olmazsa olmaz|\badeta\b|göz kamaştır|büyüleyici|eşsiz|kusursuz|benzersiz|mükemmel|harika|"
     r"yolculuğa|kapılarını aral|bir tık öte|sizi bekliyor|seni bekliyor", "kalıp pazarlama ifadesi (somut bilgiyle değiştirilebilir mi?)"),
    (r"(?i)sadece [^.]{3,60} değil,? aynı zamanda|hem de öyle|tabii ki|elbette ki|unutmayın ki|unutma ki|şüphesiz", "yapay geçiş kalıbı"),
    (r"(?i)tedavi ed|iyileştir|kesin çözüm|garanti(?! süre)|yüzde yüz|%\s?100 (?:etkili|sonuç)", "sağlık / kesinlik iddiası"),
    (r"[^.!?]{140,};", "noktalı virgülle uzatılmış uzun cümle (iki cümleye bölünebilir)"),
    (r"(?i)tıklayın|tıkla\b|buraya tıkla|göz atabilirsiniz|göz atabilirsin|inceleyebilirsiniz|inceleyebilirsin", "link taşımak için kurulmuş cümle olabilir"),
]
BIRINCI_COGUL = (r"(?i)\b\w+(?:ıyoruz|iyoruz|uyoruz|üyoruz|acağız|eceğiz)\b|\btavsiye ederiz\b",
                 "birinci çoğul (profil: yalnız liste girişlerinde 'sizin için grupladık' gibi kalıplarda serbest)")
PARCA = (r"(?i)giyim parças|\bparçasıdır\b|(?:her|sade|ince bir|bir) parça(?:yla|nın|larla)|parçalar(?:ı)? arasında",
         "ürün 'parça' diye anılmış (giysi / kıyafet / ürün / model; fiziksel parça değilse)")
KATEGORI = (r"(?i)(?<!filtre )\bkategori(?:de|sinde|deki|sindeki|nin|si)\b(?! \d)|\bbu kategori",
            "'kategori' kelimesi (profil yasağı: '{ürün} ürün grubu' / '{marka} {ürün} modelleri arasında')")
JENERIK_ANCHOR = {"buraya", "tiklayin", "burada", "bu sayfa", "link", "sayfa", "detaylar", "incele", "urunler", "tumu"}


SINIRSIZ_ALT, SINIRSIZ_UST = 750, 3000  # "sınır yok" seçeneğinin çerçevesi


def bant_sec(cli, d, anahtar, profil):
    """Bant önceliği: komut satırı > içerik JSON'u > profil. 'yok' / null bant yok demektir."""
    if cli is not None:
        if cli.strip().lower() in ("yok", "null", "none", "-"):
            return None
        m = re.match(r"^\s*(\d+)\s*[-,]\s*(\d+)\s*$", cli)
        if not m:
            sys.exit(f"bant biçimi '1500-2500' ya da 'yok' olmalı: {cli}")
        return [int(m.group(1)), int(m.group(2))]
    if anahtar in d:
        return list(d[anahtar]) if d[anahtar] else None
    return list(profil) if profil else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ortak.arguman_ekle(ap)
    ap.add_argument("--json", required=True)
    ap.add_argument("--sahiplik")
    ap.add_argument("--arastirma")
    ap.add_argument("--canli", action="store_true")
    ap.add_argument("--kayit", help="sayfa.py çıktısı; sayfada satılan markalar rakip adı taramasından muaf tutulur")
    ap.add_argument("--uzunluk", help="bu içerik için gövde bandı: '1500-2500' ya da 'yok' (profili geçersiz kılar)")
    ap.add_argument("--sss", help="bu içerik için SSS soru sayısı bandı: '5-7' ya da 'yok' (profili geçersiz kılar)")
    a = ap.parse_args()

    d = json.load(open(a.json, encoding="utf-8"))
    if not a.marka and not a.domain:
        a.domain = d["url"]
    A = ortak.ayar_args(a)
    g, linkler = d["govde"], d.get("linkler") or {}
    hedef = url_coz(d["url"]) or {}
    marka_sayfasi = (hedef.get("tip") or "").startswith("marka")
    hk = kumeler(d["main_kw"])
    duz = lambda i: re.sub(r"\*\*", "", re.sub(r"\[LINK(\d+)\]", lambda m: linkler.get("LINK" + m.group(1), ["?"])[0], i))
    govde_metin = " ".join(duz(i) for t, i in g if t in ("p", "li", "mad"))
    sss = d.get("sss") or []
    tum = govde_metin + " " + " ".join(q + " " + duz(c) for q, c in sss) + " " + " ".join(v for t, v in g if t in ("H1", "H2", "H3"))
    sorun, uyari = [], []

    # --- yapı
    tablo_metin = " ".join(str(h) for t, i in g if t == "tablo" for s_ in i for h in s_)
    kelime = len(govde_metin.split())           # tablolar hariç; icerik_docx.py ile aynı sayım
    h2 = [v for t, v in g if t == "H2"]; h3 = [v for t, v in g if t == "H3"]
    if A.get("h1_govdede"):
        if not g or g[0][0] != "H1":
            sorun.append("profil H1'in gövdede olmasını istiyor (h1_govdede); gövde H1 ile açılmalı")
        elif len(g) < 2 or g[1][0] != "p":
            sorun.append("H1'den sonra başlıksız giriş paragrafı gelmeli")
        if sum(1 for t, _ in g if t == "H1") > 1:
            sorun.append("gövdede birden çok H1 var")
    else:
        if not g or g[0][0] != "p":
            sorun.append("gövde başlıksız girişle açılmıyor (sayfada H1 var; ilk öğe paragraf olmalı)")
        if any(t == "H1" for t, _ in g):
            sorun.append("gövdede H1 var; sayfanın H1'i kategori adıdır (profil: h1_govdede false)")
    bant = bant_sec(a.uzunluk, d, "uzunluk", A.get("marka_uzunluk") if marka_sayfasi and A.get("uzunluk") else A.get("uzunluk"))
    if bant is None:
        # "sınır yok": uzunluk kategorinin ihtiyacından hesaplanır, çerçeve 750-3.000 kelime (kullanıcı kararı, 03.10.2026)
        if kelime > SINIRSIZ_UST:
            sorun.append(f"gövde {kelime} kelime; sınır yok seçeneğinde de en fazla {SINIRSIZ_UST:,} kelime".replace(",", "."))
        elif kelime < SINIRSIZ_ALT:
            sorun.append(f"gövde {kelime} kelime; sınır yok seçeneğinde de en az {SINIRSIZ_ALT} kelime")
        else:
            uyari.append(f"gövde {kelime} kelime; uzunluk bandı yok (çerçeve 750-3.000): uzunluk kategorinin "
                         "ihtiyacına ve rakip medyanına uygun mu, dolgu ya da kesilmiş bölüm var mı?")
    elif kelime < bant[0]:
        uyari.append(f"gövde {kelime} kelime; hedef {bant[0]:,}-{bant[1]:,}".replace(",", ".")
                     + " (gam darsa gerekçesiyle kısa kalabilir, tekrarla uzatılmaz)")
    elif kelime > bant[1] * 1.3:
        uyari.append(f"gövde {kelime} kelime; hedef {bant[0]:,}-{bant[1]:,}".replace(",", ".")
                     + " bandının belirgin üstünde (ek bölümler yeni bilgi taşıyor mu?)")
    if len(h2) < 4:
        uyari.append(f"{len(h2)} H2 var; konu kapsamı için genellikle en az 4-5 bölüm gerekir")
    ilk_h = next((t for t, _ in g if t in ("H2", "H3")), None)
    if ilk_h == "H3":
        sorun.append("ilk başlık H3; H3 yalnız bir H2'nin altında açılır")
    for b in h2 + h3:
        if b.count(",") >= 2:
            uyari.append(f"başlık üç konuyu virgülle diziyor: {b}")
        if len(b) > 70:
            uyari.append(f"başlık {len(b)} karakter: {b}")
    for b in {b for b in h2 + h3 if (h2 + h3).count(b) > 1}:
        sorun.append(f"aynı başlık iki kez: {b}")
    giris = " ".join(duz(i) for t, i in g[:next((k for k, (t, _) in enumerate(g) if t in ("H2", "H3")), len(g))] if t != "H1")
    if hk and not hk <= kumeler(giris):
        sorun.append(f"ana kelime ('{d['main_kw']}') başlıksız girişte geçmiyor")
    if any(t == "tablo" for t, _ in g) and not A.get("tablo"):
        sorun.append("içerikte tablo var; profil tablo kabul etmiyor (tablo: false), bilgi '•' satırlarına çevrilir")
    if not any(t in ("mad", "li") for t, _ in g):
        uyari.append("gövdede madde satırı ya da numaralı adım yok; taranabilirlik ve AI alıntılanabilirliği için beklenir")
    for t, i in g:
        if t in ("p", "mad", "li") and re.match(r"\s*(?:[•\-*]|\d+[.)])\s", i):
            sorun.append(f"madde imi ya da numara metne elle yazılmış (betik ekler): {i[:50]}")
    for t, i in g:
        if t == "p" and len(duz(i).split()) > 110:
            uyari.append(f"paragraf {len(duz(i).split())} kelime (bölünebilir): {duz(i)[:70]}…")
    # H2'den sonraki ilk cümle doğrudan yanıt olmalı; çok uzun ilk cümle çoğu zaman girizgâhtır
    for k, (t, v) in enumerate(g[:-1]):
        if t == "H2" and g[k + 1][0] == "p":
            ilk = re.split(r"(?<=[.!?])\s+", duz(g[k + 1][1]))[0]
            if len(ilk.split()) > 32:
                uyari.append(f"'{v}' bölümünün ilk cümlesi {len(ilk.split())} kelime; ilk cümle başlığı kısa ve doğrudan yanıtlar")
        if t == "H2" and g[k + 1][0] in ("H2",):
            sorun.append(f"'{v}' başlığının altı boş")

    # --- ana kelime yoğunluğu
    ana = duzle(d["main_kw"])
    # yoğunluk madde etiketleri ve anchor'lar dışında sayılır (etiketler kural gereği ana kelimeyi taşır)
    ciplak = " ".join(re.sub(r"\*\*", "", re.sub(r"\[LINK\d+\]", " ", re.sub(r"^\*\*[^*]+\*\*", " ", i)))
                      for t, i in g if t in ("p", "li", "mad"))
    gecis = len(re.findall(r"\b" + re.escape(ana) + r"\w*", duzle(ciplak)))
    yogunluk = gecis * len(ana.split()) / max(1, kelime) * 100
    if yogunluk > (4 if (marka_sayfasi or len(d["main_kw"].split()) == 1) else 3):
        uyari.append(f"ana kelime {gecis} kez geçiyor (%{yogunluk:.1f}); eş anlamlı ve ürün adlarıyla çeşitlendirilebilir")
    if gecis < 3:
        uyari.append(f"ana kelime gövdede {gecis} kez geçiyor")

    # --- linkler
    kull = re.findall(r"\[(LINK\d+)\]", " ".join(str(i) for t, i in g if t != "tablo") + " " +
                      " ".join(str(h) for t, i in g if t == "tablo" for s in i for h in s) + " " + " ".join(c for _, c in sss))
    for k in linkler:
        n = kull.count(k)
        if n != 1:
            sorun.append(f"{k} {n} kez kullanılmış (her link bir kez)")
    for k in set(kull):
        if k not in linkler:
            sorun.append(f"[{k}] tanımsız")
    lmin, lmax = A.get("link") or [5, 8]
    n = len(linkler)
    if n < lmin - 1 or n > lmax + 2:
        sorun.append(f"{n} iç link var; hedef {lmin}-{lmax}")
    elif not lmin <= n <= lmax:
        uyari.append(f"{n} iç link var; hedef {lmin}-{lmax}")
    hedefler, cids = {}, {}
    try:
        import envanter
        env_liste = envanter.yukle()
        sayfalar = {s["url"]: s for s in env_liste}
    except SystemExit:
        env_liste, sayfalar = [], None
        uyari.append("envanter yok; link hedefleri envanterle karşılaştırılmadı")
    for k, (anchor, url) in linkler.items():
        p = url_coz(url)
        if not p:
            sorun.append(f"{k}: site dışı link ({url})"); continue
        if p["tip"] in ("urun", "icerik", "diger"):
            sorun.append(f"{k}: hedef listeleme sayfası değil ({p['tip']}: {url}); kategori içeriğinin linkleri listeleme sayfaları arasındadır")
        if any(x in url for x in A.get("link_yasak_desenleri") or []):
            sorun.append(f"{k}: profil bu tür sayfaya link vermiyor ({url})")
        if p["tip"] == "arama":
            uyari.append(f"{k}: arama sayfasına link ({url}); yalnız o arama için açılmış kısa H3'ten verilir")
        if ortak.ayni_adres(p["url"].split("?")[0], (hedef.get("url") or "").split("?")[0]) and not p["q"]:
            sorun.append(f"{k}: sayfa kendine link veriyor")
        if p["url"] in hedefler:
            sorun.append(f"{k} ve {hedefler[p['url']]} aynı sayfaya gidiyor")
        hedefler[p["url"]] = k
        ak, sk = kumeler(anchor), kumeler(p["slug"])
        if ak == hk:
            sorun.append(f"{k}: anchor ('{anchor}') bu sayfanın ana kelimesi; başka sayfaya bu anchor'la link verilirse "
                         "iki sayfa aynı kelimede yarışır")
        if duzle(anchor) in JENERIK_ANCHOR or len(anchor.split()) > 6:
            sorun.append(f"{k}: anchor aranan terim değil ('{anchor}')")
        if ak and sk and not (ak & sk):
            uyari.append(f"{k}: anchor ('{anchor}') hedef sayfanın kelimesiyle örtüşmüyor ({p['slug']})")
        aile = (p["c"], p["g"], p["b"], p["q"])
        if p["c"] and aile in cids:
            sorun.append(f"{k} ve {cids[aile]} aynı kategori kimliğine gidiyor")
        cids[aile] = k
        if sayfalar is not None and p["url"] not in sayfalar and not a.canli:
            uyari.append(f"{k}: hedef sitemap envanterinde yok, canlı olduğu teyit edilmeli ({url})")
        ayni_ad = [u for u, s in (sayfalar or {}).items() if s["kume"] == sk and u != p["url"] and not s["b"] and not p["b"]
                   and s["tip"] != "diger"]
        if ayni_ad and not a.canli:
            uyari.append(f"{k}: aynı ada sahip {len(ayni_ad)} sayfa daha var; doğru (ürünü olan, canonical) kimlik --canli ile teyit edilmeli")
    link_bolum, bolum = {}, "Giriş"
    for t, v in g:
        if t == "H2":
            bolum = v
        elif t != "tablo":
            for k in re.findall(r"\[(LINK\d+)\]", str(v)):
                link_bolum.setdefault(bolum, []).append(k)
    for b, ks in link_bolum.items():
        if len(ks) > (6 if marka_sayfasi else 4):
            uyari.append(f"'{b}' bölümünde {len(ks)} link var; linkler bölümlere yayılır")
    for t, v in g:
        if t == "p" and len(re.findall(r"\[LINK\d+\]", v)) > 2:
            uyari.append(f"tek paragrafta {len(re.findall(r'\[LINK\d+\]', v))} link: {duz(v)[:60]}…")
    if a.canli:
        import sayfa
        for k, (anchor, url) in linkler.items():
            if (url_coz(url) or {}).get("tip") == "arama":
                continue
            c = sayfa.oku(url)
            if c.get("hata"):
                uyari.append(f"{k}: canlı okunamadı ({url})"); continue
            if c.get("durum") != 200 or (c.get("yonlendirme") and not ortak.ayni_adres(c["yonlendirme"], url)):
                sorun.append(f"{k}: hedef {c.get('durum')} / yönlendirme {c.get('yonlendirme')}")
            if not c.get("canonical_kendisi"):
                sorun.append(f"{k}: hedefin canonical'ı başka sayfa ({c.get('canonical')}); link canonical adrese verilir")
            if c.get("index") is False:
                sorun.append(f"{k}: hedef noindex ({url}); noindex sayfaya link verilmez")
            if c.get("urun_sayisi") is None:
                uyari.append(f"{k}: hedefte ürün sayısı okunamadı ({url}); elle bakılmalı")
            elif not c["urun_sayisi"]:
                sorun.append(f"{k}: hedefte ürün yok ({url})")
            elif c["urun_sayisi"] < 8:
                uyari.append(f"{k}: hedefte yalnız {c['urun_sayisi']} ürün var ({url})")

    # --- kelime sahipliği
    if a.sahiplik:
        s = json.load(open(a.sahiplik, encoding="utf-8"))
        baska = [(x, kumeler(x["kelime"])) for x in s["satirlar"] if x["kova"] == "BAŞKA SAYFA"]
        baska = [(x, k) for x, k in baska if k - hk and all(len(t) > 2 for t in k - hk)]
        cins = ortak.cinsiyet_kokleri()
        zayif_desen = list(A.get("zayif_sahip_desenleri") or [])
        for b in h2 + h3:
            bk = kumeler(b)
            for x, k in baska:
                if k <= bk:
                    msg = f"başlık başka sayfanın kelimesini hedefliyor: '{b}' -> '{x['kelime']}' ({x['sahip']})"
                    sp = url_coz(x["sahip"]) if x.get("sahip") else None
                    zayif = (sp and sp["tip"] in ("icerik", "arama")) or any(z in (x["sahip"] or "") for z in zayif_desen) or \
                        bool(hk & cins and not k & cins)      # cinsiyetli hedefte cinsiyetsiz sahip: çatı sayfa
                    (uyari if zayif else sorun).append(msg + (" [zayıf sahip: okuyarak karar ver]" if zayif else ""))
                    break
        for q, _ in sss:
            qk = kumeler(q)
            for x, k in baska:
                if k <= qk:
                    uyari.append(f"SSS sorusu başka sayfanın kelimesini taşıyor: '{q}' -> '{x['kelime']}' ({x['sahip']})")
                    break
        # başka sayfanın kelimesi gövdede linksiz ve tekrar tekrar geçiyorsa sayfa o kelimeye de oynuyor demektir
        gd = duzle(ciplak + " " + " ".join(a_ for a_, _ in linkler.values()))     # etiketler hariç, anchor'lar dahil
        for x, k in baska[:60]:
            ifade = duzle(x["kelime"])
            n_ = len(re.findall(r"\b" + re.escape(ifade), gd))
            if n_ >= 2:
                uyari.append(f"'{x['kelime']}' gövdede {n_} kez geçiyor (sahipli kelime en fazla bir kez, anchor olarak); sahibi {x['sahip']}")
        serbest = [x for x in s["satirlar"] if x["kova"] == "SERBEST"][:25]
        td = duzle(tum)
        eksik = [x for x in serbest if not (kumeler(x["kelime"]) - hk) <= kumeler(td)]
        if eksik:
            uyari.append("karşılanmayan SERBEST kelimeler (bilinçli dışarıda bırakıldıysa sorun değil): " +
                         ", ".join(f"{x['kelime']} ({x['hacim']})" for x in eksik[:12]))

    # --- uzunluk: rakip medyanı
    if a.arastirma:
        r = json.load(open(a.arastirma, encoding="utf-8"))
        rk = [x.get("kelime") for x in r.get("rakip_icerik") or [] if (x.get("kelime") or 0) >= 300]
        if rk:
            med = statistics.median(rk)
            if kelime + len(duz(tablo_metin).split()) < med:
                uyari.append(f"gövde {kelime} kelime; içerikli rakiplerin medyanı {med:.0f} ({', '.join(map(str, rk))})")

    # --- biçim ve dil (sabit + profil)
    desenler = list(BICIM)
    if A.get("kategori_kelimesi_yasak"):
        desenler.append(KATEGORI)
    hitap = (A.get("hitap") or "siz").lower()
    if hitap == "siz":
        desenler.append((SEN_DESEN, "'sen' hitabı (profil: 'siz')"))
    elif hitap == "sen":
        desenler.append((SIZ_DESEN, "'siz' hitabı (profil: 'sen')"))
    rakipler = ortak.rakip_listesi()
    if rakipler:
        desenler.append((r"(?i)\b(?:" + "|".join(re.escape(x) for x in sorted(rakipler, key=len, reverse=True)) + r")\b",
                         "rakip perakendeci adı"))
    for y in A.get("yasak_kalip") or []:
        y = {"desen": y, "ad": f"profil yasağı: {y}", "seviye": "sorun"} if isinstance(y, str) else y
        if y.get("seviye", "sorun") == "sorun":
            desenler.append((y["desen"], y.get("ad") or "profil yasağı"))
    satilan = ""
    if a.kayit:
        kk = json.load(open(a.kayit, encoding="utf-8"))
        satilan = duzle(" ".join(ad for ad, _ in (kk.get("markalar") or []) if ad))
    satilan += " | " + " | ".join(duzle(s["slug"]) for s in env_liste if s["tip"] == "marka")
    tum_duz = duzle(tum)
    for pat, ad in desenler:
        hedef_metin = tum_duz if ad == "rakip perakendeci adı" else tum
        for m in re.finditer(pat, hedef_metin):
            if ad == "rakip perakendeci adı" and re.search(r"(^|\s)" + re.escape(m.group(0).strip()) + r"(\s|$)", satilan):
                continue            # sitede satılan marka (ör. Beymen Business), rakip değil
            sorun.append(f"{ad}: …{hedef_metin[max(0, m.start() - 40):m.end() + 40]}…")
    uyarilar = list(UYARI_DESEN)
    if A.get("parca_kurali"):
        uyarilar.append(PARCA)
    bc = A.get("birinci_cogul") or "liste_girisi"
    if bc == "liste_girisi":
        uyarilar.append(BIRINCI_COGUL)
    for y in A.get("yasak_kalip") or []:
        if isinstance(y, dict) and y.get("seviye") == "uyari":
            uyarilar.append((y["desen"], y.get("ad") or "profil uyarısı"))
    for pat, ad in uyarilar:
        bul = [tum[max(0, m.start() - 30):m.end() + 25] for m in re.finditer(pat, tum)]
        if bul:
            uyari.append(f"{ad} ({len(bul)}): " + " | ".join(f"…{b}…" for b in bul[:4]))
    if bc == "yasak":
        for m in re.finditer(BIRINCI_COGUL[0], tum):
            sorun.append(f"birinci çoğul (profil: yasak): …{tum[max(0, m.start() - 30):m.end() + 25]}…")
    mekt = len(re.findall(r"(?i)\b\w+(?:mektedir|maktadır)\b", govde_metin))
    if A.get("mektedir") == "kacin" and mekt:
        uyari.append(f"'-mektedir / -maktadır' {mekt} kez (profil: kaçınılır)")
    elif A.get("mektedir") == "az" and mekt > max(2, kelime // 250):
        uyari.append(f"'-mektedir / -maktadır' {mekt} kez (profil: az kullanılır)")
    kalin = sum(len(re.findall(r"\*\*[^*]+\*\*", re.sub(r"^\*\*[^*]+\*\*", "", i))) for t, i in g if t in ("p", "mad", "li"))
    if kalin > max(8, len(h2) * 3):
        uyari.append(f"{kalin} kalın vurgu var; bölüm başına iki üç vurgu yeterli")
    # Kalın etiketli maddede ilk cümle özneyi yeniden kurmalı: etiket silinince cümle anlamını korur.
    for t, i in g:
        m = re.match(r"\*\*(.+?):\*\*\s*(.+)", i) if t == "mad" else None
        if m:
            et = {w[:4] for w in duzle(m.group(1)).split() if len(w) >= 4}
            ilk = re.split(r"(?<=[.!?;])\s+", duz(m.group(2)))[0]
            bas = {w[:4] for w in duzle(ilk).split()[:4]}
            if et and not (et & bas):
                uyari.append(f"madde ilk cümlesi özneyi kurmuyor (etiket silinince anlamsız kalabilir): {duz(i)[:90]}")
    sayilar = sorted({m.group(0).strip() for m in re.finditer(
        r"%\s?\d[\d.,]*|\bIP[X\d]\d?\b|(?<![\w%])\d[\d.,x]*\s?(?:derece|°C?|cm|mm|gr|kg|ml|saat|gün|yıl|kat|tel)?", govde_metin + " " + " ".join(duz(c) for _, c in sss))})
    if sayilar:
        uyari.append("metindeki rakamlar (her birinin kaynağı var mı?): " + ", ".join(sayilar[:25]))

    # --- SSS
    sss_bant = bant_sec(a.sss, d, "sss_sayisi", A.get("sss"))
    y_alt, y_ust = (A.get("sss_yanit") or [30, 70])[:2]
    if not sss:
        sorun.append("SSS yok")
    elif sss_bant is None:
        if len(sss) > 12:
            uyari.append(f"{len(sss)} SSS var; bant yok (araştırmada çıkan kadar) ama en fazla ~12 önerilir")
    elif not sss_bant[0] - 1 <= len(sss) <= sss_bant[1] + 2:
        uyari.append(f"{len(sss)} SSS var; {sss_bant[0]}-{sss_bant[1]} arası hedeflenir")
    h_kume = [kumeler(b) for b in h2 + h3]
    for q, c in sss:
        n_ = len(duz(c).split())
        if not q.strip().endswith("?"):
            sorun.append(f"SSS sorusu soru işaretiyle bitmiyor: {q}")
        if n_ > y_ust + 10:
            sorun.append(f"SSS yanıtı {n_} kelime (hedef {y_alt}-{y_ust}, en fazla {y_ust + 10}): {q}")
        elif n_ < max(10, y_alt - 10):
            uyari.append(f"SSS yanıtı {n_} kelime, soruyu karşıladığı kontrol edilsin: {q}")
        if kumeler(q) in h_kume:
            uyari.append(f"SSS sorusu bir başlıkla aynı; gövdede yanıtlanan soru SSS'de tekrarlanmaz: {q}")
        if re.match(r"(?i)\s*(yukarıda|daha önce|belirtildiği)", duz(c)):
            sorun.append(f"SSS yanıtı gövdeye gönderme yapıyor: {q}")

    # kip dağılımı: cümlelerin yüklemine (son kelimesine) bakılır
    yuklem = [re.sub(r"\W+$", "", c).split()[-1].lower() for t, i in g if t in ("p", "mad", "li")
              for c in re.split(r"(?<=[.!?;:])\s+", duz(i)) if re.sub(r"\W+$", "", c).split()]
    kip = {"-iyor": 0, "-ir/-ar": 0, "-ebilir(siniz)": 0, "-malı": 0, "-mıştır": 0, "-mektedir": 0, "isim/-dır": 0, "emir": 0}
    for y in yuklem:
        if re.search(r"(?:ıyor|iyor|uyor|üyor)(?:sun|sunuz)?$", y): kip["-iyor"] += 1
        elif re.search(r"(?:abilir|ebilir)(?:siniz|sin)$", y): kip["-ebilir(siniz)"] += 1     # hitaplı öneri kipi
        elif re.search(r"(?:malıdır|melidir|malı|meli|gerekir)$", y): kip["-malı"] += 1
        elif re.search(r"(?:mıştır|miştir|muştur|müştür)$", y): kip["-mıştır"] += 1
        elif re.search(r"(?:maktadır|mektedir)$", y): kip["-mektedir"] += 1
        elif re.search(r"(?:[ıiuü]n|[ae]y[ıi]n)$", y) and re.search(r"(?:yın|yin|ın|in|un|ün)$", y): kip["emir"] += 1
        elif re.search(r"(?:[dt][ıiuü]r)$", y): kip["isim/-dır"] += 1
        elif re.search(r"(?:[ıiuü]r|[ae]r|maz|mez|l[ıi]r|n[ıi]r)$", y): kip["-ir/-ar"] += 1
    # tek kipe kilitlenen metin makine çıktısı gibi okunur
    top = sum(kip.values()) or 1
    if kip["-ir/-ar"] / top > 0.7:
        uyari.append(f"gövde geniş zamana kilitlenmiş (%{kip['-ir/-ar'] / top * 100:.0f}); ürün gamı ve anlatı cümleleri "
                     "şimdiki zamanla, öneriler '-ebilir' kipiyle çeşitlendirilebilir")
    eksiz = len(re.findall(r"(?:^|[.!?]\s+)(?:[A-ZÇĞİÖŞÜ]\w+ )?" + re.escape(d["main_kw"]) + r"[, ]", ciplak, re.I))
    # yalnız çok kelimeli ve iyelik eki almamış kategori adlarında anlamlı ("kadın mont" -> "kadın montu");
    # "nevresim takımı", "güneş gözlüğü", tek kelimelik adlar ve marka adları zaten doğal biçimdedir
    son = duzle(d["main_kw"]).split()[-1]
    if eksiz >= 4 and len(d["main_kw"].split()) >= 2 and son[-1] not in "iu" and not marka_sayfasi:
        uyari.append(f"ana kelime {eksiz} cümlede yalın (eksiz) biçimde özne konumunda; cümle içinde çekimli biçim "
                     "doğal olur ('kadın montu', 'kadın montları')")
    print(f"{d['kategori']} [{A.get('marka') or A.get('domain')} · hitap {hitap}]: gövde {kelime} kelime · {len(h2)} H2 · "
          f"{len(h3)} H3 · {len(linkler)} link · {len(sss)} SSS (SSS {sum(len(duz(c).split()) for _, c in sss)} kelime) · "
          f"ana kelime {gecis} kez (%{yogunluk:.1f}) · kip: " + ", ".join(f"{k} {v}" for k, v in kip.items()))
    for u in uyari:
        print("NOT:", u)
    print("SORUN YOK" if not sorun else "SORUNLAR:\n  " + "\n  ".join(sorun))
    sys.exit(1 if sorun else 0)


if __name__ == "__main__":
    main()
