# Kelime sahipliği ve cannibalization

E-ticaret sitelerinde aynı ürün ailesi için birden çok listeleme sayfası yayında olabilir. `envanter.py ozet`
sitenin tip dağılımını verir:

| Tip | Örnek (Boyner) | Örnek (diğer) |
|---|---|---|
| kategori | `/mont-x-c1531` | `/fondoten/` (Flormar), `/collections/bot` |
| cinsiyet + kategori | `/kadin-mont-x-g3731-c23896554` | `/collections/kadin-bot` (Derimod), `/c/kadin-dis-giyim-691` (Loft) |
| marka | `/columbia-x-b596` | `/marka/nike`, `/collections/vendors?q=X` (Shopify) |
| marka + cinsiyet (+ kategori) | `/columbia-kadin-mont-x-b596-g3731-c23896554` | profildeki desene göre |
| kategori + filtre | `/ruj-x-c12037604?renk=nude` | `?filter.v.price...`, `?renk=` |
| arama sayfası | `/search?q=beyaz+çanta` | `/arama?q=` |
| içerik / blog | `/mag/...`, `/content/...` | `/blog/`, `/blogs/` |

Boyner'de (02.10.2026) yaklaşık 95 bin listeleme adresi vardı; Flormar'da 233 kategori ve özel liste, Derimod'da
yaklaşık 640 koleksiyon. Bir kategori içeriği bu sayfalardan herhangi birinin kelimesine oynarsa iki sayfa aynı
sorguda yarışır. Bu yüzden içerik yazılmadan önce **her kelimenin sahibi belirlenir** ve içerik yalnız kendi
kelimelerini hedefler.

## Adım 1 - Doğru hedef URL

Sitede aynı ada sahip birden fazla sayfa bulunabilir (örnek: Boyner'de "kadın mont" için `c1531` çocuk ağacında
13 ürün, `c200102` ve `c23896554` ana ağaçta; doğru olan Google'da sıralanan `c23896554`). Yanlış adrese yazılan
içerik boşa gider.

**Önce Google, GSC ve SEOmonitor'a bakılır, sonra envantere.** Sitemap bazı sayfaları taşımayabilir (Boyner'de
ana ağaçtaki bazı sayfalar ve cinsiyetsiz marka + kategori sayfaları sitemap'te yoktu). Envanterde aday çıkması
doğru sayfanın orada olduğunu göstermez; sıralanan adres envanterde yoksa üst kategorinin canlı kaydındaki
(`sayfa.py`) alt kategori adresi kullanılır.

Hedef şu dört sinyalle teyit edilir; dördü aynı sayfayı göstermeli:

1. `envanter.py --marka {slug} sahip "{ana kelime}"` - adaylar
2. `sayfa.py --marka {slug} {aday}` - ürün sayısı en yüksek, breadcrumb doğru ağaçta, canonical kendisi, index açık
3. `arastirma.py` SERP çıktısı - Google'da ana kelimede sıralanan site URL'si
4. GSC - ana kelimede en çok tıklama alan sayfa (`get_advanced_search_analytics`, site profildeki `gsc_property`,
   `dimensions: "page"`, `filter_dimension: "query"`, `filter_operator: "equals"`)

Sinyaller ayrışıyorsa içerik yazılmaz; durum kullanıcıya iki URL ve verileriyle bildirilir. Bu site düzeyinde bir
çakışmadır, içerikle çözülmez.

| Ayrışma | Yapılacak |
|---|---|
| Ana kelimede **blog yazısı** ya da **marka içerik / kampanya sayfası** sıralanıyor | İçerik yazılır; çakışma teslim notunda GSC verisiyle bildirilir. Blog ve içerik sayfaları **zayıf sahiptir** (aşağıda). Kampanya / karosel sayfası listeleme değildir: marka sorgusunun esas sayfası her zaman marka listeleme sayfasıdır (örnek: Boyner `/content/{marka}` değil `/{marka}-x-b...`) |
| Cinsiyetli sayfa ile **cinsiyetsiz çatı sayfa** aynı sorguda dönüşümlü sıralanıyor (`/erkek-gomlek` ve `/gomlek`) | Cinsiyetli kelimenin içeriği cinsiyetli sayfaya, cinsiyetsiz kelimenin içeriği ayrıca çatı sayfaya yazılır. Bkz. "Cinsiyetli ve cinsiyetsiz sayfa ailesi" |
| **Eş sesli kategori**: aynı ad iki farklı ürünü karşılıyor (kulaklık: elektronik ve kışlık aksesuar) | Breadcrumb ve ürünlere bakılır; kullanıcının kastettiği ağaçtaki sayfa seçilir, öteki not edilir |

**Cinsiyet + kategori sayfasının canonical'ı kategori sayfasını gösterebilir** (örnek: Boyner
`/kadin-elbise-x-g3731-c23896624` -> `/elbise-x-c23896624`). Bu durumda içerik canonical adrese yazılır ve
kullanıcıya not düşülür. `sayfa.py` canonical karşılaştırmasında şema, www ve sondaki `/` farkını yok sayar.

