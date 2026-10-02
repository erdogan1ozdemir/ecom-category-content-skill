# Brief Excel'i: sütunlar ve kurallar

Brief, sayfa başına **tek satır**dır. Marka başına bir Excel tutulur; dosya adı profildeki `brief_dosyasi` ya da
`{Marka} kategori içerik briefleri.xlsx`, yeri profildeki çıktı klasörü. Excel, içerik yazılacak hedef sayfaları
**sayfa tipine göre sekmelerde** taşır: profildeki `sekmeler`, yoksa envanterden `Kategori` + sitede cinsiyetli
kategori varsa `Kadın`, `Erkek`, `Çocuk`, `Bebek` + `Marka`. `brief_satiri.py --kur` sekmeleri envanterden
(ya da `--hedefler` dosyasındaki adreslerden) kurar; her sayfa `Bekliyor` durumunda bir satırdır. Brief
hazırlandığında satır URL'ye göre bulunup doldurulur ve `Hazır` olur. Envanterde olmayan bir sayfa ilgili sekmenin
sonuna eklenir.

## Düzen

Tablo başlığı 1. satırda, veri 2. satırdan başlar; üstte not bloğu ve birleştirilmiş hücre yoktur.
Başlık Calibri 11 kalın beyaz, `#434343` dolgulu; gövde Calibri 10 `#10332F`, sola ve dikeyde ortalı,
kaydırmalı. `scripts/brief_satiri.py` biçimi kendisi kurar.

## Sütunlar

**Kategori** - sayfanın adı ("Kadın Mont").

**URL** - teyit edilmiş hedef adres (bkz. `sahiplik-ve-cannibalization.md`, Adım 1).

**Brief** - `Bekliyor` ya da `Hazır`; betik doldurur. Kurulumda Kategori sütunu slug'dan üretilir (Türkçe
karaktersiz); brief hazırlanınca sayfanın gerçek adıyla değişir.

**Main KW** - sayfanın ana kelimesi, küçük harfle. Kategori sorgusunun en hacimli doğal biçimi ("kadın mont";
"mont kadın" ya da "bayan mont" değil).

**Main KW Hacim** - 12 aylık ortalama aylık arama, sayı olarak. Mevsimsel kategorilerde ortalama yanıltır:
zirve ayı ve son üç ay ortalaması DİKKAT satırına yazılır.

**İkincil ve Uzun Kuyruk Kelimeler** - aynı hücrede alt alta `kelime (hacim)`, hacme göre azalan. Yalnız HEDEF ve
SERBEST kovasındaki kelimeler. Hacmi olmayan ama otomatik tamamlamadan gelen hedefli ifade `(-)` ile yazılır.
15-25 kelime yeter; aynı kök kümesinin varyantları tek satırda birleştirilir.

**Alt Başlıklar** - `H2: Başlık`, `H3: Başlık` satırları. Sabit iskelet yoktur: başlıklar o kategorinin
araştırmasından kurulur ve sahiplik süzgecinden geçer (bkz. `icerik-kurallari.md`, bölüm 3-4;
`scripts/baslik_adaylari.py`). Başlıkların yanına kelime sayısı yazılmaz. Profil `h1_govdede: true` ise ilk satır
`H1: ...` olur.

**İçerik Kurgusu** - şu sırayla:

```
TON: Hitap "{profildeki hitap}"; {profildeki ton}; sıfat yerine özellik.

AÇILIŞ: Başlıksız 1-2 paragraf. İlk cümle ana kelimeyle tanım; ikinci paragraf sitedeki gam (türler, kalıplar, markalar: ...).

H2 · Başlık: Bu bölümde ne anlatılır, hangi kelime karşılanır, hangi biçim (madde / adım / H3 / tablo). [dayanak: 3 rakip + PAA]
H2 · Başlık: ...

SSS: {Ayrı modül / gövdenin sonunda}; gövde kelime sayısına dahil değil.

BİÇİM: {profilden: "•" satırları ve numaralı adımlar (tablo ve liste biçimi yok) / gerçek liste ve tablo}, kalın vurgu, link sayısı.
UZUNLUK: Hedef {profildeki bant ya da "sınır yok"} kelime gövde; rakip medyanı ... kelime (tekrar yok, yeni bilgi).
SSS SAYISI: {profildeki bant} soru (bu içerik için farklı bant istendiyse o bant ve nedeni).
DİKKAT: Yazılmayacaklar, sahiplik uyarıları, mevsimsellik, teyit edilecekler, profil yasakları.
```

