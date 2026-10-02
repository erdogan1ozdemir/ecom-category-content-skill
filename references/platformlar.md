# Platformlar: tespit, listeleme verisinin okunması, bilinen tuzaklar

`scripts/sayfa.py` her okumada platformu sayfa HTML'inden tespit eder ve uygun adaptörü çalıştırır; ardından
HTML sezgisel okuma yalnız boş kalan alanları doldurur. Her alanın kaynağı kayıttaki `yontem` sözlüğündedir
("akinon-json:facets", "html:filtre-blogu" gibi). Bulunamayan alan boş kalır; uydurulmaz.

## Tespit (HTML imzaları)

| Platform | İmza | Adaptör |
|---|---|---|
| Next.js | `__NEXT_DATA__`, `/_next/static` | Boyner yapısı (`props.pageProps.initialState.filters.resolvedPage`) varsa `nextjs-boyner`, yoksa genel JSON taraması |
| Nuxt | `__NUXT__`, `__NUXT_DATA__`, `/_nuxt/` | `__NUXT_DATA__` (devalue dizisi) çözülür; `window.__NUXT__=` JSON değilse (JS fonksiyonu / nesne) HTML'e düşülür |
| Shopify | `cdn.shopify.com`, `Shopify.theme`, `myshopify.com` | `/collections/{handle}.json` + `/collections/{handle}/products.json?limit=250` |
| Akinon | `akinoncloud`, `static_omnishop` | sayfa adresine `?format=json` |
| VTEX | `vteximg`, `vtexassets`, `__RUNTIME__` | `/api/catalog_system/pub/products/search{yol}?map=c,c` ve `/facets/search{yol}` |
| Ticimax | `ticimax` | JSON-LD + HTML sezgisel |
| Magento | `Magento_`, `mage/cookies`, `text/x-magento-init` | JSON-LD + HTML sezgisel |
| Salesforce CC | `demandware`, `dwvar_` | JSON-LD + HTML sezgisel |
| İdeasoft, T-Soft, WooCommerce, Inveon | ad / dosya imzası | JSON-LD + HTML sezgisel |

Tespit edilemeyen ya da alanları boş dönen sayfada `--pw`: yerel Playwright sayfayı render eder, render edilmiş
DOM'a aynı sezgisel okuma uygulanır ve `window.__NUXT__`, `__NEXT_DATA__`, `__INITIAL_STATE__`, `__STATE__`,
`__PRELOADED_STATE__` JSON'u (döngü korumalı) genel anahtar taramasından geçer.

## Alanlar ve okuma yolları

| Alan | Okuma sırası |
|---|---|
| title, description, canonical, meta robots | adaptör JSON'u -> HTML `<title>`, `<meta>`, `<link rel=canonical>`; `X-Robots-Tag` başlığı |
| H1 | adaptör -> ilk `<h1>` |
| breadcrumb | adaptör -> JSON-LD `BreadcrumbList` -> HTML (en çok öğeli, `javascript:` bağlantısız `breadcrumb` listesi) |
| ürün sayısı | adaptör (Shopify `products_count`, Akinon `pagination.total_count`, VTEX `resources` başlığı, Next/Nuxt `totalCount` benzeri anahtar) -> JSON-LD `numberOfItems` -> sayfa metni ("520 ürün listeleniyor", "179 üründen", "408 ürünün 24 tanesi") |
| örnek ürün adları | adaptör -> JSON-LD `ItemList` / `Product` -> HTML ürün kartları (`product-item`, `product-card`...) |
| alt kategoriler | adaptör (Akinon kategori facet'i: seçili kategorinin altındaki derin seçenekler; kardeşler `kardes_kategoriler`) -> filtre bloğundaki linkli "Kategori" grubu -> kategori menüsündeki listeleme linkleri (üst sayfa ve filtreli adresler hariç) -> yolu bu sayfanın altında kalan linkler |
| markalar | adaptör -> filtre bloğundaki "Marka" grubu -> marka sayfasına giden linkler |
| filtreler (facet) | adaptör -> HTML filtre blokları: `filter / facet / refine` sınıflı en içteki kapsayıcılar, grup başlığı nitelikten (`heading`, `data-title`, `data-spec-attr-name`, `aria-label`) ya da yakındaki başlık öğesinden |
| fiyat filtresi, sıralama | adaptör -> "Fiyat" / "Sırala" grubu, `select[name=sort]` |
| mevcut SEO metni | adaptör (Boyner `Content`, Shopify `body_html`) -> `seo / description / aciklama / category-text / collection__description / list__footer-content / rte` sınıflı en uzun blok -> sayfanın en uzun paragraf bloğu (header, footer, nav ve ürün kartı dışında) |

## Platform notları ve tuzaklar

**Next.js (örnek: Boyner).** Her şey `__NEXT_DATA__` JSON'unda: `filters.resolvedPage` (Title, Description, H1,
CanonicalUrl, MetaRobots, PageType, Content), `getProducts` (Breadcrumbs, TotalCount, ürünler), `getFilters`
(alt kategoriler, markalar, ürün çeşidi, renk, materyal...), `getCloudLinking` (link bulutu). Boyner'de cinsiyet +
kategori sayfasının `PageType` değeri `BrandCategoryGender` görünür; marka içermese de. Başka bir Next.js sitesinde
yapı farklıdır; genel JSON taraması ürün listesi (ad + fiyat anahtarlı sözlük dizisi), filtre grupları (ad + değer
dizisi), toplam sayı ve breadcrumb arar. Sonucu `yontem`'den kontrol edin.

