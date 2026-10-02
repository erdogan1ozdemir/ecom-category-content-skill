#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sitenin listeleme sayfası envanteri: sitemap'lerden kurulur, sınıflandırılır, önbelleğe alınır, sorgulanır.

Neden var: e-ticaret sitelerinde aynı ürün ailesi için kategori, cinsiyet + kategori, marka, marka + kategori,
filtre ve arama sayfaları ayrı ayrı yayında olabilir. İçerik yazarken her kelimenin "sahibi" olan sayfayı bilmek
gerekir; yoksa iki sayfa aynı kelimeye oynar. Bu betik hem cannibalization kontrolünün hem de iç link seçiminin
veri kaynağıdır.

Sitemap keşfi: profilde `sitemapler` varsa yalnız onlar okunur (ör. Boyner); yoksa robots.txt'deki Sitemap:
satırları, /sitemap.xml ve /sitemap_index.xml denenir, index'ler izlenir, .gz dosyaları açılır.
Sınıflandırma (ortak.url_coz): (1) profildeki url_desenleri, (2) sezgisel kurallar, (3) sitemap dosya adı
ipucu (sitemap-categories, sitemap_collections, SitemapProducts...), (4) belirsiz -> "diger". Belirsiz kalanlar
`belirsiz` komutuyla örneklenir; desenler profile yazılır ve envanter yenilenir.
Ürün adresleri sayılır ve örneklenir (marka dili için) ama hedef ya da sahip olmaz.

