# E-ticaret Kategori Sayfası: Brief ve İçerik

Herhangi bir e-ticaret sitesinin kategori ve marka (listeleme) sayfaları için **içerik briefi** ve **SEO + GEO
uyumlu kategori içeriği** üreten Claude Code skill'i. Boyner için kurulan `boyner-kategori-brief-icerik`
skill'inin metodolojisini ajansın bütün e-ticaret portföyüne açar: **metodoloji sabit kalır, biçim ve dil
markaya göre değişir.**

- **Bir kelime, bir sahip.** Her kelime sitenin hangi sayfasına aitse orada hedeflenir; içerik başka sayfanın
  kelimesine başlık açmaz, o sayfaya link verir (cannibalization kontrolü, sitemap envanteri üzerinden).
- **Başlıklar araştırmadan çıkar.** Sabit şablon yoktur; her kategorinin iskeleti ilk 5 rakibin başlıkları, PAA,
  uzun kuyruk kelime kümeleri ve arama eğiliminden kurulur.
- **İçerik sayfadaki gerçek ürün gamına dayanır.** Türler, markalar ve malzemeler sayfanın canlı filtre
  verisinden okunur (Next.js, Nuxt, Shopify, Akinon, VTEX adaptörleri ve HTML sezgisel okuma).
- **Marka dili siteden çıkarılır, ekibe doğrulatılır** ve `markalar/{marka}/profil.md` dosyasına yazılır.

## Kurulum

```bash
git clone https://github.com/erdogan1ozdemir/ecom-category-content-skill.git ~/.claude/skills/ecom-kategori-icerik
python3 -m pip install openpyxl python-docx playwright && python3 -m playwright install chromium
```

Gerekli araçlar:

| Araç | Ne için | Not |
|---|---|---|
| DataForSEO | SERP, PAA, kelime kümesi, site sıralama haritası | kimlik `~/.claude.json` -> `mcpServers.dfs-mcp.env` (`DATAFORSEO_USERNAME`, `DATAFORSEO_PASSWORD`); depoda kimlik tutulmaz |
| GSC MCP (`gsc`) | sayfa sorguları, sorgu-sayfa dağılımı | OAuth hesabıyla (servis hesabı yalnız son çare) |
| SEOmonitor MCP | takipli kelimelerin sıralanan sayfaları | markanın kampanyası varsa |
| Ahrefs MCP | yalnız kullanıcı isterse | birim kontrolü kuralıyla |
| Python | `openpyxl`, `python-docx`, `playwright` (Chromium) | istekler `curl` ile atılır |

## Hızlı kullanım

```bash
S=~/.claude/skills/ecom-kategori-icerik/scripts
python3 $S/envanter.py --marka flormar yenile                       # sitemap envanteri (7 günde bir)
python3 $S/sayfa.py --marka flormar https://www.flormar.com.tr/fondoten/ --cikti kayit.json
python3 $S/arastirma.py --marka flormar "fondöten" --url URL --cikti arastirma.json
python3 $S/sahiplik.py --marka flormar --arastirma arastirma.json --url URL --kayit kayit.json --teyit --cikti sahiplik.json
python3 $S/baslik_adaylari.py --marka flormar --arastirma arastirma.json --sahiplik sahiplik.json --kayit kayit.json
python3 $S/brief_satiri.py --marka flormar --kur                    # ilk kurulum: sekmeler ve Bekliyor satırları
python3 $S/brief_satiri.py --marka flormar --json satir.json
python3 $S/icerik_denetim.py --marka flormar --json icerik.json --sahiplik sahiplik.json --arastirma arastirma.json --kayit kayit.json --canli
python3 $S/icerik_docx.py --marka flormar --json icerik.json        # -> "fondoten: https://....docx"
```

Profil henüz yoksa `--marka` yerine `--domain flormar.com.tr` ile çalışılır (varsayılan ayarlar).

## Yeni marka ekleme

