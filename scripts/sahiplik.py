#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kelime sahipliği (cannibalization) tablosu: araştırmadaki her kelime sitenin hangi sayfasına ait?

E-ticaret sitelerinde bir kelimeye çoğu zaman birden fazla listeleme sayfası aday. İçerik yazılmadan önce her
kelime dört kovadan birine düşer:

  HEDEF        Bu sayfanın kelimesi. Title, H1, giriş ve H2'lerde işlenir.
  BAŞKA SAYFA  Kelimenin sitede kendi sayfası var (alt kategori, marka + kategori, renk araması...).
               Bu içerikte hedeflenmez: başlığa çıkmaz, SSS sorusu olmaz. Geçerse bir kez ve o sayfaya
               link veren anchor olarak geçer.
  SERBEST      Hedefin kapsamında, kendi sayfası olmayan uzun kuyruk. H2/H3, madde ya da SSS ile bu
               sayfada karşılanır; trafik kazancı buradan gelir.
  KAPSAM DIŞI  Sitede satılmayan marka ya da perakendeci kelimesi, başka cinsiyet. Yazılmaz.

Sahip belirleme sırası: (1) hedef sayfanın canlı kırılımları (--kayit), (2) sitenin o kelimede Google'da
sıralanan sayfası (arastirma.py haritası), (3) envanterde kök kümesi kelimeyle birebir eşleşen sayfa. Aynı
ada sahip birden çok kategori kimliği varsa --teyit canlı kayıttan ürün sayısı en yüksek ve canonical'ı
kendisi olanı seçer. Rakip perakendeci listesi profilden (rakip_perakendeciler) ve pazar yerlerinden gelir;
sitede sayfası olan marka rakip sayılmaz.

Kullanım:
    python3 sahiplik.py --marka boyner --arastirma $T/arastirma.json --url https://www.boyner.com.tr/kadin-mont-x-g3731-c23896554 \\
        --kayit $T/kayit.json [--teyit] [--min-hacim 50] [--cikti $T/sahiplik.json]
"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak
from ortak import kumeler, url_coz, duz, KAPSAM_DISI_KALIP, RENKLER, kisalt
import envanter

MARKA_EK = frozenset({"the", "jeans", "jean", "assn", "by", "of", "club", "sport", "kids", "home"})


def _urun_mu(u):
    p = url_coz(u) if u else None
    return bool(p) and p["tip"] == "urun"


