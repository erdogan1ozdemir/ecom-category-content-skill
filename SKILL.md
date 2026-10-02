---
name: ecom-kategori-icerik
description: Herhangi bir e-ticaret sitesinin kategori ve marka (listeleme) sayfaları için içerik briefi ve SEO + GEO uyumlu kategori içeriği üretir; marka dilini siteden çıkarıp ekibe doğrulatır ve markalar/{marka}/profil.md dosyasına yazar. Hedef kategoride ilk 5 SERP'i ve rakip içeriklerini inceler, kelime kümesini ve soru kalıplarını çıkarır, sitenin sitemap envanterine karşı kelime sahipliği (cannibalization) tablosu kurar, 5-8 çapraz iç link seçer; başlık iskeleti o kategorinin araştırmasından kurulur, SSS yanıtları answer-first yazılır. Çıktılar - marka başına sayfa tipine göre sekmeli brief Excel'i ve içerik başına Word dosyası. Şu durumlarda mutlaka kullan - kullanıcı bir e-ticaret kategori URL'si ya da kategori adı verip "kategori içeriği yaz", "kategori SEO metni", "kategori açıklaması", "kategori briefi", "listeleme sayfası içeriği", "e-ticaret kategori sayfası", "SSS yaz", "içeriği revize et" dediğinde · Özdilekteyim, Flormar, Turkcell Pasaj, VitrA, Sephora, Mudo, Derimod, Dagi, Jerf, Loft, SPX, Suud Collection, Tchibo, Kiko Milano, ADL, Koçak, MM Kozmetik, Love My Body, Vilebrequin, Ecovacs, Miele gibi bir marka için kategori metni, uzun kuyruk kelime, alt başlık planı, iç link planı ya da cannibalization kontrolü istendiğinde · "bu kelimenin sahibi hangi sayfa" diye sorulduğunda · içeriği zayıf kategoriler aranırken · yeni bir marka için kategori içerik dili / marka profili kurulurken · kullanıcı yalnız bir listeleme adresi yapıştırıp içerik beklediğinde. Boyner istenirse boyner-kategori-brief-icerik skill'i kullanılır (Boyner profili burada yalnız örnek olarak durur). Teknik SEO audit, müşteriye giden rapor/sunum ve blog yazısı bu skill'in işi değildir.
---

# E-ticaret Kategori Sayfası: Brief ve İçerik

Bu skill bir e-ticaret listeleme sayfası (kategori, cinsiyet + kategori, marka, marka + kategori) için **iki
çıktı** üretir:

1. **Brief satırı** - marka başına ortak Excel'de o sayfanın satırı. Excel, içerik yazılacak tüm hedef
   sayfaları sayfa tipine göre sekmelerde taşır (Kategori, Kadın, Erkek, Çocuk, Bebek, Marka; cinsiyetli
   kategorisi olmayan sitede yalnız Kategori ve Marka). Bekleyenler `Bekliyor`, hazırlananlar `Hazır`.
2. **Kategori içeriği** - Word dosyası. Belge adı `{slug}: {tam URL}`; dosya sisteminde `:` ve `/` yerine
   görünüşü aynı `∶` ve `∕` karakterleri kullanılır.

HTML çıktısı varsayılan akışta yoktur; `scripts/cms_html.py` yalnız kullanıcı isterse çalıştırılır. Kullanıcı yalnız
"brief" derse içerik yazılmaz; yalnız "içerik" derse brief satırı atlanır ama araştırma ve sahiplik fazları
yine yürütülür, çünkü içerik onlara dayanır.

**Boyner için bu skill değil `boyner-kategori-brief-icerik` kullanılır.** `markalar/boyner/` profili burada
genel yapının tam doldurulmuş örneğidir.

## İşin özü: metodoloji sabit, biçim ve dil markaya göre

Sabit kalanlar (her markada aynı, kullanıcı kararı):

- **Her kelimenin tek bir sahibi vardır.** İçerik yalnız kendi sayfasının kelimelerini hedefler; başka sayfanın
  kelimesi başlığa çıkmaz, o sayfaya link olur.
- **İçerik sayfadaki gerçek ürün gamına dayanır.** Türler, markalar, kalıplar ve malzemeler sayfanın canlı
  filtre verisinden gelir; satılmayan şey yazılmaz.