## Adım 2 - Dört kova

`sahiplik.py` araştırmadaki her kelimeyi şu kovalardan birine koyar:

- **HEDEF:** kök kümesi hedefin kök kümesine eşit ("kadın mont", "mont kadın", "kadın mont modelleri", "bayan mont").
- **BAŞKA SAYFA:** kelimenin kök kümesiyle birebir eşleşen başka bir sayfa var, ya da Google o kelimede sitenin
  başka bir sayfasını ilk 20'de sıralıyor.
- **SERBEST:** hedefin ürün çekirdeğini taşıyan, kendi sayfası olmayan uzun kuyruk ("kışlık kadın mont",
  "su geçirmez kadın mont", "kadın mont beden tablosu").
- **KAPSAM DIŞI:** sitede satılmayan marka / perakendeci (profildeki `rakip_perakendeciler` + pazar yerleri;
  sitede marka sayfası olan marka rakip sayılmaz), başka cinsiyet, başka ürün çekirdeği.

Kök kümesi nedir: kelime ASCII'ye katlanır, dolgu ekleri ("modelleri", "fiyatları", "çeşitleri", markanın kendi
adı) atılır, çoğul ve iyelik ekleri kırpılır, "bayan" -> "kadın" eşlenir. "Kadın Mont Modelleri ve Fiyatları" ile
"mont kadın" aynı kümedir: {kadin, mont}.

Sahip belirlenirken öncelik sırası: (1) hedef sayfanın canlı kaydındaki alt kategori, kardeş kategori ve marka
kırılımı (`--kayit`), (2) Google'da o kelimede ilk 20'de sıralanan site sayfası, (3) envanterde kök kümesi eşleşen
sayfa. Slug'ı SEO ekleriyle şişkin ya da kimlikli sitelerde (Loft `/c/...-690`) canlı kayıttaki görünen ad da
eşlenir.

## Adım 3 - Kovaları elle gözden geçir

Betik kelime biçimine bakar, niyete bakamaz. Tablonun üzerinden bir kez geçilir:

- **SERBEST'teki marka kelimeleri:** betik envanterde marka sayfası olan markaları tanır; olmayanları tanıyamaz.
  Marka sitede satılıyorsa (`envanter.py ara "{marka}"`, canlı kayıttaki markalar) sahibi marka sayfasıdır ->
  BAŞKA SAYFA. Satılmıyorsa KAPSAM DIŞI. Tek markalı sitede (Flormar, Derimod) marka kelimesi markanın kendisidir:
  "flormar fondöten" HEDEF'tir (marka adı dolgu sayılır).
- **SERBEST'teki renk kelimeleri:** "siyah kadın mont" için arama sayfası ya da renk filtresi sayfası var mı
  bakılır. Varsa BAŞKA SAYFA; yoksa metinde renk bir cümlede anılır, H3 açılmaz.
- **BAŞKA SAYFA'da "N aday sayfa" notu:** aynı ada sahip birden çok sayfa var demektir. `--teyit` ile ya da elle
  `sayfa.py` çalıştırılarak ürünü olan, canonical'ı kendisi olan sayfa seçilir.
- **Eş anlamlı sahipler:** "kadın kaban" ile "kadın mont" ayrı sayfalardır ve ayrı kalır; ama "kadın mont kaban"
  sorgusunda Google kaban sayfasını sıralıyorsa bu kelime kabanındır.
- **Arama sayfasına sahip kelime:** arama sayfası sıralanıyorsa kelimenin sahibi odur. Arama sayfaları zayıf
  sahiplerdir; yine de aynı kelimeye H2 açılmaz.
- **Özel / kampanya listeleri** (Flormar `specialpages`: "kalıcı özellikli rujlar", "çok satanlar"): envanterde
  kategori sayılır; kalıcı bir ürün grubunu anlatıyorsa sahiptir, kampanya ise (indirim, burç, gün) sahip
  sayılmaz ve link verilmez.

## Adım 4 - GSC ile çapraz kontrol

SERP haritası tek gün ve tek konum içindir; GSC 3 aylık gerçeği gösterir. İki sorgu yeter:

1. **Hedef sayfa hangi sorgulardan gösterim alıyor?** `get_search_by_page_query` (site profildeki `gsc_property`,
   90 gün). Pozisyonu 5-20 arasında, gösterimi yüksek sorgular içeriğin ilk karşılaması gereken kelimelerdir;
   SERBEST kovasına eklenir.
2. **Ana kelimeyi taşıyan sorgularda hangi sayfalar gösterim alıyor?** `get_advanced_search_analytics`,
   `dimensions: "query,page"`, `filter_dimension: "query"`, `filter_operator: "contains"`,
   `filter_expression: "{ana kelime}"`. Aynı sorguda iki farklı sayfa kayda değer gösterim alıyorsa mevcut
   çakışmadır: brief'in DİKKAT satırına ve teslim notuna yazılır.