**Shopify (örnek: Derimod, Jerf).** Ücretsiz JSON uçları: `/collections/{handle}.json` (title, body_html,
products_count) ve `/collections/{handle}/products.json?limit=250&page=N` (title, vendor, product_type, tags,
options). Betik iki sayfa (500 ürün) okur; `gam_json` ürün tipi, etiket ve seçenek (Renk, Beden) dağılımını verir.
Tuzaklar: `products_count` stokta olmayanları da sayar (Derimod kadın bot: JSON 539, sayfada "520 ürün
listeleniyor"; ikisi de kayıtta). Etiketlerin bir kısmı teknik (`feed-gender-female`, `yuzde_20`,
`markasizayakkabi`); süzülür ama içerik malzemesi olarak etiket değil `product_type` ve filtre değerleri esastır.
Mağaza tek markalıysa "Marka" yalnız kendisidir. `/en/` gibi dil önekli adresler envanterde `diger` sayılır.
Alan adı www'siz olabilir (derimod.com.tr); kök adres ana sayfanın yönlendirmesinden bulunur.

**Akinon (örnek: Flormar, SPX).** Sayfa adresine `?format=json` eklenince `pagination.total_count`, `facets`
(her facet `data.choices[]`: label, quantity, url, depth, is_selected), `sorters`, `products`, `category` döner.
Kategori facet'i ağaçtır: seçili kategoriden sonraki daha derin seçenekler alt kategori, aynı derinliktekiler
kardeş kategoridir. `in_stock` gibi teknik facet'ler atlanır. Sitemap `sitemap-categories`, `sitemap-products`,
`sitemap-flatpages`, `sitemap-specialpages` olarak ayrılır; adresler düzdür (`/fondoten/`, ürünler sonunda 13
haneli barkodla), sınıflama sitemap adından gelir. `specialpages` kampanya ve koleksiyon listeleridir: envanterde
`kategori` sayılır ama brief Excel'ine alınmaları `kur_kaynaklar` ile sınırlanabilir; kampanya sayfasına link
verilmez. SEO metni HTML'de `list__footer-content` içindedir.

**VTEX.** Katalog uçları denenir; çalışmazsa HTML'e düşülür. Gerçek bir VTEX sitesinde henüz denenmedi: ilk
VTEX markasında sonuç `yontem`'den kontrol edilip bu not güncellenmelidir. (Loft'un VTEX olduğu düşünülüyordu;
loft.com.tr incelendiğinde mncdn + `InvUtility.js` imzalı .NET tabanlı bir altyapı çıktı, HTML sezgisel okunuyor.)

**Nuxt (örnek: Tchibo).** Tchibo'da `window.__NUXT__` bir JS nesnesi (mikro ön yüzler, `__NUXT__["category-ui"]`),
JSON değil; render sonrası da okunabilir durum bulunamadı. Ürün sayısı sayfa metninden ("408 ürünün 24 tanesini
gördünüz"), breadcrumb ve ürün adları JSON-LD'den, alt kategoriler menüden gelir; filtreler ve SEO metni boş
kalabilir (filtre paneli tıklamayla açılıyor). Menü linkleri kardeş kategorileri de içerebilir; alt / kardeş
ayrımı breadcrumb ve yol ile elle yapılır.

**Inveon / özel .NET (örnek: Loft).** Kategori adresi `/c/{slug}-{kimlik}`; slug SEO ekleriyle şişkin olabilir
(`kadin-eldiven-modelleri-ve-fiyatlari-kadin-kislik-eldiven-690`), kelime kümesi bu yüzden gürültülüdür: sahiplikte
canlı kayıttaki görünen ad da kullanılır. Filtre grupları `filter-container group-container-{Ad}`, başlık
`data-spec-attr-name`; "Kategori" filtresi linksiz checkbox'tır (alt kategori değil filtre olarak kaydedilir).

**Ticimax, Magento, SFCC, diğerleri.** JSON-LD ve HTML sezgisel. Filtre bloğu bulunamazsa `--pw`; yine boşsa
filtre değerleri kullanıcıya sorulur ya da sayfadaki ürün adlarından (örnek ürünler) çıkarılır ve teslim notunda
"filtre verisi okunamadı" yazılır.

**Cloudflare / bot koruması (örnek: Sephora TR).** Doğrudan istek "Just a moment..." döner. `sayfa.py --pw`
denenir; yine gelmiyorsa o site bırakılır, kullanıcıya söylenir ve gerekirse canlı kayıt alanları (alt
kategoriler, filtreler) kullanıcıdan istenir. İstekler arasında en az 1,2 saniye beklenir; art arda yoğun istek
atılmaz.

## Yeni platformda yapılacaklar

1. `sayfa.py --domain {site} {kategori URL}` -> "Platform", "adaptör" ve "Boş kalan alanlar".
2. Boş alan varsa `--pw`; yine boşsa sayfa kaynağında JSON uç (`?format=json`, `/api/...`, `.json`) ya da gömülü
   durum aranır.
3. `envanter.py ... yenile` -> `belirsiz` -> `url_desenleri`.
4. Bulgular bu dosyaya "Platform notları" altında eklenir (ilk VTEX, Ticimax, Magento markasında).