- **Başlık iskeleti sabit değildir.** Her kategorinin başlıkları kendi araştırmasından çıkar: ilk 5 rakibin
  başlıkları, PAA, uzun kuyruk kelime kümeleri ve arama eğilimi.
- İç link kuralları, net fiyat / yıl / ürün sayısı yazmama, tutarlılık kuralları, cinsiyetli / cinsiyetsiz sayfa
  ailesi, zayıf sahipler, answer-first SSS.

Markaya göre değişenler **marka profilinde** durur ve ilk kurulumda ekibe sorulur: hitap (siz / sen), ton,
yasak ve tercih edilen kelimeler, CMS biçimi (tablo, liste, HTML, H1 gövdede mi, SSS ayrı modül mü), uzunluk
bandı (varsayılan 1.500-2.500), link sayısı (varsayılan 5-8), ticari dil, "-mektedir" ve yumuşatma tercihi,
"kategori" kelimesi yasağı gibi marka özel kalıplar.

## Marka profili

```
markalar/{marka-slug}/profil.md    okunur kurallar: ton, hitap, yaz / yazma tablosu, CMS biçimi, revize geçmişi
markalar/{marka-slug}/ayar.json    betikler için: domain, pazar, URL desenleri, biçim bayrakları, bantlar
```

Profil depoya girer, ekip ortak kullanır. Her işte **önce profil okunur** (`profil.md` baştan sona); yoksa Faz 0
yürütülür. Şablon `markalar/_sablon/`, tam örnek `markalar/boyner/`, nasıl çıkarılacağı
`references/marka-profili.md`'de.

## Çalışma akışı

Betikler `scripts/` altındadır ve her biri `--marka {slug}` (profil varken) ya da `--domain {alan adı}` alır.
Ara dosyalar için oturumun geçici dizini kullanılır (aşağıda `$T`); `S=~/.claude/skills/ecom-kategori-icerik/scripts`.

### Başlangıç kontrolleri (her çalıştırmada, profil olsa da)

Profil ve önbellek eski bir çalıştırmadan kalmış olabilir; site o arada değişmiş olabilir. Bu yüzden her
çalıştırma iki adımla başlar.

1. **Maliyet tahmini ve onay.** Talep edilen içerik sayısı belli olunca, araştırmaya ve ücretli çağrıya geçmeden:
   ```bash
   python3 $S/maliyet.py --marka {slug} --adet {N} [--kurulum] [--ahrefs-satir 300]
   ```
   Betik toplam token aralığını, süreyi (en çok iki paralel ajan), DataForSEO tutarını ve canlı bakiyeyi,
   istenirse Ahrefs birimini yazar. Ahrefs kullanılacaksa kalan birim `subscription-info-limits-and-usage` ile
   okunup tahmine eklenir. Özet kullanıcıya gösterilir ve **onay alınmadan iş başlamaz** (AskUserQuestion:
   "Başla" / "Daha az içerikle başla" / "Vazgeç"). Tahmin revizesiz ilk üretimi kapsar: skill kendi başına
   revize ya da puanlama turu yapmaz; denetimdeki bulguların düzeltilmesi tahmine dahildir. Kullanıcı revize
   isteyeceğini söylerse `--revize 1` eklenir. Bakiye üst tahminin altındaysa bu açıkça söylenir.
2. **Envanter tazeleme.** `python3 $S/envanter.py --marka {slug} yenile`: sitemap'ler yeniden okunur, önceki
   envanterle fark (çıkan / eklenen sayfa) yazılır. Ardından `python3 $S/brief_satiri.py --marka {slug} --ozet`:
   brief Excel'inde adresi artık sitemap'te olmayan satırlar listelenir. Çıkan bir sayfa hedef ise yazılmadan
   kullanıcıya sorulur (kaldırılmış, yönlendirilmiş ya da adı değişmiş olabilir); eklenen sayfalar sahiplik
   tablosunda yeni sahip olarak görünür. Aynı oturumda ikinci bir partide tazeleme tekrarlanmaz.

### Faz 0 - Marka kurulumu (profil yoksa)

