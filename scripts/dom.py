#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standart kütüphaneyle hafif HTML ağacı. Platformdan bağımsız sezgisel okuma (filtre blokları, ürün
kartları, SEO metni) düz regex ile yapılamaz: iç içe <div>'lerin hangisinin kapandığını bilmek gerekir.
BeautifulSoup kurulu olmayabilir; bu modül yalnız html.parser kullanır.

    kok = dom.ayristir(html)
    for d in kok.bul(sinif=r"filter-item"): print(d.metin())
"""
import html as _html
import re
from html.parser import HTMLParser

BOS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
GORUNMEZ = {"script", "style", "noscript", "template", "svg"}


class Dugum:
    __slots__ = ("etiket", "nit", "cocuk", "ust")

    def __init__(self, etiket, nit=None, ust=None):
        self.etiket, self.nit, self.cocuk, self.ust = etiket, dict(nit or {}), [], ust

    # --- erişim
    def sinif(self):
        return self.nit.get("class") or ""

    def kimlik(self):
        return self.nit.get("id") or ""

    def metin(self, ayrac=" "):
        parca = []

        def gez(d):
            for c in d.cocuk:
                if isinstance(c, str):
                    parca.append(c)
                elif c.etiket not in GORUNMEZ:
                    if c.etiket in ("br", "p", "div", "li", "h1", "h2", "h3", "h4", "tr"):
                        parca.append(ayrac)
                    gez(c)
        gez(self)
        return re.sub(r"\s+", " ", _html.unescape(" ".join(parca))).strip()

    def ic_html(self):
        """Düğümün içini yaklaşık HTML olarak geri kurar (yalnız metin, başlık, paragraf, liste, link)."""
        out = []

        def gez(d):
            for c in d.cocuk:
                if isinstance(c, str):
                    out.append(_html.escape(c, quote=False))
                elif c.etiket not in GORUNMEZ:
                    nit = ""
                    if c.etiket == "a" and c.nit.get("href"):
                        nit = f' href="{_html.escape(c.nit["href"])}"'
                    out.append(f"<{c.etiket}{nit}>")
                    gez(c)
                    if c.etiket not in BOS:
                        out.append(f"</{c.etiket}>")
        gez(self)
        return "".join(out)

    def tum(self):
        """Kendisi hariç bütün alt düğümler (derinlik öncelikli)."""
        for c in self.cocuk:
            if isinstance(c, Dugum):
                yield c
                yield from c.tum()

    def bul(self, etiket=None, sinif=None, kimlik=None, nit=None):
        """etiket: 'h1' ya da ('h2','h3'); sinif/kimlik: regex; nit: {ad: regex}."""
        et = (etiket,) if isinstance(etiket, str) else etiket
        for d in self.tum():
            if et and d.etiket not in et:
                continue
            if sinif and not re.search(sinif, d.sinif(), re.I):
                continue
            if kimlik and not re.search(kimlik, d.kimlik(), re.I):
                continue
            if nit and not all(re.search(v, d.nit.get(k) or "", re.I) for k, v in nit.items()):
                continue
            yield d

    def ilk(self, *a, **k):
        return next(self.bul(*a, **k), None)

    def atalar(self):
        d = self.ust
        while d is not None:
            yield d
            d = d.ust

    def linkler(self):
        return [(a.metin(), a.nit.get("href")) for a in self.bul("a") if a.nit.get("href")]


class _Ayristirici(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.kok = Dugum("#kok")
        self.yigin = [self.kok]

    def handle_starttag(self, tag, attrs):
        ust = self.yigin[-1]
        d = Dugum(tag, {k: (v or "") for k, v in attrs}, ust)
        ust.cocuk.append(d)
        if tag not in BOS:
            self.yigin.append(d)

    def handle_startendtag(self, tag, attrs):
        ust = self.yigin[-1]
        ust.cocuk.append(Dugum(tag, {k: (v or "") for k, v in attrs}, ust))

    def handle_endtag(self, tag):
        # kapanmamış etiketlere toleranslı: yığında geriye doğru eşleşeni bul
        for i in range(len(self.yigin) - 1, 0, -1):
            if self.yigin[i].etiket == tag:
                del self.yigin[i:]
                return

    def handle_data(self, data):
        if data.strip():
            self.yigin[-1].cocuk.append(data)


def ayristir(h):
    p = _Ayristirici()
    try:
        p.feed(h or "")
        p.close()
    except Exception:
        pass
    return p.kok
