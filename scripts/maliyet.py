#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Talep edilen sayıda kategori içeriği için token, süre, DataForSEO ve Ahrefs tahmini; işe başlamadan önce
kullanıcı onayı için.

Neden var: toplu üretim 5 saatlik kullanım penceresini ve ücretli veri bakiyelerini hızla tüketebilir. Skill
araştırmaya ya da ücretli bir çağrıya geçmeden önce bu tahmini kullanıcıya gösterir ve onay alır.

Ölçüm dayanağı (Boyner, 01-02.10.2026, Opus ajanları, tam akış: araştırma + sahiplik + içerik + denetim + Word +
brief satırı): içerik başına 330-440 bin token (medyan ~370 bin), 40-58 araç çağrısı, 18-28 dakika. Revize / devam
turu (ajan bağlamı yeniden yüklenir) 300-500 bin token. DataForSEO kategori başına $0,11-0,30 (SERP + PAA, kelime
genişletme, site haritası, gerekirse JS içerik okuma); 30 gün önbellekte olan çağrı ücretsizdir. Ahrefs varsayılan
akışta kullanılmaz (sıralama haritası GSC -> SEOmonitor -> DataForSEO); yalnız kullanıcı isterse.
Marka kurulumu (Faz 0) için ölçüm yoktur; aralık tahminidir ve öyle raporlanır.

Kullanım:
    python3 maliyet.py --marka flormar --adet 10
    python3 maliyet.py --marka flormar --adet 10 --kurulum          # yeni marka: Faz 0 dahil
    python3 maliyet.py --marka flormar --adet 10 --revize 1         # içerik başına bir revize turu bekleniyorsa
    python3 maliyet.py --marka flormar --adet 10 --ahrefs-satir 300 # Ahrefs sıralama haritası istenirse
    python3 maliyet.py --marka flormar --adet 10 --json             # makine okunur çıktı

Ahrefs kalan birimi betikten okunamaz (MCP aracı); skill `subscription-info-limits-and-usage` ile okur ve
tahmine ekler.
"""
import argparse, json, math, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

ICERIK_TOKEN = (330_000, 440_000, 370_000)      # alt, üst, medyan
REVIZE_TOKEN = (300_000, 500_000)
KURULUM_TOKEN = (150_000, 350_000)              # ölçüm yok, tahmin
ICERIK_DK = (18, 28)
DFS_USD = (0.11, 0.30)
KURULUM_DFS_USD = (0.0, 0.10)                   # dil ölçümünde JS okuma gerekirse
AHREFS_BIRIM_SATIR = 10                         # keyword, best_position, best_position_url: satır başına ~10 birim
AHREFS_ASGARI = 50                              # istek başına asgari birim
PARALEL = 2                                     # aynı anda en çok iki ajan (kullanıcı kararı)


def dfs_bakiye():
    """DataForSEO hesap bakiyesi (appendix/user_data ücretsizdir). Okunamazsa None."""
    try:
        import arastirma
        auth = arastirma.kimlik()
        r = subprocess.run(["curl", "-s", "-m", "30", "-H", f"Authorization: Basic {auth}",
                            "https://api.dataforseo.com/v3/appendix/user_data"], capture_output=True, text=True)
        d = json.loads(r.stdout)["tasks"][0]["result"][0]
        return float(d["money"]["balance"])
    except Exception:
        return None


def bin_(n):
    return f"{n / 1000:,.0f} bin".replace(",", ".") if n < 1_000_000 else f"{n / 1_000_000:.1f} milyon".replace(".", ",")


def usd(x):
    return f"${x:,.2f}".replace(".", "#").replace(",", ".").replace("#", ",")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ortak.arguman_ekle(ap)
    ap.add_argument("--adet", type=int, required=True, help="yazılacak içerik sayısı")
    ap.add_argument("--kurulum", action="store_true", help="yeni marka: Faz 0 (profil kurulumu) dahil")
    ap.add_argument("--revize", type=float, default=0, help="içerik başına beklenen revize turu (ör. 1, 0.5)")
    ap.add_argument("--ahrefs-satir", type=int, default=0, help="Ahrefs sıralama haritası istenirse içerik başına satır")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    ortak.ayar_args(a)
    n = a.adet

    tok = [ICERIK_TOKEN[0] * n, ICERIK_TOKEN[1] * n]
    tok_medyan = ICERIK_TOKEN[2] * n
    if a.revize:
        tok[0] += REVIZE_TOKEN[0] * n * a.revize; tok[1] += REVIZE_TOKEN[1] * n * a.revize
        tok_medyan += sum(REVIZE_TOKEN) / 2 * n * a.revize
    if a.kurulum:
        tok[0] += KURULUM_TOKEN[0]; tok[1] += KURULUM_TOKEN[1]; tok_medyan += sum(KURULUM_TOKEN) / 2
    dfs = [DFS_USD[0] * n, DFS_USD[1] * n]
    if a.kurulum:
        dfs[0] += KURULUM_DFS_USD[0]; dfs[1] += KURULUM_DFS_USD[1]
    ahrefs = max(AHREFS_ASGARI, a.ahrefs_satir * AHREFS_BIRIM_SATIR) * n if a.ahrefs_satir else 0
    dalga = math.ceil(n / PARALEL)
    sure = (ICERIK_DK[0] * dalga, ICERIK_DK[1] * dalga)
    bakiye = dfs_bakiye()

    out = {"marka": ortak.AYAR.get("marka_adi") or ortak.AYAR.get("domain"), "adet": n, "kurulum": a.kurulum,
           "revize_turu": a.revize, "token": [int(tok[0]), int(tok[1])], "token_medyan": int(tok_medyan),
           "sure_dk": list(sure), "paralel": PARALEL, "dfs_usd": [round(dfs[0], 2), round(dfs[1], 2)],
           "dfs_bakiye_usd": bakiye, "ahrefs_birim": ahrefs}
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2)); return

    print(f"{out['marka']} · {n} kategori içeriği" + (" + marka kurulumu (Faz 0)" if a.kurulum else "")
          + (f" + içerik başına {a.revize:g} revize turu" if a.revize else ""))
    print(f"  Token     : {bin_(tok[0])} - {bin_(tok[1])} (medyan ~{bin_(tok_medyan)}; içerik başına ~370 bin)")
    print(f"  Süre      : ~{sure[0]}-{sure[1]} dk (en çok {PARALEL} ajan paralel, {dalga} dalga)")
    print(f"  DataForSEO: {usd(dfs[0])} - {usd(dfs[1])} (30 gün önbellekte olan çağrılar ücretsiz)"
          + (f" · bakiye {usd(bakiye)}" if bakiye is not None else " · bakiye okunamadı"))
    if bakiye is not None and bakiye < dfs[1]:
        print(f"  UYARI     : DataForSEO bakiyesi üst tahminin altında ({usd(bakiye)} < {usd(dfs[1])})")
    print(f"  Ahrefs    : " + (f"~{ahrefs:,} birim".replace(",", ".") + " (kalan birim MCP ile okunur; birim kuralı geçerli)"
                                if ahrefs else "0 birim (varsayılan akışta kullanılmaz)"))
    if a.kurulum:
        print("  Not       : Faz 0 token aralığı ölçüme değil tahmine dayanır.")
    print("  Ücretsiz  : GSC (OAuth), SEOmonitor, curl / jina / yerel Playwright okumaları")


if __name__ == "__main__":
    main()