1. `markalar/` altında markanın klasörü var mı bakılır. Varsa `profil.md` okunur, Faz 1'e geçilir.
2. Yoksa kullanıcıya (AskUserQuestion) sorulur: alan adı, marka adının yazımı, hedef kategoriler (tek URL,
   URL listesi ya da "içeriği zayıf kategorileri bul"), çıktı klasörü (varsayılan
   `~/Desktop/Claude Projects/{Marka}/Kategori İçerik/`).
3. `markalar/_sablon/` klasörü `markalar/{slug}/` olarak kopyalanır; `ayar.json`'a `domain`, `marka_adi`,
   `sektor`, `cikti_klasoru` yazılır. `gsc` MCP `list_properties` ve SEOmonitor `seomonitor_get_tracked_campaigns`
   ile `gsc_property` ve `seomonitor_campaign_id` bulunur.
4. **Platform tespiti:** `python3 $S/sayfa.py --marka {slug} {bir kategori URL}` - "Platform" ve "adaptör"
   satırları; okunamayan alan varsa `--pw`. Platformlara göre okuma: `references/platformlar.md`.
5. **Envanter:** `python3 $S/envanter.py --marka {slug} yenile` -> tip dağılımı. "Belirsiz" adres varsa
   `envanter.py ... belirsiz` örnekleri gösterir; desenler kullanıcıya gösterilip `ayar.json` ->
   `url_desenleri`'ne yazılır, envanter yenilenir. Ürün adresleri sayılır ama hedef olmaz.
6. **Marka dili:** `python3 $S/marka_dili.py --marka {slug} --cikti $T/dil.json`. Öncelik: kategori metinleri,
   ürün açıklamaları, blog. "yeterli: HAYIR" derse marka ve sektöre uygun rakiplerin dilinden profil türetilir
   (`references/marka-profili.md`, "Rakip yedeği").
7. **Profil taslağı** `profil.md` şablonuyla yazılır; dil ölçümü ve 2-3 örnek paragraf dayanak olarak eklenir.
   Sektör notları: `references/sektorler.md`.
8. **Ekibe doğrulama** (AskUserQuestion, en çok dört soru bir arada, üç tur): hitap, genel ton, yasak ve tercih
   edilen kelimeler, ticari dil · CMS biçimi (tablo / liste / HTML / H1 / SSS modülü), link bandı, marka kalıpları ·
   **gövde uzunluğu** (seçenekli: ortalama 1.500-2.500 önerilen, 1.500-2.000, 1.250-1.750, 750-1.250, sınır yok = uzunluğu kategorinin ihtiyacı belirler, en az 750 en fazla 3.000 kelime)
   ve **SSS soru sayısı** (5-7 önerilen, 3-4, 8-10, araştırmada ne kadar çıkarsa en fazla ~12). Soru listesi ve
   `ayar.json` karşılıkları `references/marka-profili.md`, "Kurulum soruları".
9. Yanıtlar `profil.md` ve `ayar.json`'a işlenir; teyit tarihi ve teyit eden yazılır. Profil değişikliği depoya
   doğrudan gitmez: ekip üyesi değişen dosyaları depo sahibine iletir, depo sahibi birleştirir
   (`references/marka-profili.md`, "Profil güncelleme akışı"). Teslim notunda değişen alanlar listelenir.

### Faz 1 - Hedef sayfayı teyit et ve canlı kaydı oku

Kullanıcı URL verdiyse onu, kategori adı verdiyse adayları bul. **Önce GSC ve SEOmonitor'da** ana kelimede
sıralanan site adresine bakılır, sonra envantere:

```bash
python3 $S/envanter.py --marka {slug} sahip "kadın mont"
python3 $S/sayfa.py --marka {slug} {URL} --gam --cikti $T/kayit.json     # --gam: kırılımların ürün sayısı ve örnekleri
```