Kullanım:
    python3 envanter.py --marka flormar yenile          # sitemap'leri indir, envanteri kur (7 günde bir yeter)
    python3 envanter.py --domain derimod.com.tr yenile  # profil yokken (Faz 0)
    python3 envanter.py --marka X ozet                  # tip, yöntem ve sitemap bazında sayılar
    python3 envanter.py --marka X belirsiz              # sınıflanamayan adresler, yol kalıbına göre örnekli
    python3 envanter.py --marka X ara "kadın mont"      # kelimeyi taşıyan sayfalar, tipe göre
    python3 envanter.py --marka X sahip "kadın şişme mont"   # kelimenin sahibi olan sayfa(lar)
    python3 envanter.py --marka X iliskili URL          # üst, alt, kardeş, cinsiyet, marka ve filtre sayfaları

    yenile seçenekleri: --urun-sitemap 5 (en çok kaç ürün sitemap'i okunur; kalanlar sayılmaz, raporlanır)
                        --en-cok 150 (toplam sitemap dosyası sınırı)
"""
import argparse, json, os, re, sys, time
from collections import Counter, defaultdict
from urllib.parse import urlsplit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak
from ortak import url_coz, kumeler, duz, onbellek, sitemap_ipucu, liste_mi

# Sahiplik sırası: aynı kelimeye iki sayfa uyuyorsa üstteki tip sahibidir.
TIP_SIRA = ["cinsiyet_kategori", "kategori", "marka_cinsiyet_kategori", "marka_kategori", "marka_cinsiyet",
            "marka", "arama", "cinsiyet_kategori_filtre", "kategori_filtre", "marka_cinsiyet_kategori_filtre",
            "marka_kategori_filtre", "marka_filtre", "marka_cinsiyet_filtre", "icerik"]


def dosya():
    return onbellek("envanter.json")


def loclar(xml):
    return [u.replace("&amp;", "&").strip() for u in
            re.findall(r"<loc>\s*(?:<!\[CDATA\[)?\s*(.*?)\s*(?:\]\]>)?\s*</loc>", xml or "", re.S)]


def kesfet():
    """Kök sitemap'ler: profildeki liste ya da robots.txt + bilinen yollar."""
    if ortak.AYAR.get("sitemapler"):
        return [(s["url"], s.get("ad")) if isinstance(s, dict) else (s, None) for s in ortak.AYAR["sitemapler"]]
    kok = ortak.site().rstrip("/")
    robots = ortak.getir(kok + "/robots.txt", saniye=20, deneme=1)
    adaylar = re.findall(r"(?im)^\s*sitemap\s*:\s*(\S+)", robots or "")
    adaylar += [kok + "/sitemap.xml", kok + "/sitemap_index.xml"]
    gorulen, out = set(), []
    for u in adaylar:
        anahtar = re.sub(r"^https?://(www\.)?", "", u)
        if anahtar not in gorulen:
            gorulen.add(anahtar); out.append((u, None))
    return out


def filtre_metni(q):
    """?renk=nude&materyal=deri -> 'nude deri' (filtre değeri kelimenin parçasıdır: nude ruj)."""
    return " ".join(v.replace("-", " ").replace(",", " ") for kv in (q or "").split("&") if "=" in kv
                    for v in [kv.split("=", 1)[1]])


def yenile(urun_sitemap=5, en_cok=150):
    kokler = kesfet()
    profil_listesi = bool(ortak.AYAR.get("sitemapler"))
    kuyruk = [(u, ad, 0) for u, ad in kokler]
    kayit, gorulen, sm_rapor = [], set(), []
    urun = {"sayi": 0, "ornek": [], "okunan_sitemap": 0, "atlanan_sitemap": 0}
    ziyaret, bulundu = set(), False
    while kuyruk:
        u, ad, derinlik = kuyruk.pop(0)
        if u in ziyaret:
            continue
        if len(ziyaret) >= en_cok:
            print(f"UYARI: {en_cok} sitemap sınırına ulaşıldı; kalan {len(kuyruk) + 1} dosya okunmadı.", file=sys.stderr)
            break
        ipucu = sitemap_ipucu(u)
        if ipucu == "urun" and urun["okunan_sitemap"] >= urun_sitemap:
            urun["atlanan_sitemap"] += 1
            continue
        ziyaret.add(u)
        r = ortak.istek(u, 90)
        xml = r["govde"]
        if ortak.cloudflare_mi(xml):
            sm_rapor.append({"url": u, "durum": "cloudflare"}); print(f"{u}: Cloudflare doğrulaması", flush=True)
            continue
        locs = loclar(xml)
        if not locs:
            if derinlik or profil_listesi:
                sm_rapor.append({"url": u, "durum": f"boş ({r['kod']})"})
            continue
        bulundu = True
        if "<sitemapindex" in xml[:3000] or all(re.search(r"\.xml(\.gz)?(\?|$)|sitemap", x, re.I) for x in locs[:20]):
            for x in locs:
                kuyruk.append((x, ad, derinlik + 1))
            sm_rapor.append({"url": u, "durum": f"index ({len(locs)} alt dosya)"})
            continue
        yol = urlsplit(u).path.strip("/")
        on = yol.split("/")[0] + "/" if "/" in yol and yol.split("/")[0].lower() in ortak.DIL_ONEK else ""
        kaynak = ad or (on + re.sub(r"\.xml(\.gz)?$", "", yol.rsplit("/", 1)[-1])) or u
        if ipucu == "urun":
            urun["okunan_sitemap"] += 1
        n = nu = 0
        for x in locs:
            p = url_coz(x, ipucu)
            if not p:
                continue
            if p["tip"] == "urun":
                urun["sayi"] += 1; nu += 1
                if len(urun["ornek"]) < 300:
                    urun["ornek"].append(p["url"])
                continue
            if p["url"] in gorulen:
                continue
            gorulen.add(p["url"])
            p["kaynak"] = kaynak
            p["kume"] = sorted(kumeler((p["slug"] or "") + " " + filtre_metni(p["q"])))
            kayit.append(p); n += 1
        sm_rapor.append({"url": u, "ad": kaynak, "ipucu": ipucu, "sayfa": n, "urun": nu, "durum": "ok"})
        print(f"{kaynak}: {n} sayfa" + (f" · {nu} ürün" if nu else ""), flush=True)
    if not bulundu:
        sys.exit("Sitemap bulunamadı (robots.txt, /sitemap.xml, /sitemap_index.xml). Profile `sitemapler` yazılmalı.")
    veri = {"tarih": time.strftime("%Y-%m-%d"), "domain": ortak.AYAR.get("domain"), "sitemapler": sm_rapor,
            "urun": urun, "sayfalar": kayit}
    json.dump(veri, open(dosya(), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"toplam {len(kayit)} sayfa · {urun['sayi']} ürün ({urun['okunan_sitemap']} ürün sitemap'i okundu"
          + (f", {urun['atlanan_sitemap']} atlandı" if urun["atlanan_sitemap"] else "") + f") -> {dosya()}")
    ozet(veri["sayfalar"], veri)


def ham_yukle():
    if not os.path.exists(dosya()):
        sys.exit(f"Envanter yok ({ortak.AYAR.get('domain')}). Önce: python3 envanter.py --marka ... yenile")
    return json.load(open(dosya(), encoding="utf-8"))


def yukle():
    d = ham_yukle()
    yas = (time.time() - os.path.getmtime(dosya())) / 86400
    if yas > 7:
        print(f"UYARI: envanter {yas:.0f} günlük; 'envanter.py yenile' ile güncellenmeli.", file=sys.stderr)
    for s in d["sayfalar"]:
        s["kume"] = frozenset(s["kume"])
    return d["sayfalar"]


def sirala(sayfalar):
    return sorted(sayfalar, key=lambda s: (TIP_SIRA.index(s["tip"]) if s["tip"] in TIP_SIRA else 99, len(s["url"])))


def sahip(kelime, sayfalar):
    """Kelimenin kök kümesiyle birebir eşleşen sayfalar; sahiplik sırasına göre (sınıflanamayanlar hariç)."""
    k = kumeler(kelime)
    return sirala([s for s in sayfalar if s["kume"] == k and s["tip"] != "diger"]) if k else []


def ara(kelime, sayfalar):
    k = kumeler(kelime)
    return sirala([s for s in sayfalar if k and k <= s["kume"] and s["tip"] != "diger"])


def iliskili(url, sayfalar):
    p = url_coz(url)
    if not p:
        sys.exit("URL çözülemedi: " + url)
    ben = next((s for s in sayfalar if s["url"] == p["url"]), None)
    kume = ben["kume"] if ben else kumeler(p["slug"])
    cins = ortak.cinsiyet_kokleri()
    cekirdek = frozenset(kume - cins) or kume                 # cinsiyet kelimesi atılmış ürün çekirdeği
    out = {"hedef": p["url"], "tip": p["tip"], "envanterde": bool(ben), "cekirdek": sorted(cekirdek)}
    diger = [s for s in sayfalar if s["url"] != p["url"] and liste_mi(s) and s["tip"] != "arama"]
    ayni_c = [s for s in diger if p["c"] and s["c"] == p["c"]]
    out["ayni_kategori_cinsiyetler"] = [s["url"] for s in ayni_c if not s["b"] and not s["q"]]
    out["ayni_kategori_filtreler"] = [s["url"] for s in ayni_c if s["q"] and not s["b"]
                                      and (s["g"] == p["g"] or not s["g"] or not p["g"])][:60]
    out["ayni_kategori_markalar"] = [s["url"] for s in ayni_c if s["b"] and not s["q"]
                                     and (s["g"] == p["g"] or not p["g"])][:60]
    kat = [s for s in diger if not s["b"] and not s["q"] and s["c"] != p["c"]]
    # alt: hedefin kümesini kapsayan daha dar sayfalar (kadın mont -> kadın şişme mont)
    out["alt_sayfalar"] = [s["url"] for s in sirala([s for s in kat if kume < s["kume"]])][:80]
    # üst: hedefin kümesinin alt kümesi olan daha geniş sayfalar (kadın şişme mont -> kadın mont, mont)
    out["ust_sayfalar"] = [s["url"] for s in sirala([s for s in kat if s["kume"] and s["kume"] < kume])][:20]
    # akraba: aynı ürün çekirdeğini başka cinsiyetle taşıyanlar (erkek mont, kız çocuk mont)
    out["akraba_sayfalar"] = [s["url"] for s in sirala([s for s in kat if cekirdek <= s["kume"]
                              and not kume <= s["kume"]])][:40]
    out["arama_sayfalari"] = [s["url"] for s in sayfalar if s["tip"] == "arama" and cekirdek <= s["kume"]][:30]
    return out


def ozet(sayfalar, veri=None):
    veri = veri or ham_yukle()
    print(f"\n{veri.get('domain')} · {veri.get('tarih')} · {len(sayfalar)} sayfa")
    print("Tip dağılımı:")
    for t, n in Counter(s["tip"] for s in sayfalar).most_common():
        print(f"  {n:6d}  {t}")
    print("Sınıflama yöntemi:")
    for t, n in Counter((s.get("yontem") or "profil").split(":")[0] for s in sayfalar).most_common():
        print(f"  {n:6d}  {t}")
    u = veri.get("urun") or {}
    if u:
        print(f"Ürün adresi: {u.get('sayi')} ({u.get('okunan_sitemap')} ürün sitemap'i okundu"
              + (f", {u.get('atlanan_sitemap')} atlandı; gerçek sayı daha yüksek" if u.get("atlanan_sitemap") else "") + ")")
    sorunlu = [s for s in veri.get("sitemapler") or [] if s.get("durum") not in ("ok",) and not str(s.get("durum")).startswith("index")]
    for s in sorunlu:
        print(f"  sitemap {s['durum']}: {s['url']}")
    b = sum(1 for s in sayfalar if s.get("yontem") == "belirsiz")
    if b:
        print(f"Belirsiz: {b} adres sınıflanamadı -> 'envanter.py belirsiz' ile örneklenir, desen profile yazılır.")


def belirsiz(sayfalar, n=40):
    """Sınıflanamayan adresleri yol kalıbına göre gruplar: profile url_desenleri yazmak için."""
    grup = defaultdict(list)
    for s in sayfalar:
        if s.get("yontem") != "belirsiz" and s["tip"] != "diger":
            continue
        yol = urlsplit(s["url"]).path
        seg = [x for x in yol.split("/") if x]
        kalip = "/" + "/".join(re.sub(r"\d+", "N", x) if re.search(r"\d", x) else "*" for x in seg) + ("/" if yol.endswith("/") else "")
        grup[(s.get("yontem") or "", s.get("kaynak") or "", kalip)].append(s["url"])
    print(f"{sum(len(v) for v in grup.values())} adres 'diger' tipinde. Kalıp · sitemap · sınıflama yöntemi · örnekler:")
    for (yontem, kaynak, kalip), us in sorted(grup.items(), key=lambda kv: -len(kv[1]))[:n]:
        print(f"\n  {len(us):5d}  {kalip}   (sitemap: {kaynak} · {yontem})")
        for x in us[:5]:
            print(f"         {x}")
    print("\nDesen önerisi profile şöyle yazılır (ayar.json -> url_desenleri; ilk eşleşen kazanır):\n"
          '  {"tip": "kategori", "desen": "^/[a-z0-9-]+/$"}   ·   {"tip": "urun", "desen": "-\\\\d{13}/$"}\n'
          "Ardından: envanter.py yenile")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ortak.arguman_ekle(ap)
    ap.add_argument("komut", choices=["yenile", "ozet", "ara", "sahip", "iliskili", "belirsiz"])
    ap.add_argument("arg", nargs="*")
    ap.add_argument("--urun-sitemap", type=int, default=5)
    ap.add_argument("--en-cok", type=int, default=150)
    a = ap.parse_intermixed_args()
    ortak.ayar_args(a)
    if a.komut == "yenile":
        return yenile(a.urun_sitemap, a.en_cok)
    sayfalar = yukle()
    if a.komut == "ozet":
        ozet(sayfalar)
    elif a.komut == "belirsiz":
        belirsiz(sayfalar)
    elif a.komut in ("ara", "sahip"):
        kelime = " ".join(a.arg)
        liste = (sahip if a.komut == "sahip" else ara)(kelime, sayfalar)
        print(f"'{kelime}' -> kök kümesi {sorted(kumeler(kelime))} · {len(liste)} sayfa")
        for s in liste[:80]:
            print(f"  {s['tip']:32s} {s['url']}")
    elif a.komut == "iliskili":
        print(json.dumps(iliskili(a.arg[0], sayfalar), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