1. `cp -r markalar/_sablon markalar/{marka-slug}`; `ayar.json`'a `domain`, `marka_adi`, `sektor`, `cikti_klasoru`.
2. Platform: `sayfa.py --marka {slug} {kategori URL}` ("Platform", "adaptör", "Boş kalan alanlar").
3. Envanter: `envanter.py --marka {slug} yenile`; `belirsiz` adresler için `url_desenleri` yazılır.
4. Dil: `marka_dili.py --marka {slug} --cikti dil.json`; metin yetersizse rakip yedeği.
5. `profil.md` taslağı; ekibe doğrulama soruları (hitap, ton, CMS tablo / liste / HTML / H1 / SSS, uzunluk, link,
   yasak kelimeler). Ayrıntı: `references/marka-profili.md`.
6. Pilot: tek içerik, kullanıcı revizesi, revizeler profile kural olarak; onaydan sonra toplu üretim (en çok iki
   ajan aynı anda).
7. Profil değişikliği depoya commit edilir.

## Depo yapısı

```
SKILL.md                              Çalışma akışı (Faz 0-6, pilot kapısı, toplu üretim) ve değişmeyen kurallar
README.md
markalar/
  _sablon/profil.md, ayar.json        Yeni marka şablonu
  boyner/profil.md, ayar.json         Tam doldurulmuş örnek (Boyner kararları)
references/
  marka-profili.md                    Dil çıkarma, rakip yedeği, kurulum soruları, profil ve ayar alanları
  platformlar.md                      Platform tespiti, adaptörler, platform tuzakları
  sektorler.md                        Sektöre göre eksenler ve dikkat noktaları
  sahiplik-ve-cannibalization.md      Hedef URL teyidi, dört kova, GSC çapraz kontrolü
  arastirma-ve-dogrulama.md           Kaynak sırası, ilk 5 SERP okuma, mevsimsellik, tuzaklar
  icerik-kurallari.md                 Ton ve hitap (profilden), iskelet kurma, yapı taşı havuzu, GEO yazımı, SSS
  ic-link-kurallari.md                Link rolleri, anchor kuralları, hedef teyidi
  brief-kurallari.md                  Brief Excel'inin on üç sütunu
  marka-sayfasi.md                    Hedef marka sayfasıysa
  kontrol-listesi.md                  Teslim öncesi denetim
scripts/
  ortak.py                            Profil yükleme, curl istekleri (bekleme, Cloudflare), Türkçe kök/küme, URL sınıflama
  dom.py                              Standart kütüphaneyle hafif HTML ağacı
  envanter.py                         Sitemap keşfi + sınıflama; sahip, ara, iliskili, ozet, belirsiz
  sayfa.py                            Listeleme sayfasının canlı kaydı (platform adaptörleri, alan bazında yöntem)
  marka_dili.py                       Marka dili ölçümü (kategori, ürün, blog örnekleri)
  arastirma.py                        SERP + PAA + AI Overview, kelime kümesi, öneriler, rakip içerik, site haritası
  sahiplik.py                         Kelime sahipliği tablosu: HEDEF / SERBEST / BAŞKA SAYFA / KAPSAM DIŞI
  baslik_adaylari.py                  Başlık adayları, sahiplik süzgeciyle
  brief_satiri.py                     Brief Excel'i: sekmeler, Bekliyor / Hazır satırlar
  icerik_denetim.py                   Profile bağlı yapı, link, sahiplik, biçim, hitap ve SSS denetimi
  icerik_docx.py                      İçerik JSON'undan Word (profile göre liste / tablo)
  pw_oku.py                           Yerel Playwright okuyucu (rakip içerik ve render edilmiş listeleme)
  cms_html.py                         Yalnız istenirse: CMS HTML'i
examples/boyner/                      Örnek brief satırı ve içerik JSON'ları
```

Önbellek: `~/.cache/ecom-kategori-icerik/{domain}/` (envanter, kök adres) ve `~/.cache/ecom-kategori-icerik/dfs/`
(DataForSEO yanıtları, 30 gün).