Hedef dört sinyalle teyit edilir (envanter adayı, canlı kayıt: ürün sayısı + breadcrumb + canonical + index,
Google'da sıralanan URL, GSC); ayrıntı `references/sahiplik-ve-cannibalization.md` Adım 1. Canonical başka
sayfayı gösteriyorsa, sayfa noindex ise ya da sinyaller ayrışıyorsa yazmadan önce kullanıcıya sorulur.

`sayfa.py` kaydı içeriğin gerçeklik zeminidir: alt kategoriler, markalar, filtre değerleri, mevcut içerik ve
her alanın hangi yöntemle okunduğu (`yontem`). Boş kalan alan uydurulmaz; gerekirse `--pw` ile yeniden okunur ya da
kullanıcıya söylenir. Mevcut içerik `--icerik` ile okunur; işe yarar bilgi alınır, yapısı alınmaz.

### Faz 2 - Araştır

```bash
python3 $S/arastirma.py --marka {slug} "kadın mont" --url {URL} --cikti $T/arastirma.json [--ek "kadın kaban"] [--harita $T/harita.json]
```

Tek çağrıda: SERP (profildeki pazar/dil, mobil) ilk 10 ve sitenin sıralanan sayfası · bilgi niyetli SERP
("... nasıl seçilir") ile PAA ve AI Overview · kelime kümesi (hacim, zirve ayı, son üç ay) · otomatik tamamlama ·
ilk 5 rakibin içerik iskeleti · ana kelimeyi taşıyan sorgularda sitenin sıralanan sayfaları.

**Veri kaynağı sırası** (kullanıcı kararı):

1. **GSC** (OAuth, ücretsiz; `ayar.json` -> `gsc_property`, 90 gün): hedef sayfanın sorguları
   (`get_search_by_page_query`) ve ana kelimeyi taşıyan sorgularda sayfa dağılımı
   (`get_advanced_search_analytics`, `dimensions: "query,page"`). **SEOmonitor** (ücretsiz; markanın kampanyası
   varsa `seomonitor_campaign_id`): takipli kelimelerin sıralanan sayfaları. İkisinden derlenen liste
   `[{"kelime","hacim","sira","url"}]` olarak `--harita` ile verilirse DataForSEO haritası çekilmez.
2. **DataForSEO** (ana ücretli kaynak, ucuz; 30 gün önbellek): `arastirma.py` varsayılanı.
3. **Ahrefs** yalnız kullanıcı isterse. Önce `subscription-info-limits-and-usage`: kalan birim ≥ 0,75 × (limit
   × aya kalan gün / 30) **ve** ≥ 100 bin değilse atlanır ve kullanıcıya sorulur. Yalnız
   `keyword,best_position,best_position_url` sütunları istenir.

GSC'ye erişilemezse adım atlanır ve söylenir. Rakip okuma zinciri betikte otomatiktir: curl -> r.jina.ai ->
yerel Playwright (`pw_oku.py`) -> DataForSEO ayrıştırma; MCP Playwright yalnız nadir elle. Ayrıntı:
`references/arastirma-ve-dogrulama.md`.

### Faz 3 - Kelime sahipliğini çıkar

```bash
python3 $S/sahiplik.py --marka {slug} --arastirma $T/arastirma.json --url {URL} --kayit $T/kayit.json --teyit --cikti $T/sahiplik.json
```

Her kelime dört kovadan birine düşer: **HEDEF**, **SERBEST** (kendi sayfası olmayan uzun kuyruk), **BAŞKA SAYFA**
(sahibi belli; hedeflenmez, linklenir), **KAPSAM DIŞI**. Betik biçime bakar, niyete bakamaz: tablo bir kez elle
gözden geçirilir (`references/sahiplik-ve-cannibalization.md`). Site düzeyinde çakışma içerikle çözülmez; teslim
notunda bildirilir.

### Faz 4 - Başlık iskeletini ve briefi kur

```bash
python3 $S/baslik_adaylari.py --marka {slug} --arastirma $T/arastirma.json --sahiplik $T/sahiplik.json --kayit $T/kayit.json
python3 $S/brief_satiri.py --marka {slug} --kur [--hedefler $T/hedefler.txt]      # ilk kez: Excel ve Bekliyor satırları
python3 $S/brief_satiri.py --marka {slug} --json $T/satir.json                      # satırı doldurur, Hazır yapar
```

Başlık adayları dört kaynaktan gelir ve sahiplik süzgecinden geçer (`[SAHİPLİ]` aday başlık olamaz). İskelet
kategorinin doğasına göre kurulur: `references/icerik-kurallari.md` bölüm 3-4. Sütunların biçimi
`references/brief-kurallari.md`'de. Özet: Main KW 12 aylık ortalamayla · ikincil kelimeler yalnız HEDEF ve
SERBEST'ten · her H2'nin dayanağı kurguda (`[dayanak: 3 rakip + PAA]`) · 5-8 link (profildeki bant) rolleri ve
cümleleriyle · Kapsam Dışı sütunu BAŞKA SAYFA kovasından · SSS sayısı profildeki bantta (PAA ve otomatik
tamamlamadan). Kurgu'nun TON, UZUNLUK ve SSS satırları profilden yazılır.

### Faz 5 - İçeriği yaz

Yazmadan önce **`markalar/{slug}/profil.md`** ve **`references/icerik-kurallari.md`** okunur (araştırma uzun
sürdüyse yeniden). Profil biçimi belirler; kurallar dosyası metodolojiyi:

- Hitap, ton, kipler, ticari dil, yasak / tercih kalıpları **profilden**. Ses bilgili bir mağaza danışmanınınki:
  sıfat yerine özellik, süs yerine karar verdiren bilgi.
- Gövde **başlıksız 1-2 paragraflık girişle** açılır (profil `h1_govdede: true` ise H1 + giriş); ilk cümle ana
  kelimeyle tanım, ikinci paragraf sitedeki gam. Ardından brief'teki iskelet; H3 yalnız H2 altında.
- **Her H2'nin ilk cümlesi başlığın sorusunu doğrudan yanıtlar**; bölüm kendi başına okunur.
- **Uzunluk** profildeki bant (`uzunluk`; varsayılan 1.500-2.500 kelime gövde, `null` ise uzunluğu kategorinin ihtiyacı ve rakip
  medyanı belirler, en az 750 en fazla 3.000 kelime; dolgu da kesme de yapılmaz); tekrarla değil daha fazla bilgiyle.
- **Başlıklar arama diliyle** yazılır ve ana kelimeyi ya da ürün adını taşır.
- **Net fiyat, fiyat aralığı, indirim oranı, kampanya adı, yıl, "bu sezon" ve ürün sayısı yazılmaz.**
- **Tablo ve liste** profile göre: CMS kabul etmiyorsa sayılabilir şeyler `mad` ("•  " düz satır), adımlar `li`
  ("1. " düz satır); kabul ediyorsa aynı JSON tipleri gerçek liste olarak, `tablo` tablo olarak basılır.
- **BAŞKA SAYFA kelimesi başlık ya da SSS olmaz;** bir kez, tanım cümlesi içinde ve sahibine link veren anchor
  olarak geçer. **İç link metnin içinden çıkar:** anchor silinince cümle anlamlı kalır.
- **İçerik mevcut ürün gamını anlatır;** taslak bitince canlı kayıt bir kez daha okunur.
- **SSS soru sayısı** profildeki bant (`sss`; varsayılan 5-7, Boyner 6-10); **yanıtlar** `sss_yanit` bandında
  (varsayılan 30-70 kelime, en fazla 80), ilk cümle doğrudan yanıt.

İçerik JSON'u (`scripts/icerik_docx.py` başında): `kategori`, `url`, `main_kw`, `linkler`
(`{"LINK1": [anchor, url]}`), `govde` (`["p" | "H2" | "H3" | "mad" | "li" | "tablo", içerik]`; köprüler
`[LINK1]`, vurgu `**kalın**`), `sss` (`[soru, yanıt]`); isteğe bağlı `uzunluk` ve `sss_sayisi` (bu içerik için
profil bandını geçersiz kılar). Örnek: `examples/boyner/`.

### Faz 6 - Denetle, üret, teslim et

```bash
python3 $S/icerik_denetim.py --marka {slug} --json $T/icerik.json --sahiplik $T/sahiplik.json --arastirma $T/arastirma.json --kayit $T/kayit.json --canli
python3 $S/icerik_docx.py --marka {slug} --json $T/icerik.json       # -> cikti_klasoru/"{slug}: {URL}.docx"
```

Denetim kuralları profile bağlıdır (hitap, tablo, yasak kalıplar, kategori kelimesi, parça, uzunluk / SSS /
link bantları, rakip listesi). Kullanıcı tek bir içerik için farklı bant isterse profil değişmez: `--uzunluk
750-1250` ya da `--uzunluk yok`, `--sss 3-4` ya da `--sss yok` (veya içerik JSON'unda `uzunluk`, `sss_sayisi`).
`--canli` zorunludur: her link hedefi o anda okunur. 404 / 410 dönen, noindex olan, ürünü kalmayan ya da
canonical'ı başka sayfaya giden hedef envanterden yenisiyle değiştirilir; 301 / 302 dönen hedefin linki son
adrese çevrilir (final adres de aynı kontrolden geçer). Cloudflare yüzünden okunamayan link teslim notunda
"elle bakılmalı" olarak yazılır. Bulgu varsa çıktı üretilmez; önce metin düzeltilir. `NOT:` satırları okunarak karar verilir. Ardından
`references/kontrol-listesi.md` okuma maddeleri geçilir ve metin bir kez baştan sona okunur.

**Bağımsız puanlama turu yoktur** (kullanıcı kararı). Kullanıcı açıkça isterse ("puanla", "değerlendir") tek
tur `seo-content` ajanı çalıştırılır.

### Pilot kapısı (her markanın ilk içeriği)

Bir marka için ilk çalıştırmada **tek içerik** üretilir ve kullanıcıya gösterilir. Kullanıcının her revizesi
`profil.md` -> "Revize geçmişi"ne **kural olarak** yazılır (tarih, ne istendi, kural cümlesi, gerekiyorsa yaz /
yazma örneği); `ayar.json` bayrağına dönüşebilenler (hitap, tablo, yasak kalıp, bant) oraya da işlenir. Pilot
onaylanmadan kalan kategoriler üretilmez. Onaydan sonra profildeki "Pilot" satırı `onaylandı` yapılır.

### Toplu üretim

Onaydan sonra kalan kategoriler üretilir. **Aynı anda en çok iki ajan** çalışır; çok sayıda içerik üç dört
kişilik gruplara bölünür, gruplar arasında beklenir. Her ajana profil yolu, hedef URL, çıktı klasörü ve bu skill
verilir. Ajan kesilirse kaldığı yerden sürdürülür; yeni ajan açılıp işe baştan başlanmaz. Kardeş kategoriler
(kadın mont / kadın kaban) aynı partideyse önce hepsinin sahiplik tablosu çıkarılır, sonra yazılır.

İçeriği zayıf kategori aranıyorsa: GSC'den gösterimi yüksek kategori sayfaları alınır, `sayfa.py` ile içerik
durumu okunur. Boş ya da kısa içerikli, ürünü çok ve pozisyonu 4-15 arasında olan sayfalar ilk adaylardır.

### Teslim notu

Çıktılar profildeki çıktı klasörüne kaydedilir. Notta dört şey söylenir: hangi bilgi hangi kaynaktan alındı ·
ne yazılmadı ve neden (sahibi başka sayfa olan kelimeler, teyit edilemeyen bilgiler, okunamayan alanlar) ·
kullanıcı kararı bekleyenler (canonical, CMS'te SSS modülü, profil soruları) · site düzeyi çakışmalar. Ayrıca
başlangıçtaki tahminle gerçekleşen kullanım yan yana verilir (DataForSEO bakiyesinin önceki ve sonraki değeri,
Ahrefs kullanıldıysa birim), envanter farkından etkilenen ve değiştirilen linkler listelenir.

## Değişmeyen kurallar

- **Hedef URL teyit edilmeden içerik yazılmaz.**
- **Bir kelime, bir sahip.** Sahibi başka sayfa olan kelime için başlık, SSS ya da ayrı paragraf açılmaz.
- **Bu sayfanın ana kelimesi başka sayfaya anchor olmaz;** sayfa kendine link vermez; aynı hedefe iki kez link
  verilmez; link sayısı profildeki bantta (varsayılan 5-8).
- **Her link hedefi canlı, index'e açık, canonical ve ürünlü listeleme sayfasıdır.** Blog, içerik / kampanya,
  outlet ve ürün sayfalarına link verilmez (profildeki `link_yasak_desenleri`). Arama sayfasına yalnız o arama
  için açılmış kısa H3'ten link verilir.
- **Cinsiyetli sayfa cinsiyetli kelimeyi, cinsiyetsiz çatı sayfa cinsiyetsiz kelimeyi hedefler.** Marka
  sorgusunun esas sayfası marka listeleme sayfasıdır.
- **Anchor, hedefin sıralandığı aramaya göre yazılır,** sayfanın adına göre değil.
- **Hitap profildeki gibidir** (siz ya da sen); baştan sona tek hitap.
- **Net fiyat, fiyat aralığı, indirim oranı, kampanya adı, yıl, "bu sezon" ve ürün sayısı yazılmaz** ("uygun",
  "ekonomik" gibi niteleyiciler ve rakamsız "Fiyatları" başlığı, profil izin veriyorsa serbesttir).
- **Canlı kayıtta olmayan ürün bilgisi yazılmaz.** Sitede satılmayan marka, filtrelenmeyen tür metne girmez.
  Rakip perakendeci adı geçmez.
- **Doğrulanamayan sayı ve iddia yazılmaz.** Kozmetikte sağlık iddiası kurulmaz (`references/sektorler.md`).
- **Site hizmetleri** (teslimat, iade, mağazadan teslim) yalnız sitenin kendi sayfasından teyit edilerek ve
  süre / tutar rakamı verilmeden anılır.
- **Sabit başlık şablonu kullanılmaz;** her başlığın araştırmada dayanağı vardır ve başlık aranabilir ifadedir.
- **Mevcut içeriklerin yapısı örnek alınmaz;** yalnız profilde teyit edilen dil sürdürülür. Profilin "Yapı"
  bölümü sitedeki yapıyı açıkça benimsediyse (Flormar) o bölümdeki bölüm tipleri kullanılır; başlıklar yine
  o kategorinin araştırmasından kurulur.
- İçerik Dili Rehberi bu çıktıya uygulanmaz (tüketiciye dönük metin). Uzun tire, emoji ve marka sembolü yine de
  kullanılmaz.

## Site istekleri ve maliyet

Betikler aynı alan adına istekler arasında en az 1,2 saniye bekler (`ECOM_BEKLE` ile artırılabilir). Cloudflare
doğrulaması gelirse betik bekleyip bir kez daha dener; yine gelirse o site bırakılır, `--pw` denenir ya da
birkaç dakika ara verilir ve durum teslim notunda yazılır. DataForSEO sonuçları 30 gün önbellektedir
(`~/.cache/ecom-kategori-icerik/dfs/`, `--yeni` ile atlanır); kardeş kategorilerde ortak sorgular önbellekten
gelir. Kimlik `~/.claude.json` içindeki `dfs-mcp` yapılandırmasından okunur. Python paketleri: `openpyxl`,
`python-docx`, `playwright` (yalnız `--pw` ve rakip okuma yedeği). İstekler `curl` ile atılır.

## Referanslar

| Dosya | Ne zaman okunur |
|---|---|
| `markalar/{slug}/profil.md` | Her işte, ilk iş. Hitap, ton, yaz / yazma, CMS biçimi, revize geçmişi. |
| `references/marka-profili.md` | Faz 0'da ve pilot revizelerinde. Profil çıkarma, rakip yedeği, kurulum soruları, şablon alanları. |
| `references/platformlar.md` | Faz 0'da ve `sayfa.py` alan boş döndüğünde. Platform imzaları, adaptörler, tuzaklar. |
| `references/sektorler.md` | Profil yazarken ve iskelet kurarken. Sektöre göre eksenler ve dikkat noktaları. |
| `references/sahiplik-ve-cannibalization.md` | Faz 1 ve 3'te. Hedef teyidi, dört kova, elle gözden geçirme, GSC çapraz kontrolü. |
| `references/arastirma-ve-dogrulama.md` | Faz 2'de. Kaynak sırası, ilk 5 SERP okuma, mevsimsellik, tuzaklar. |
| `references/brief-kurallari.md` | Faz 4'te, brief satırını kurarken. |
| `references/icerik-kurallari.md` | Faz 4'te iskeleti kurarken (bölüm 3-4) ve Faz 5'te yazmadan önce. |
| `references/ic-link-kurallari.md` | Link seçerken ve yerleştirirken. |
| `references/marka-sayfasi.md` | Hedef bir marka sayfasıysa. |
| `references/kontrol-listesi.md` | Faz 6'da, teslimden önce. |
| `examples/boyner/` | Örnek brief satırı ve içerik JSON'u (Boyner profiliyle); biçim referansı. |