def siniflandir(kw, hedef, sayfalar, harita, marka_kumeleri, cins_kok, markali, canli, marka_dizin, rakipler):
    k = kumeler(kw["kelime"])
    hk = hedef["kume"]
    if not k:
        return None
    h_url = harita.get(k)                      # harita kök kümesiyle eşlenir: "erkek keten gömlek" = "keten erkek gömlek"
    if re.search(KAPSAM_DISI_KALIP, duz(kw["kelime"])):
        return {"kelime": kw["kelime"], "hacim": kw.get("hacim"), "kova": "KAPSAM DIŞI", "sahip": None,
                "not": "kampanya / gezinme / konu dışı kalıp", "adaylar": []}
    sahipler = [s for s in envanter.sahip(kw["kelime"], sayfalar)]
    if k in canli and k != hk:
        # sayfanın kendi filtresinde listelenen alt kategori ya da marka kırılımı: en güvenilir sahip.
        # Sitemap eski kategori kimliklerini de taşıyabilir; canlı kayıttaki adres doğru kimliktir.
        return {"kelime": kw["kelime"], "hacim": kw.get("hacim"), "kova": "BAŞKA SAYFA", "sahip": canli[k],
                "not": "canlı kayıt: sayfanın kendi alt kırılımı", "adaylar": []}
    if not sahipler and k != hk:
        # marka sayfaları slug'da fazladan bir kelime taşıyabilir ("the north face" / "north face")
        sahipler = envanter.sirala([s for s in markali if k < s["kume"] and len(s["kume"] - k) == 1
                                    and (s["kume"] - k) <= MARKA_EK])
    # aynı ada sahip birden çok kategori kimliği varsa hedefin kategori ailesindeki aday öne alınır
    sahipler.sort(key=lambda s: 0 if s["c"] == hedef["c"] else 1)
    s_url = [s["url"] for s in sahipler]

    def hedef_aile(u):
        p = url_coz(u) if u else None
        return bool(p) and p.get("c") == hedef["c"] and not p.get("b") and p.get("g") in (hedef["g"], None) and not p.get("q")
    baska_cins = (k & cins_kok) - hk
    if k == hk or (h_url and h_url["url"].split("?")[0] == hedef["url"] and not sahipler):
        kova, sahip, not_ = "HEDEF", hedef["url"], ("Google'da sıralanan: %s. sıra · %s" % (h_url["sira"], kisalt(h_url["url"])) if h_url else "")
        if k != hk:
            kova, not_ = "SERBEST", f"sitede bu sayfa sıralanıyor ({h_url['sira']}.), kendi sayfası yok"
    elif hedef["url"] in s_url:
        kova, sahip, not_ = "HEDEF", hedef["url"], ""
    elif baska_cins and (hk & cins_kok) and not (hk & cins_kok <= k and len(k & cins_kok) == len(hk & cins_kok)):
        # hedef cinsiyetliyken başka cinsiyetin kelimesi; cinsiyetsiz hedefte (kategori, marka) bu kural işlemez
        kova, sahip, not_ = "KAPSAM DIŞI", (s_url or [h_url and h_url["url"]])[0], "başka cinsiyet"
    elif sahipler:
        kova, sahip = "BAŞKA SAYFA", s_url[0]
        not_ = f"{len(s_url)} aday sayfa" if len(s_url) > 1 else sahipler[0]["tip"]
        if h_url and h_url["sira"] and h_url["sira"] <= 20 and not _urun_mu(h_url["url"]) and h_url["url"] != hedef["url"]:
            sahip, not_ = h_url["url"], f"Google'da bu sayfa sıralanıyor ({h_url['sira']}.)"
    elif h_url and not hedef_aile(h_url["url"]) and h_url["sira"] and h_url["sira"] <= 20 and not _urun_mu(h_url["url"]):
        kova, sahip, not_ = "BAŞKA SAYFA", h_url["url"], f"Google'da bu sayfa sıralanıyor ({h_url['sira']}.)"
    else:
        ek = duz(kw["kelime"])
        # Kelime, sitede sayfası olan bir markanın adını taşıyorsa sahibi marka tarafıdır (marka + kategori
        # kırılımı canlı kayıttan teyit edilir). Renk adıyla çakışan marka adları (mavi) bu kuralın dışındadır.
        marka = next((m for m in marka_dizin if m <= k and not m <= hk and not m <= RENKLER), None)
        if marka and not hedef.get("b"):
            return {"kelime": kw["kelime"], "hacim": kw.get("hacim"), "kova": "BAŞKA SAYFA", "sahip": marka_dizin[marka],
                    "not": "marka kelimesi: marka + kategori kırılımı varsa o, yoksa marka sayfası", "adaylar": []}
        rakip = next((r for r in rakipler if f" {r} " in f" {ek} "), None)
        if rakip and kumeler(rakip) not in marka_kumeleri:
            kova, sahip, not_ = "KAPSAM DIŞI", None, f"sitede satılmayan marka/perakendeci: {rakip}"
        elif hk <= k or (hk - cins_kok) <= k:
            kova, sahip, not_ = "SERBEST", None, ("soru" if kw.get("soru") else "uzun kuyruk")
            if h_url:
                not_ += f" · site {h_url['sira']}. sırada: {kisalt(h_url['url'])}"
        else:
            kova, sahip, not_ = "KAPSAM DIŞI", None, "hedefin ürün çekirdeğini taşımıyor"
    return {"kelime": kw["kelime"], "hacim": kw.get("hacim"), "kova": kova, "sahip": sahip, "not": not_,
            "adaylar": s_url[:8] if len(s_url) > 1 else []}


