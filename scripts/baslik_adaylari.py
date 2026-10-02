#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Araştırma ve sahiplik çıktılarından başlık adaylarını çıkarır. Başlık iskeleti kategoriye göre
kurulur; sabit şablon yoktur. Bu betik iskeleti KURMAZ, malzemeyi dört kaynaktan toplayıp sahiplik
süzgecinden geçirir; hangi adayın H2, hangisinin H3 ya da SSS olacağına okuyarak karar verilir.

Kaynaklar:
  1. İlk 5 rakibin H2/H3 başlıkları, konuya göre kümelenmiş (kaç rakipte geçtiğiyle)
  2. PAA soruları (kategori SERP'i + bilgi niyetli SERP)
  3. SERBEST kovasındaki uzun kuyruk kelimeler, niteleyene göre kümelenmiş (hacim toplamıyla)
  4. Otomatik tamamlama önerileri (soru ve uzun kuyruk)

Her aday sahiplik tablosuna karşı işaretlenir:
  [OK]      kullanılabilir
  [SAHİPLİ] sitenin başka bir sayfasının kelimesini taşıyor; başlık olamaz, o sayfaya link olur
  [DIŞ]     kapsam dışı (satılmayan marka, başka cinsiyet, alakasız)

Kullanım:
    python3 baslik_adaylari.py --marka X --arastirma arastirma.json --sahiplik sahiplik.json [--kayit kayit.json]
"""
import argparse, json, os, re, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak
from ortak import kumeler, duz

# Başlık konusunu tanımak için kök ipuçları; kategori ailesinden bağımsız, yalnız kümeleme içindir.
KONU = [("çeşit / tür / model", r"cesit|tur(?:u|ler)?\b|model|tipleri|nelerdir"),
        ("seçim / nelere dikkat", r"secim|secilir|secerken|dikkat|nasil alinir|hangi\w* (?:tercih|alinmali|secilmeli)"),
        ("kullanım / uygulama", r"kullan|uygula|surulur|takilir|baglanir|kurulur"),
        ("kombin / stil", r"kombin|stil|tarz|giyilir|yakisir|uyum"),
        ("özellik / avantaj / fayda", r"ozellik|avantaj|fayda|neden|ne ise yarar|etki"),
        ("malzeme / içerik / kumaş", r"malzeme|materyal|kumas|icerik|dolgu|doku|hammadde"),
        ("beden / ölçü / boyut", r"beden|olcu|boyut|numara|ebat|kac cm|hacim"),
        ("bakım / temizlik / saklama", r"bakim|temizl|yikan|saklan|omru"),
        ("marka", r"marka"),
        ("fiyat", r"fiyat|ucuz|kac tl|ne kadar"),
        ("mevsim / dönem", r"kislik|yazlik|mevsim|bahar|sezon"),
        ("kime / hangi ihtiyaca", r"icin\b|kimler|yasa gore|cilt tip|sac tip|baslangic|profesyonel"),
        ("karşılaştırma / fark", r"fark|\bmi\b.*\bmi\b|\bmu\b.*\bmu\b|karsilastir|hangisi"),
        ("tanım / nedir", r"nedir|ne demek|nasil bir")]


def konu(metin):
    d = duz(metin)
    return next((ad for ad, p in KONU if re.search(p, d)), "diğer")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ortak.arguman_ekle(ap)
    ap.add_argument("--arastirma", required=True)
    ap.add_argument("--sahiplik", required=True)
    ap.add_argument("--kayit")
    a = ap.parse_args()
    d = json.load(open(a.arastirma, encoding="utf-8"))
    sj = json.load(open(a.sahiplik, encoding="utf-8"))
    if not a.marka and not a.domain:
        a.domain = sj.get("domain") or d.get("domain") or sj.get("hedef")
    ortak.ayar_args(a)
    s = sj["satirlar"]
    hk = kumeler(d["kelime"])
    baska = [(x, kumeler(x["kelime"])) for x in s if x["kova"] == "BAŞKA SAYFA" and kumeler(x["kelime"]) - hk]
    dis = [kumeler(x["kelime"]) - hk for x in s if x["kova"] == "KAPSAM DIŞI"]

    def isaret(metin):
        k = kumeler(metin)
        for x, bk in baska:
            if bk <= k:
                return f"[SAHİPLİ -> {ortak.kisalt(x['sahip'])}]"
        return "[OK]"

    print(f"ANA KELİME: {d['kelime']}\n")
    print("== 1. Rakip başlıkları (konuya göre; kaç rakipte geçtiği) ==")
    grup = defaultdict(list)
    for i, r in enumerate(d.get("rakip_icerik") or []):
        alan = re.sub(r"^https?://(www\.)?", "", r["url"]).split("/")[0]
        for t, b in r.get("basliklar") or []:
            if t in ("H2", "H3") and 2 <= len(b.split()) <= 14:
                grup[konu(b)].append((alan, t, b))
    for ad, liste in sorted(grup.items(), key=lambda kv: -len({x[0] for x in kv[1]})):
        print(f"\n  {ad} · {len({x[0] for x in liste})} rakip")
        for alan, t, b in liste[:8]:
            print(f"    {isaret(b):<10.60} {t} {b}  ({alan})")
    okunan = [r for r in d.get("rakip_icerik") or [] if (r.get("kelime") or 0) >= 150]
    print(f"\n  içerik taşıyan rakip: {len(okunan)}/{len(d.get('rakip_icerik') or [])}"
          + (" · az rakip okunabildi; ilk 5 sayfa tarayıcıyla da açılıp bakılmalı" if len(okunan) < 3 else ""))

    print("\n== 2. PAA soruları ==")
    for q in (d["serp"].get("paa") or []) + (d.get("serp_bilgi") or {}).get("paa", []):
        print(f"    {isaret(q):<10.60} {q}   · {konu(q)}")

    print("\n== 3. SERBEST uzun kuyruk kümeleri (niteleyene göre; toplam hacim) ==")
    kume = defaultdict(list)
    for x in s:
        if x["kova"] != "SERBEST":
            continue
        for n in sorted(kumeler(x["kelime"]) - hk) or ["(ana)"]:
            kume[n].append(x)
    sirali = sorted(kume.items(), key=lambda kv: -sum(x["hacim"] or 0 for x in kv[1]))
    for n, liste in sirali[:40]:
        top = sum(x["hacim"] or 0 for x in liste)
        print(f"    {top:>7}  {n:<14} " + ", ".join(f"{x['kelime']} ({x['hacim']})" for x in liste[:4]))
    print("    Not: marka ve renk niteleyenleri başlık olmaz (marka: sahibi marka sayfası ya da kapsam dışı; "
          "renk: tek cümle).")

    print("\n== 4. Otomatik tamamlama (soru ve uzun kuyruk fikirleri) ==")
    cek = hk - ortak.cinsiyet_kokleri()
    for o in d.get("oneriler") or []:
        if cek <= kumeler(o["oneri"]):
            print(f"    {isaret(o['oneri']):<10.60} {o['oneri']}   · {konu(o['oneri'])}")

    if a.kayit:
        k = json.load(open(a.kayit, encoding="utf-8"))
        print("\n== 5. Sayfanın canlı kırılımları (başlık değil, içerik malzemesi) ==")
        print("    Alt kategoriler: " + ", ".join(ad for ad, _ in k.get("alt_kategoriler") or []))
        for ad, deger in (k.get("filtreler") or {}).items():
            print(f"    {ad}: " + ", ".join(deger[:12]))


if __name__ == "__main__":
    main()