Her H2 satırının sonunda başlığın **dayanağı** köşeli parantezle yazılır (`[dayanak: 3 rakip]`, `[dayanak: PAA]`,
`[dayanak: "kışlık" kümesi 2.780]`, `[dayanak: filtre ekseni]`); dayanağı yazılamayan başlık açılmaz. Kurgu
satırları telgraf üslubuyla yazılır ve yaklaşık 30 ekran satırına sığar (Excel satır yüksekliği sınırı 409
punto). Sayfanın canlı kaydından gelen somut adlar (alt kategoriler, markalar, filtre değerleri) ilgili H2
satırına yazılır; içerik ekibi olmayan ürünü uydurmasın.

**Link Verilecek Sayfalar** - numaralı liste, her link iki satır:

```
1. anchor metni : https://...
   H2 · Bölüm adı bölümünde, hangi cümlede.
```

Link sayısı profildeki bantta; seçim ve dağılım `ic-link-kurallari.md`'de.

**Kapsam Dışı Kelimeler (Sahibi Başka Sayfa)** - BAŞKA SAYFA kovasının hacme göre ilk 10-15 kelimesi:

```
kadın şişme mont (6.600) -> /kadin-sisme-mont-x-g3731-c23896555
columbia kadın mont (18.100) -> /columbia-kadin-mont-x-b596-g3731-c23896554
```

Bu sütun brief'in cannibalization sigortasıdır: içerik ekibi hangi kelimeye başlık açmayacağını buradan okur.
Site düzeyinde çakışma tespit edildiyse sütunun sonuna not düşülür.

**SSS'ler** - numaralı soru, altında `Yanıtta:` satırı. Soru sayısı profildeki `sss` bandında (varsayılan 5-7;
Boyner 6-10; `null` ise araştırmada çıkan kadar, en fazla ~12). Kaynak PAA, bilgi niyetli SERP, otomatik
tamamlama ve SERBEST soru kelimeleri; soru uydurulmaz. Brief yalnız soruyu ve yanıtta geçmesi gerekeni verir.

**Yanıt Biçimi** - kategoriler arasında değişmeyen metin (hitap satırı profile göre), olduğu gibi kopyalanır:

```
• Her yanıt {sss_yanit: varsayılan 30-70} kelimedir (en fazla {üst sınır + 10: 80}).
• İlk cümle soruyu doğrudan yanıtlar (evet, hayır ya da net bilgi); gerekçe ikinci cümlede verilir.
• Yanıt kendi başına okunur; "yukarıda belirtildiği gibi" türünde gönderme yapılmaz.
• Kategori adı yanıtta en az bir kez tam haliyle geçer.
• Hitap "{profildeki hitap}"dir; fiyat, indirim ve tarih yazılmaz.
• Gövdedeki cümleler birebir tekrarlanmaz; SSS daha kısa ve doğrudan yazılır.
• Doğrulanamayan bilgi yazılmaz; yanıtlanamayan soru listeden çıkarılır.
```

**Mevcut Durum** - sayfanın bugünkü hâli, 4-6 satır:

```
Sayfa tipi: cinsiyet_kategori · platform: shopify · ürün: 539 (sayfada 520) · canonical: kendisi
Mevcut içerik: yok (ya da: 806 kelime, 11 başlık, 6 link, SSS yok)
Google (mobil, {tarih}): "{ana kelime}" 3. sıra
GSC 90 gün: {click} click · {impression} impression · ort. pozisyon {x}
İlk 5 rakip içerik medyanı: {n} kelime
```

## Briefe girmeyenler

Fiyat aralığı, ürün sayısı hedefi, kampanya bilgisi, KAPSAM DIŞI kovası (rakip perakendeci kelimeleri).