def teyit_et(satirlar, hedef_c):
    """Çok adaylı sahiplerde canlı kaydı okuyup ürün sayısı en yüksek, canonical'ı kendisi olan sayfayı seçer."""
    import sayfa
    onbellek = {}
    for s in satirlar:
        if s["kova"] != "BAŞKA SAYFA" or not s["adaylar"]:
            continue
        en_iyi, en_cok = None, -1
        for u in s["adaylar"][:6]:
            if (url_coz(u) or {}).get("tip") == "arama":
                continue
            if u not in onbellek:
                k = sayfa.oku(u)
                # H1'i kelimeyle örtüşmeyen sayfa (ör. "Mont & Şişme Mont") aynı ada sahip görünse de sahip değildir
                uyum = kumeler(k.get("h1") or "") <= kumeler(s["kelime"]) | kumeler(k.get("cinsiyet") or "")
                onbellek[u] = ((k.get("urun_sayisi") or 0) if uyum else 0, k.get("canonical_kendisi"), k.get("durum"))
            n, kendi, durum = onbellek[u]
            puan = n + (10 ** 6 if (url_coz(u) or {}).get("c") == hedef_c else 0)   # hedefin kategori ailesi önde
            if durum == 200 and kendi and n > 0 and puan > en_cok:
                en_iyi, en_cok = u, puan
        if en_iyi:
            s["sahip"] = en_iyi
            s["not"] = f"teyitli: {onbellek[en_iyi][0]} ürün · {len(s['adaylar'])} aday arasından"
    return satirlar


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ortak.arguman_ekle(ap)
    ap.add_argument("--arastirma", required=True)
    ap.add_argument("--url", required=True, help="hedef sayfa")
    ap.add_argument("--min-hacim", type=int, default=50)
    ap.add_argument("--kayit", help="sayfa.py --cikti dosyası; sayfanın canlı alt kategori ve marka kırılımları "
                                    "sahip olarak öncelik alır (önerilir)")
    ap.add_argument("--teyit", action="store_true", help="çok adaylı sahipleri canlı kayıttan teyit et (yavaş)")
    ap.add_argument("--cikti")
    a = ap.parse_args()
    if not a.marka and not a.domain:
        a.domain = a.url
    ortak.ayar_args(a)

    d = json.load(open(a.arastirma, encoding="utf-8"))
    sayfalar = envanter.yukle()
    hedef = url_coz(a.url)
    if not hedef:
        sys.exit("Hedef URL çözülemedi (alan adı marka profiliyle uyuşmuyor olabilir)")
    hedef["kume"] = kumeler(hedef["slug"])
    harita = {}
    for x in (d.get("site_haritasi") or d.get("boyner_haritasi") or {}).get("liste") or []:
        if x.get("url"):
            harita.setdefault(kumeler(x["kelime"]), {"url": x["url"].split("?srsltid")[0], "sira": x.get("sira")})
    marka_kumeleri = {s["kume"] for s in sayfalar if s["tip"] == "marka"}
    markali = [s for s in sayfalar if s["b"] and s["c"]]
    marka_dizin = {s["kume"]: s["url"] for s in sayfalar if s["tip"] == "marka" and s["kume"]}
    cins_kok = ortak.cinsiyet_kokleri()
    rakipler = ortak.rakip_listesi()

    canli = {}
    if a.kayit:
        kayit = json.load(open(a.kayit, encoding="utf-8"))
        for ad, u in (kayit.get("alt_kategoriler") or []) + (kayit.get("kardes_kategoriler") or []) + (kayit.get("markalar") or []):
            p = url_coz(u) if u else None
            if p and not p["q"] and ortak.liste_mi(p):
                canli.setdefault(kumeler(p["slug"]), p["url"])
            if p and ad and ortak.liste_mi(p) and not kumeler(ad) <= kumeler(p["slug"]):
                canli.setdefault(kumeler(ad), p["url"])      # slug adı yansıtmıyorsa (kimlikli/kısaltılmış adres) görünen ad da eşlenir
        if kayit.get("markalar"):
            marka_kumeleri |= {kumeler(ad) for ad, _ in kayit["markalar"] if ad}
    kelimeler = [k for k in d["kelimeler"]["liste"] if (k.get("hacim") or 0) >= a.min_hacim]
    gorulen, satirlar, varyant = set(), [], {}
    for kw in kelimeler:
        k = kumeler(kw["kelime"])
        varyant.setdefault(k, []).append(f"{kw['kelime']} ({kw.get('hacim')})")
        if k in gorulen:          # "kadın mont" / "mont kadın" / "kadın mont modelleri" aynı niyet: en hacimlisi kalır
            continue
        gorulen.add(k)
        r = siniflandir(kw, hedef, sayfalar, harita, marka_kumeleri, cins_kok, markali, canli, marka_dizin, rakipler)
        if r:
            satirlar.append(r)
    for s_ in satirlar:           # aynı kök kümesinin diğer yazımları (brief'in ikincil sütunu için)
        s_["varyantlar"] = varyant.get(kumeler(s_["kelime"]), [])[1:6]
    if a.teyit:
        satirlar = teyit_et(satirlar, hedef["c"])

    for kova in ("HEDEF", "SERBEST", "BAŞKA SAYFA", "KAPSAM DIŞI"):
        grup = [s for s in satirlar if s["kova"] == kova]
        print(f"\n== {kova} ({len(grup)}) ==")
        for s in grup[:45]:
            sahip = kisalt(s["sahip"] or "")
            print(f"  {s['hacim'] or 0:>6}  {s['kelime']:<38} {sahip[:70]:<70} {s['not']}"
                  + (("  · varyant: " + ", ".join(s["varyantlar"])) if kova == "HEDEF" and s.get("varyantlar") else ""))
        if len(grup) > 45:
            print(f"  ... +{len(grup) - 45} kelime (tam liste JSON çıktısında)")
    # aynı kelimede iki site sayfası sıralanıyorsa site düzeyinde çakışma vardır; içerikle çözülmez, bildirilir
    if a.cikti:
        json.dump({"hedef": hedef["url"], "domain": ortak.AYAR.get("domain"), "satirlar": satirlar},
                  open(a.cikti, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\nyazıldı: {a.cikti}")


if __name__ == "__main__":
    main()
