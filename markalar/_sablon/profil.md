# {Marka adı} · kategori içerik profili

> Şablon. `markalar/{marka-slug}/profil.md` olarak kopyalanır ve doldurulur. Nasıl çıkarılacağı:
> `references/marka-profili.md`. Doldurulmamış alan `-` kalır; uydurulmaz. Betik ayarları `ayar.json`'da.

## Künye

| Alan | Değer |
|---|---|
| Marka adı ve yazımı | {ör. VitrA; "Vitra" ve "VITRA" yazılmaz} |
| Alan adı | {ör. vitra.com.tr} |
| Sektör | {giyim / kozmetik / ev-banyo / elektronik-telekom / gıda / mobilya ...} (bkz. `references/sektorler.md`) |
| Pazar ve dil | Türkiye · Türkçe |
| Platform | {nextjs / shopify / akinon / vtex / ticimax / diğer} (bkz. `references/platformlar.md`) |
| GSC property | {sc-domain:...} |
| SEOmonitor kampanyası | {id ya da -} |

## Hitap ve ton

- **Hitap:** {siz / sen}. {Birinci çoğul: yalnız liste girişlerinde ("sizin için grupladık") / serbest / yok.}
- **Ton:** {3-5 sıfat: ör. bilgili, sade, sıcak, teknik}.
- **Ses:** {ör. bilgili bir mağaza danışmanı: sıfat yerine özellik, süs yerine karar verdiren bilgi.}

Örnek cümleler:

| Yaz | Yazma |
|---|---|
| {markanın dilinde bir tanım cümlesi} | {aynı bilginin kaçınılan biçimi} |
| {bir öneri cümlesi} | {} |

## Cümle yapısı

- Cümle uzunluğu: {ör. 12-18 kelime; uzun cümle noktalı virgülle uzatılmaz, bölünür}.
- Kipler: {ör. tanım geniş zaman, katalog şimdiki zaman, öneri "-ebilirsiniz"; "-mektedir" serbest / az / kaçınılır}.
- Yumuşatma: {ör. kural ve tavsiye cümleleri "genellikle", "-abilir", "önerilir" ile}.

## Yaz / yazma tablosu

| Yazma | Yaz | Neden |
|---|---|---|
| {kategoride} | {"{ürün} ürün grubu", "{Marka} {ürün} modelleri arasında"} | {kullanıcı kararı / pilot revizesi} |
| {} | {} | {} |

## Ürün adlandırma

- Ürün ailesi sözcüğü: {giysi / makyaj ürünü / cihaz / takım ...}; ürün "parça" diye anılır mı: {evet / hayır}.
- Seri ve ürün adları: {ör. markanın yazımıyla: "Quick Dry", "Perfect Coverage"}.
- Ürün adı tekrarı: {ör. niteleyiciyle tekrarlanır: "pudra fondöten", zamirle düşürülmez}.

## CTA dili

- {ör. kapanışta bir iki cümlelik çağrı; ünlem en çok bir kez; "hemen" kullanılmaz.}

## Ticari dil sınırları

- Net fiyat, fiyat aralığı, indirim oranı, kampanya adı, yıl, ürün sayısı: **yazılmaz** (metodoloji; her markada).
- {Serbest olanlar: "uygun fiyatlı", "ekonomik", rakamsız "Fiyatları" başlığı, "taksit seçenekleri" (rakamsız) ...}

## Yasal ve sektörel kısıtlar

- {ör. kozmetikte sağlık iddiası yok ("leke görünümünü azaltmaya yardımcı"); teknik ölçü yalnız üretici kaynağıyla.}

## CMS biçimi

| Alan | Değer |
|---|---|
| Tablo | {kabul ediyor / etmiyor} |
| Liste (madde imi) | {kabul ediyor / etmiyor: "•  " düz satır} |
| Teslim | {Word / Word + HTML} |
| H1 gövdede | {hayır: şablon H1'i basıyor, gövde başlıksız girişle açılır / evet} |
| SSS | {ayrı modül / gövdenin sonunda} |

## Uzunluk, SSS ve link

- Gövde: {ortalama 750-1.250 / 1.250-1.750 / 1.500-2.000 / 1.500-2.500 / sınır yok (kapsam ve rakip medyanı
  belirler)} kelime; SSS hariç (marka sayfası {1.200-1.800}). ayar.json: `uzunluk` [min, max] ya da null.
- SSS soru sayısı: {3-4 / 5-7 / 8-10 / araştırmada ne kadar çıkarsa (en fazla ~12)}. ayar.json: `sss` [min, max]
  ya da null.
- SSS yanıtı: {30-70} kelime, en fazla {80}. ayar.json: `sss_yanit` [min, max].
- İç link: {5-8}.
- Tek içerik için farklı bant istenirse o içerikte geçersiz kılınır (denetimde `--uzunluk`, `--sss`; içerik
  JSON'unda `uzunluk`, `sss_sayisi`); profil değişmez.

## Site hizmetleri (teyitli)

- {hizmet · teyit adresi · teyit tarihi; süre ve tutar rakamı yazılmaz}

## Kaynak

- Çıkarılan sayfalar: {kategori URL'leri, ürün ve blog örnekleri ya da "rakip yedeği: site1, site2"}
- Ölçüm özeti (`marka_dili.py`): {hitap sayımı, ort. cümle, -mektedir, İngilizce oranı, kategori kelimesi}
- Ekip teyidi: {tarih} · {teyit eden}

## Pilot

- Pilot içerik: {URL} · durum: {bekliyor / revizede / onaylandı}

## Revize geçmişi

- {YYYY-MM-DD} · istek: {...} · kural: {...} · ayar.json: {...} · yaz: {...} · yazma: {...}
