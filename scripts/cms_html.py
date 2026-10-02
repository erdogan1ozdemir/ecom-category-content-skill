#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""İçerik JSON'undan CMS'e girilecek sade HTML'i üretir. VARSAYILAN AKIŞTA KULLANILMAZ (kullanıcı kararı,
02.10.2026: yalnız docx ve brief üretilir). Yalnız kullanıcı açıkça isterse ya da marka profilinde `html: true` ise.

Çıktı temiz HTML'dir: h1 (yalnız profil h1_govdede ise), h2, h3, p, ul, ol, table, a, strong. Satır içi stil,
sınıf ve kimlik yoktur. Profil liste kabul etmiyorsa (liste: false) "mad"/"li" öğeleri <ul>/<ol> yerine "•  " /
"1. " önekli <p> olarak basılır; tablo kabul etmiyorsa (tablo: false) tablo varsa çıktı üretilmez.
Örnek (Boyner): kategori içeriği sayfa kaydının `Content` alanında HTML olarak durur; mevcut içerikler Google
Docs kalıntısı taşır (`docs-internal-guid`, `dir="ltr"`, ilk harfi kopmuş başlıklar). Bu betik alanı temiz doldurur.

Kullanım:
    python3 cms_html.py --json icerik.json --out kadin-mont-icerik.html [--marka X]
        [--baslik-kaydir 1]     # H2 -> H3, H3 -> H4 (CMS şablonu içerik başlığını H2 basıyorsa)
        [--schema]              # SSS için FAQPage JSON-LD bloğunu da ekler (ayrı dosya: *-faq-schema.json)
        [--sss-ayri]            # SSS'yi ayrı dosyaya yazar (CMS'te ayrı SSS modülü varsa)

Çıktının başında meta bilgisi yorum satırı olarak durur; CMS'e yapıştırılacak kısım yorumun altındadır.
"""
import argparse, html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak


def satir_ici(metin, linkler):
    m = html.escape(metin.strip(), quote=False)
    m = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", m)

    def link(x):
        anchor, url = linkler[x.group(1)]
        return f'<a href="{html.escape(url)}">{html.escape(anchor, quote=False)}</a>'
    m = re.sub(r"\[(LINK\d+)\]", link, m)
    assert "[LINK" not in m and "**" not in m, m[:80]
    return m


def govde_html(d, kaydir=0, liste_izni=True):
    linkler = {k: tuple(v) for k, v in (d.get("linkler") or {}).items()}
    L, liste, sayac = [], None, 0

    def kapat():
        nonlocal liste
        if liste:
            L.append(f"</{liste}>"); liste = None
    for tip, x in d["govde"]:
        sayac = sayac + 1 if tip == "li" else 0
        if tip in ("mad", "li") and not liste_izni:
            kapat()
            L.append(f"<p>{'&bull;&nbsp; ' if tip == 'mad' else str(sayac) + '. '}{satir_ici(x, linkler)}</p>")
            continue
        if tip in ("mad", "li"):
            et = "ul" if tip == "mad" else "ol"
            if liste != et:
                kapat(); L.append(f"<{et}>"); liste = et
            L.append(f"  <li>{satir_ici(x, linkler)}</li>")
            continue
        kapat()
        if tip in ("H1", "H2", "H3"):
            n = int(tip[1]) + kaydir
            L.append(f"<h{n}>{html.escape(x, quote=False)}</h{n}>")
        elif tip == "tablo":
            L.append("<table>")
            L.append("  <thead><tr>" + "".join(f"<th>{html.escape(str(h), quote=False)}</th>" for h in x[0]) + "</tr></thead>")
            L.append("  <tbody>")
            for s in x[1:]:
                L.append("    <tr>" + "".join(f"<td>{satir_ici(str(h), linkler)}</td>" for h in s) + "</tr>")
            L.append("  </tbody>\n</table>")
        else:
            L.append(f"<p>{satir_ici(x, linkler)}</p>")
    kapat()
    return "\n".join(L), linkler


def sss_html(d, linkler, kaydir=0, kalip=None):
    if not d.get("sss"):
        return ""
    n = 2 + kaydir
    L = [f"<h{n}>{html.escape(d.get('sss_baslik') or (kalip or '{kategori} Hakkında Sık Sorulan Sorular').format(kategori=d['kategori']), quote=False)}</h{n}>"]
    for soru, yanit in d["sss"]:
        L.append(f"<h{n + 1}>{html.escape(soru, quote=False)}</h{n + 1}>")
        L.append(f"<p>{satir_ici(yanit, linkler)}</p>")
    return "\n".join(L)


def schema(d):
    duz = lambda t: re.sub(r"\*\*", "", re.sub(r"\[LINK(\d+)\]", lambda m: d["linkler"]["LINK" + m.group(1)][0], t))
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": s,
                            "acceptedAnswer": {"@type": "Answer", "text": duz(y)}} for s, y in d["sss"]]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ortak.arguman_ekle(ap)
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--baslik-kaydir", type=int, default=0)
    ap.add_argument("--schema", action="store_true")
    ap.add_argument("--sss-ayri", action="store_true")
    a = ap.parse_args()
    d = json.load(open(a.json, encoding="utf-8"))
    if not a.marka and not a.domain:
        a.domain = d["url"]
    A = ortak.ayar_args(a)
    if any(t == "tablo" for t, _ in d["govde"]) and not A.get("tablo"):
        sys.exit("İçerikte tablo var; profil tablo kabul etmiyor (tablo: false).")
    govde, linkler = govde_html(d, a.baslik_kaydir, bool(A.get("liste")))
    sss = sss_html(d, linkler, a.baslik_kaydir, A.get("sss_baslik"))
    ust = f"<!-- {d['kategori']} · {d['url']} · bu yorum satırı CMS'e yapıştırılmaz -->\n"
    if a.sss_ayri and sss:
        open(a.out, "w", encoding="utf-8").write(ust + govde + "\n")
        yol = re.sub(r"\.html$", "", a.out) + "-sss.html"
        open(yol, "w", encoding="utf-8").write(sss + "\n"); print("yazıldı:", yol)
    else:
        open(a.out, "w", encoding="utf-8").write(ust + govde + ("\n" + sss if sss else "") + "\n")
    print("yazıldı:", a.out)
    if a.schema and d.get("sss"):
        yol = re.sub(r"\.html$", "", a.out) + "-faq-schema.json"
        json.dump(schema(d), open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=2); print("yazıldı:", yol)


if __name__ == "__main__":
    main()
