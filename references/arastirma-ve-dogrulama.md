# Araştırma ve doğrulama: hangi bilgi hangi kaynaktan

## Kaynak sırası

| Bilgi | Birincil kaynak | İkincil | Not |
|---|---|---|---|
| Sayfadaki ürün gamı (alt türler, markalar, kalıp, materyal, renk) | `sayfa.py` (canlı filtre verisi; yöntem kayıtta) | `sayfa.py --pw`; Shopify'da `gam_json` | Tek geçerli kaynak. Filtrede olmayan yazılmaz; okunamayan alan kullanıcıya sorulur |
| Hedef URL'nin doğruluğu | `sayfa.py` + SERP + GSC | `envanter.py sahip` | Dört sinyal örtüşmeli (bkz. sahiplik dosyası) |
| Arama hacmi, mevsimsellik | `arastirma.py` kelime kümesi (DataForSEO) | SEOmonitor kelime verisi (kampanya varsa) | 12 aylık ortalama + zirve ayı |
| Sorular | SERP PAA, bilgi niyetli SERP PAA, otomatik tamamlama | Rakip SSS'leri | Uydurulmaz |
| Rakip içerik yapısı | `arastirma.py` rakip_icerik | Sayfayı tarayıcıyla açmak | Başlıklar konu kapsamı için okunur, kopyalanmaz |
| Hangi site sayfası hangi kelimede | GSC `query,page` (OAuth, ücretsiz, 90 gün) | SEOmonitor `seomonitor_get_ranking_pages` (ücretsiz, yalnız takipli kelimeler) -> `arastirma.py` site haritası (DataForSEO, ucuz) -> Ahrefs `site-explorer-organic-keywords` (yalnız kullanıcı isterse, birim kontrolüyle; yalnız `keyword,best_position,best_position_url`) | SERP tek gün, GSC 90 gün |
| Malzeme, dolgu, kumaş, teknik ölçü | Üretici / marka sayfası, ürün verisi, standart | Genel başvuru kaynakları | Sayısal değer ancak kaynakla |
| Bakım ve kullanım | Üretici bakım / kullanım talimatı | - | "Etiketteki talimat esastır" cümlesi eklenir |
| Kozmetik içerik ve etki | Marka ürün sayfası | Dermatoloji kaynakları | İddia değil işlev: "yardımcı olur" |
| Site hizmetleri (teslimat, iade, mağazadan teslim, taksit) | Sitenin kendi yardım / içerik sayfası | - | Süre ve tutar rakamı yazılmaz; teyit adresi profile yazılır |

**Ahrefs birim kuralı:** önce ücretsiz `subscription-info-limits-and-usage`; kalan birim ≥ 0,75 × (aylık limit × aya
kalan gün / 30) **ve** ≥ 100 bin değilse Ahrefs atlanır ve kullanıcıya sorulur. Hacim, KD ve trafik sütunları
satır başına 10 birim yer; istenmez.

`arastirma.py --harita dosya.json` GSC ve SEOmonitor'dan derlenen `[{"kelime","hacim","sira","url"}]` listesini
kullanır; verilirse DataForSEO haritası çekilmez.

## İlk 5 SERP nasıl okunur

`arastirma.py` ilk 5 rakip sayfanın başlıklarını, kelime sayısını ve sorularını verir. Bakılacaklar:

1. **Ortak konular:** beş rakibin üçünde geçen başlık konusu (seçim ölçütü, kombin, bakım) bizim iskelette de
   karşılanmalı. Bu, Google'ın o sorguda beklediği kapsamdır.
2. **Eksik konular:** hiçbir rakipte olmayan ama soru verisinde çıkan konu ayrışma fırsatıdır; bir H3 ya da SSS
   ile karşılanır.
3. **Biçim:** rakiplerde tablo, liste, SSS var mı? Yoksa bunları eklemek tek başına fark yaratır (profil izin
   veriyorsa).
4. **Uzunluk tabanı:** içerik taşıyan rakiplerin medyanı.

Rakip sayfa okuma sırası (betikte otomatik; hepsi bağlama token yazmaz):

| Sıra | Yöntem | Maliyet | Not |
|---|---|---|---|
| 1 | doğrudan indirme (`curl`) | ücretsiz, ~1 sn | JavaScript'siz sayfalar |
| 2 | `r.jina.ai` okuyucusu | ücretsiz, ~5 sn | JavaScript'le oluşan sayfalar; kimlik anahtarsız dakikada sınırlı istek |
| 3 | yerel Playwright (`scripts/pw_oku.py`) | ücretsiz, ~6-13 sn | bot korumalı sayfalar; headless olmazsa headed denenir |
| 4 | DataForSEO sayfa ayrıştırma | ücretli | son çare |

MCP Playwright'ı (`browser_navigate`) elle kullanmak her sayfada 3-5 bin token bağlama yazar; betiğin okuyamadığı
nadir sayfa için kalır. Pazar yeri kategori sayfalarında H2'ler çoğunlukla ürün adıdır ve editoryal metin yoktur;
bu sayfalar başlık kaynağı sayılmaz. Kelime sayısı düşükse bu bir okuma hatası değil sayfanın kendi durumu
olabilir.

SERP'te pazar yerleri ile marka siteleri karışıktır. Pazar yerlerinin kategori metinleri genellikle kısa ve
şablondur; marka sitelerininki daha uzundur. Taban olarak içerik taşıyanlar alınır.

## Mevsimsellik

Giyim, outdoor, güneş ürünleri ve hediye kategorileri mevsimseldir (örnek: Boyner "kadın mont" 12 aylık ortalaması
33.100 iken yaz aylarında ortalama 5.800'e iner, zirvesi Aralık'tadır). Brief'te:

- Main KW Hacim sütununa 12 aylık ortalama yazılır.
- DİKKAT satırına zirve ayı ve son üç ay ortalaması yazılır.
- İçerik zirveden 6-8 hafta önce yayında olmalıysa bu da DİKKAT'e not edilir.

## Bilinen tuzaklar

- **Aynı ada sahip birden çok sayfa.** İlk çıkan adaya yazma; `sayfa.py` ile ürün sayısına ve breadcrumb'a bak.
- **Platforma göre okunamayan alanlar.** `sayfa.py` "Boş kalan alanlar" satırı; `--pw` ve `references/platformlar.md`.
  Okunamayan gam bilgisi uydurulmaz.
- **Arama ve filtre adresleri bot korumasına takılabilir;** envanterde oldukları bilinir, canlı durumları
  betikle teyit edilemeyebilir (örnek: Boyner `/search?q=`, `?renk=`).
- **Otomatik tamamlama önerilerinde alakasız sonuçlar çıkar** ("montale en iyi kadın parfümü"); öneriler elenerek
  kullanılır.
- **Site haritasında ürün sayfası sıralanıyorsa** o kelimenin kategori düzeyinde sahibi yoktur; kelime SERBEST
  sayılabilir.
- **Mevcut içerik CMS kalıntısı taşıyabilir** (Google Docs kimlikleri, ilk harfi kopmuş başlıklar: Boyner'de
  "K ız Çocuk Bluz"). Mevcut içerik revize edilecekse metin `sayfa.py --icerik` ile düz okunur, HTML'i taşınmaz.
- **Örnek: Boyner.** `g25462663` ikinci bir "kadın" cinsiyet kimliğidir; cinsiyet + kategori sayfasının
  `PageType` değeri `BrandCategoryGender` görünür; yaklaşık 45 ardışık istekten sonra Cloudflare doğrulaması
  gelebilir.
