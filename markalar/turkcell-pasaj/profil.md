# Turkcell Pasaj · kategori içerik profili

> İskelet profil (03.10.2026). Envanter ve betik ayarları hazır; dil, yapı ve CMS alanları ekibin ileteceği Pasaj
> profil dosyasıyla doldurulacak. O dosya gelene kadar Faz 0'daki dil ölçümü ve ekip soruları yapılmadan içerik
> üretilmez.

## Künye

| Alan | Değer |
|---|---|
| Marka adı ve yazımı | Turkcell Pasaj ("Pasaj" tek başına da kullanılır; "PASAJ" yazılmaz) |
| Alan adı | turkcell.com.tr · mağaza kökü `/pasaj` |
| Sektör | elektronik ve teknoloji perakendesi, çok markalı (bkz. `references/sektorler.md`, "Elektronik ve telekom") |
| Pazar ve dil | Türkiye · Türkçe |
| Platform | nextjs |
| GSC property | sc-domain:turkcell.com.tr (Pasaj adresleri `/pasaj/` filtresiyle okunur) |
| SEOmonitor kampanyası | 91100 "turkcell.com.tr (pasaj)" |

## Kapsam ve envanter

- Pasaj, turkcell.com.tr içinde **ayrı bir e-ticaret sitesidir**. Telco sayfaları (tarife, paket, fatura, ev
  interneti) envantere girmez; envanter yalnız Pasaj sitemap index'inden kurulur:
  `https://www.turkcell.com.tr/sitemap-pasaj-index.xml`. Kök `sitemap.xml` ve `/pasaj/sitemap.xml` kullanılmaz.
- Okunan alt sitemap'ler: `new-categories` (kategori, `/pasaj/c/{slug}-{id}`), `brands` (marka ve marka-kategori:
  `/pasaj/markalar/{marka}`, `/pasaj/{yol}-{marka}`), `landing-pages` ve `campaigns` (kampanya), `general`
  (kampanya, karşılaştırma, marka listeleri), `store` (`/pasaj/magaza/...`), `devices` (ürün). `images` sitemap'leri
  okunmaz.
- Eski yol biçimi (`/pasaj/cep-telefonu`) 301 ile `/pasaj/c/cep-telefonu-352` adresine gider; link ve sahiplikte
  her zaman `/pasaj/c/` biçimi kullanılır.
- Brief Excel'i: `new-categories` kaynağı (~175 kategori); kampanya, indirim ve yenilenmiş sayfaları hariç.
- Envanter testi (03.10.2026): 1.686 sayfa (kategori 176, marka 1.346, içerik/kampanya 102) + 2.327 ürün.

## Hitap ve ton

- **Hitap:** sen (Turkcell dili; `references/sektorler.md`). Ekip teyidi bekliyor.
- **Ton:** - (ekip dosyasıyla)
- **Ses:** - (ekip dosyasıyla)

## Cümle yapısı

- -

## Yaz / yazma tablosu

| Yazma | Yaz | Neden |
|---|---|---|
| taksit sayısı, kampanya tutarı, fiyat | rakamsız "taksit seçenekleri", "Pasaj'a özel kampanyalar" | metodoloji |

## Ürün adlandırma

- Marka ve model adları üretici yazımıyla: "iPhone", "Galaxy", "PlayStation 5", "MacBook". Teknik değerler yalnız
  üretici kaynağıyla.

## CTA dili

- -

## Ticari dil sınırları

- Net fiyat, fiyat aralığı, indirim oranı, kampanya adı, yıl, ürün sayısı: **yazılmaz** (metodoloji; her markada).
- Taksit, kampanya ve paket dili yasak değil ama rakam yok (`references/sektorler.md`).

## Yasal ve sektörel kısıtlar

- -

## CMS biçimi

| Alan | Değer |
|---|---|
| Tablo | - |
| Liste (madde imi) | - |
| Teslim | Word |
| H1 gövdede | - |
| SSS | - |

## Uzunluk, SSS ve link

- Gövde: - (ayar.json şimdilik varsayılan 1.500-2.500)
- SSS soru sayısı: - (varsayılan 5-7)
- İç link: - (varsayılan 5-8)

## Site hizmetleri (teyitli)

- -

## Kaynak

- Ekip profil dosyası: bekleniyor.

## Pilot

- Pilot içerik: - · durum: bekliyor

## Revize geçmişi

- 2026-10-03 · istek: Pasaj ayrı e-ticaret, kendi sitemap'i var · kural: envanter yalnız sitemap-pasaj-index alt
  sitemap'lerinden · ayar.json: sitemapler, url_desenleri (`/pasaj/c/`, `/pasaj/markalar/`), kur_kaynaklar
  ["new-categories"]