GSC'ye erişilemiyorsa bu adım atlanır ve atlandığı kullanıcıya söylenir; SERP haritası tek başına kullanılır.
GSC her zaman OAuth hesabıyla çekilir (ajans portföyündeki property'ler yalnız OAuth ile görünür).

## Sahiplik metne nasıl yansır

| | HEDEF | SERBEST | BAŞKA SAYFA | KAPSAM DIŞI |
|---|---|---|---|---|
| Giriş, kapanış | evet | doğal geçerse | hayır | hayır |
| H2 / H3 | evet | evet | **hayır** | hayır |
| Madde, tanım cümlesi | evet | evet | bir kez, anchor olarak | hayır |
| SSS sorusu | evet | evet | **hayır** | hayır |
| Anchor metni (başka sayfaya) | **hayır** | hayır | evet (sahibine) | hayır |
| Brief sütunu | Main KW / İkincil | İkincil ve Uzun Kuyruk | Kapsam Dışı Kelimeler | yazılmaz |

`icerik_denetim.py --sahiplik` başlıkları, SSS sorularını ve anchor'ları bu tabloyla karşılaştırır.

## Zayıf sahipler ve sınır durumlar

- **Blog ve içerik sayfaları zayıf sahiptir** (envanterde tip `icerik`; profildeki `zayif_sahip_desenleri`).
  Bilgi niyetli kelimeyi ("fondöten nedir", "en iyi fondöten") alabilirler, ama kategori niyetli kelimeyi
  ("fondöten markaları", "fondöten çeşitleri") kategori sayfasından alamazlar. "En iyi ..." listesi blogundur,
  kategori içeriğinde açılmaz. Bu sayfalara link verilmez (kullanıcı isterse istisna).
- **Arama sayfası sahibi olan alt tür** (örnek: Boyner keten gömlek, oduncu gömlek): kendi H3'ünü alabilir, ama
  arama sayfasıyla yarışmayacak ölçüde: tek paragraf (60-100 kelime), türü tanımlar ve hangi ihtiyaca uyduğunu
  söyler. Paragrafın bir cümlesinde arama sayfasına link verilir (anchor: aramanın kendisi). Arama sayfası renk
  sorgusunun sahibiyse başlık açılmaz.
- **Sahibi 8 üründen az olan kelime:** başlık açılmaz, link de verilmez; düz metinle bir kez geçer.
- **Cinsiyetli ve cinsiyetsiz sayfa ailesi.** Giyim, ayakkabı ve aksesuarda aynı ürünün çoğu zaman cinsiyetsiz,
  kadın, erkek ve çocuk sürümleri vardır. Her sürüm kendi kelimesini hedefler: cinsiyetli sayfa cinsiyetli
  kelimeyi (başlıklar ve madde etiketleri cinsiyeti taşır), cinsiyetsiz sayfa cinsiyetsiz kelimeyi ve ürünün genel
  bilgisini. Cinsiyetli içerikte cinsiyetsiz bilgi anlatılabilir ama başlığa çıkmaz. İki sürüm birbirine link
  verebilir.
- **Cinsiyetsiz bilgi sorusu** ("sneaker nasıl temizlenir"): doğal sahibi cinsiyetsiz çatı sayfadır. Çatı sayfada
  içerik yoksa ve yazılması planlanmıyorsa cinsiyetli sayfada karşılanabilir; DİKKAT satırına "çatı sayfaya içerik
  yazılırsa taşınır" notu düşülür.
- **Kardeş kategori:** "tek kişilik nevresim takımı" kelimesinin sahibi tek kişilik nevresim sayfasıdır; betik
  "takım" kelimesi yüzünden eşleştiremeyebilir. Hedefin breadcrumb'ındaki üst kategorinin alt kategorileri
  (Akinon'da `kardes_kategoriler`) elle sahip adayı olarak gözden geçirilir.
- **Alt marka:** bir markanın alt çizgisi ayrı marka sayfasına sahipse (Calvin Klein Jeans), o çizginin kelimeleri
  alt marka sayfasınındır.
- **Marka kelimesi:** kelime sitede sayfası olan bir markanın adını taşıyorsa betik sahibi marka tarafına verir.
  Canlı kırılımdaki adres ile Google'da sıralanan adres farklıysa **Google'da sıralanan adres** sahip ve link
  hedefi sayılır; ikisi de teslim notunda yazılır.

## İçerikle çözülmeyenler

Şunlar içerik işi değildir; fark edilirse yazılmaz, kullanıcıya bildirilir:

- Aynı ada sahip iki sayfanın ikisinin de indekste olması
- Cinsiyet + kategori sayfası ile kategori sayfasının aynı sorguda dönüşümlü sıralanması
- Arama sayfasının kategori sayfasının önünde sıralanması
- Hedef sayfanın canonical'ının başka sayfayı göstermesi ya da noindex olması
