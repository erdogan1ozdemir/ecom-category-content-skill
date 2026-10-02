# Marka profili: çıkarma, doğrulama, saklama

Metodoloji her markada aynıdır; **biçim ve dil markaya göre değişir** (kullanıcı kararı). Markaya özgü her
karar `markalar/{marka-slug}/` altındaki iki dosyada durur:

| Dosya | Kim okur | İçerik |
|---|---|---|
| `profil.md` | model ve ekip | ton, hitap, cümle yapısı, yaz / yazma tablosu, ürün adlandırma, CTA, ticari dil sınırları, yasal kısıtlar, CMS biçimi, bantlar, kaynak, pilot ve revize geçmişi |
| `ayar.json` | betikler | alan adı, pazar, GSC / SEOmonitor, URL desenleri, cinsiyet kimlikleri, biçim bayrakları, yasak kalıplar, rakip listesi, bantlar, çıktı klasörü |

Profil depoya girer ve ekip ortak kullanır. İki dosya çelişirse `profil.md` esastır, `ayar.json` düzeltilir.
Şablon: `markalar/_sablon/`. Tam doldurulmuş örnek: `markalar/boyner/`.

## İçindekiler

1. Dil nereden çıkarılır (öncelik sırası)
2. Rakip yedeği
3. Ölçüm nasıl okunur
4. Kurulum soruları (ekibe doğrulama)
5. Profil şablonunun alanları
6. ayar.json alanları
7. Pilot ve revize geçmişi

## 1. Dil nereden çıkarılır

Öncelik sırası (kullanıcı kararı):

1. **Markanın mevcut kategori sayfası metinleri** - kategori içeriğinin en yakın örneği.
2. **Ürün açıklamaları** - markanın ürünü nasıl anlattığı, hangi terimleri kullandığı.
3. **Blog** - ton ve hitap için; yapısı kategori metnine taşınmaz.

```bash
python3 scripts/marka_dili.py --marka {slug} --cikti $T/dil.json [--kategori 8 --urun 6 --blog 4 --tara 25]
python3 scripts/marka_dili.py --marka {slug} --url URL1 URL2 ...     # envanter yerine elle seçilen kategoriler
```

Betik profili yazmaz; ölçüm ve örnek paragraf verir. Model çıktıyı okur, örnek paragrafların üçünü dördünü tam
okur (`ornekler[].ilk_paragraflar`; gerekirse `sayfa.py URL --icerik`), sonra profil taslağını yazar.

**Mevcut içeriğin yapısı örnek alınmaz** (Boyner'de alınan karar, her markada geçerli): mevcut metinler çoğu
zaman başlık hiyerarşisi tutmaz, SSS taşımaz, "eşsiz bir yolculuk" türü bilgisiz cümlelerle doludur. Profile
**dil** kararları girer: hitap, ton, terim tercihi, marka adı yazımı, CTA alışkanlığı.

## 2. Rakip yedeği

Kategori metni yoksa ya da kalitesizse (`marka_dili.py` "yeterli: HAYIR" diyorsa ya da metinler anahtar kelime
dolgusu, kopuk cümle, tutarsız hitap taşıyorsa) profil **marka ve sektöre uygun rakiplerin dilinden** türetilir:

- Aynı sektörde ve fiyat konumunda 2-3 site seçilir (kozmetikte marka siteleri, giyimde marka siteleri; pazar
  yerleri değil). Seçim kullanıcıya gösterilir.
- Her birinden 2-3 kategori metni okunur (`sayfa.py --domain {rakip} URL --icerik`; rakip sitede yalnız okuma).
- Ortak payda profile yazılır: hitap, ton, cümle uzunluğu, terim düzeyi. Rakibe özgü kalıp ve marka adı alınmaz.
- Profilde "Kaynak: rakip yedeği ({siteler})" yazılır ve ekip teyidi zorunlu sayılır.

## 3. Ölçüm nasıl okunur

| Ölçüm | Profile yansıması |
|---|---|
| siz / sen / biz sayımı | Baskın hitap önerilir; karışıksa ekibe sorulur. Biz sayımı yüksekse birinci çoğul kullanımı (yalnız liste girişi mi, serbest mi) sorulur. |
| ort. cümle uzunluğu | 12-16 kelime olağan; 20+ ise uzun cümle kaçınılacaklara girer. |
| ünlem / 1000 kelime, emoji | 3'ün üzeri ünlem markanın tarzı olabilir ama kategori metninde en çok bir ünlem önerilir; emoji kategori metnine girmez. |
| "-mektedir" | Sık ise `mektedir: serbest`, hiç yoksa `az` önerilir. |
| İngilizce görünümlü kelime oranı ve örnekleri | Ürün adı mı (Quick Dry, Matte Finish), sektör terimi mi (primer, highlighter), gereksiz mi; yaz / yazma tablosuna girer. |
| "kategori", "ürün grubu", "parça" | Kullanılıyorsa ekibe "kategori kelimesi yasak mı" sorulur (Boyner'de yasak). |
| CTA'lar | "hemen keşfet" gibi kalıplar markanın tarzıysa bir kez kapanışta; yoksa CTA dili sade tutulur. |
| sık kalıplar, cümle açılışları | Ürün adlandırma (seri adları, "Flormar oje" gibi marka + ürün kalıbı) ve tekrar eden açılışlar. |
| marka adı yazımları | Doğru yazım profile yazılır (VitrA, GAME+); diğerleri yasak kalıba girer. |

## 4. Kurulum soruları (ekibe doğrulama)

Taslak hazırlandıktan sonra AskUserQuestion ile sorulur; her soruda taslağın önerisi ilk seçenektir ve
"(Önerilen)" etiketini taşır. Bir turda en çok dört soru; üç tur yeterlidir.

**Tur 1 - dil**

1. Hitap: siz mi, sen mi? (öneri ölçümden; Turkcell ve Flormar "sen", Boyner "siz")
2. Genel ton: 3-5 sıfat ve bir örnek cümle (taslaktaki öneri gösterilir)
3. Yasak ve tercih edilen kelimeler: taslaktaki yaz / yazma tablosu onaylanır ya da düzeltilir; marka adı yazımı
4. Ticari dil: "uygun fiyatlı", "ekonomik", "Fiyatları" başlığı, taksit / kampanya kelimeleri serbest mi? (rakam
   her durumda yazılmaz)

**Tur 2 - biçim (CMS)**

1. CMS içerik alanı tablo kabul ediyor mu? Liste (madde imi) kabul ediyor mu? Kabul etmiyorsa "•  " düz satır
   biçimi kullanılır (Boyner).
2. Teslim biçimi: Word mü, HTML mi (ikisi de)? H1 gövdede mi (şablon H1'i kendisi mi basıyor)? SSS ayrı modül mü?
3. Link sayısı (varsayılan 5-8)
4. Marka özel kalıplar: "kategori" kelimesi yasak mı, "-mektedir" serbest mi, birinci çoğul ("sizin için
   seçtik") kullanılır mı, ürün "parça" diye anılabilir mi?

**Tur 3 - uzunluk ve SSS** (seçenekli; kullanıcı kararı)

1. Gövde uzunluğu (SSS hariç):

   | Seçenek | ayar.json `uzunluk` |
   |---|---|
   | ortalama 1.500-2.500 kelime **(Önerilen, varsayılan)** | `[1500, 2500]` |
   | ortalama 1.500-2.000 kelime | `[1500, 2000]` |
   | ortalama 1.250-1.750 kelime | `[1250, 1750]` |
   | ortalama 750-1.250 kelime | `[750, 1250]` |
   | sınır yok (en makul uzunluk kategorinin ihtiyacından hesaplanır; en az 750, en fazla 3.000 kelime) | `null` |

2. SSS soru sayısı:

   | Seçenek | ayar.json `sss` |
   |---|---|
   | 5-7 soru **(Önerilen, varsayılan)** | `[5, 7]` |
   | 3-4 soru | `[3, 4]` |
   | 8-10 soru | `[8, 10]` |
   | araştırmada ne kadar çıkarsa (en fazla ~12) | `null` |

3. (İsteğe bağlı) SSS yanıt uzunluğu: varsayılan 30-70 kelime, en fazla 80 (`sss_yanit: [30, 70]`; en fazla
   değeri üst sınır + 10). Ekip farklı isterse değiştirilir.

AskUserQuestion dört seçenek gösterir; beşinci seçenek ("sınır yok") için "Diğer" yanıtı kullanılır ya da
seçenekler iki soruya bölünür. Seçim `profil.md` -> "Uzunluk, SSS ve link" ve `ayar.json`'a yazılır.
`icerik_denetim.py` uzunluk ve SSS sayısını bu değerlerden denetler; `uzunluk` `null` ise 750-3.000 çerçevesini denetler, `sss` `null` ise yalnız bilgi notu verir.
**Tek içerik için** kullanıcı farklı bant isterse profil değişmez, o içerikte geçersiz kılınır: denetimde
`--uzunluk 750-1250` / `--uzunluk yok`, `--sss 3-4` / `--sss yok`, ya da içerik JSON'unda `"uzunluk": [750, 1250]`
ve `"sss_sayisi": [3, 4]` (`sss` alanı soru-yanıt listesi olduğu için sayı bandı `sss_sayisi` adını taşır).

Yanıtlar `profil.md`'ye ve karşılık gelen `ayar.json` bayraklarına yazılır; "Kaynak" bölümüne teyit tarihi ve
teyit eden kişi girer.

## 5. Profil şablonunun alanları (`markalar/_sablon/profil.md`)

| Bölüm | İçerik |
|---|---|
| Künye | marka adı ve doğru yazımı, alan adı, sektör, pazar / dil, platform |
| Hitap ve ton | hitap; 3-5 sıfat; 2-3 örnek cümle (yaz) ve karşıtı (yazma) |
| Cümle yapısı | cümle uzunluğu, kip tercihi (-mektedir, -abilir, emir), birinci çoğul, yumuşatma |
| Yaz / yazma tablosu | tercih edilen ve kaçınılan kelime ve kalıplar, gerekçesiyle |
| Ürün adlandırma | seri ve ürün adlarının yazımı, ürün ailesi sözcüğü (giysi, makyaj ürünü, cihaz), "parça" kuralı |
| CTA dili | kapanış çağrısı biçimi, ünlem |
| Ticari dil sınırları | fiyat, kampanya, taksit, indirim; rakam yasağı her durumda |
| Yasal ve sektörel kısıtlar | sağlık iddiası, garanti, teknik ölçü kaynağı, çocuk ürünü güvenliği |
| CMS biçimi | tablo, liste, HTML, H1 gövdede, SSS modülü, link biçimi |
| Uzunluk, SSS ve link | gövde bandı, SSS soru sayısı, SSS yanıt uzunluğu, link bandı; tek içerikte geçersiz kılma |
| Site hizmetleri | teyitli hizmetler (teslimat, iade, mağaza) ve teyit adresi; rakamsız anılır |
| Kaynak | hangi sayfalardan çıkarıldı (URL listesi), marka_dili ölçüm özeti, ekip teyidi tarihi, teyit eden |
| Pilot | pilot içerik (URL), durum (bekliyor / revizede / onaylandı) |
| Revize geçmişi | tarih · istek · kural cümlesi · yaz / yazma örneği |

## 6. ayar.json alanları

| Alan | Örnek | Açıklama |
|---|---|---|
| `marka`, `marka_adi`, `domain`, `kok_url` | `"flormar"`, `"Flormar"`, `"flormar.com.tr"`, `"https://www.flormar.com.tr/"` | `kok_url` yoksa ana sayfanın yönlendirmesinden bulunur (www'li mi değil mi) |
| `sektor`, `platform` | `"kozmetik"`, `"akinon"` | bilgi; `sayfa.py` platformu her okumada yeniden tespit eder |
| `location_code`, `language_code`, `ulke` | `2792`, `"tr"`, `"tr"` | DataForSEO ve otomatik tamamlama pazarı; şimdilik Türkiye/Türkçe |
| `gsc_property`, `seomonitor_campaign_id` | `"sc-domain:flormar.com.tr"`, `12345` | ücretsiz sıralama verisi kaynakları |
| `sitemapler` | `[{"url": "...", "ad": "category"}]` | boşsa keşif (robots.txt, /sitemap.xml, /sitemap_index.xml) |
| `url_desenleri` | `[{"tip": "kategori", "desen": "^/[a-z0-9-]+/$"}]` | ilk eşleşen kazanır; tip: `liste` (b/g/c kimliklerinden), `kategori`, `marka`, `arama` (grup `arama`), `urun`, `icerik`, `diger`; isimli gruplar `slug`, `kimlik`, `b`, `g`, `c`, `q`; `kimlik` alt desenleri; `cinsiyet_slugdan` |
| `yalniz_desen` | `true` | desene uymayan adres envantere girmez (Boyner) |
| `cinsiyet_kimlikleri`, `cinsiyet_sekme` | `{"3731": "Kadın"}`, `{"3733": "Çocuk"}` | kimlik tabanlı cinsiyet (Boyner); slug'da "kadin/erkek/cocuk" geçen sitelerde gerekmez |
| `sekmeler` | `["Kategori", "Kadın", "Erkek", "Marka"]` | boşsa envanterden |
| `kur_kaynaklar`, `kur_haric`, `kur_marka` | `["sitemap-categories-1"]`, `"outlet|kampanya"`, `false` | brief Excel'ine hangi sayfaların `Bekliyor` olarak gireceği |
| `hitap` | `"siz"` / `"sen"` | denetim karşı hitabı bulgu sayar |
| `tablo`, `liste`, `html`, `h1_govdede`, `sss_modulu` | `false` | CMS biçimi |
| `kategori_kelimesi_yasak`, `parca_kurali` | `true` | Boyner kalıpları; denetim bayrağa göre bakar |
| `mektedir` | `"serbest"` / `"az"` / `"kacin"` | |
| `birinci_cogul` | `"liste_girisi"` / `"serbest"` / `"yasak"` | |
| `sss_baslik` | `"{kategori} Hakkında Sık Sorulan Sorular"` | SSS H2 kalıbı (Flormar: `"{kategori} Hakkında Sıkça Sorulanlar"`); içerik JSON'undaki `sss_baslik` önceliklidir |
| `yasak_kalip` | `[{"desen": "(?i)\\bbayan\\b", "ad": "...", "seviye": "sorun"}]` | `seviye: uyari` NOT olarak döner |
| `rakip_perakendeciler` | `["golden rose", "pastel"]` | pazar yerleri her zaman eklenir; sitede sayfası olan marka muaf |
| `dolgu_ek` | `["flormar"]` | kelime kümesinde yok sayılan ek kelimeler (marka adı kendiliğinden eklenir) |
| `uzunluk`, `marka_uzunluk`, `link` | `[1500, 2500]`, `[1200, 1800]`, `[5, 8]` | bantlar; `uzunluk: null` = sınır yok (uzunluk kategorinin ihtiyacından; 750 altı ve 3.000 üstü denetimde SORUN) |
| `sss`, `sss_yanit` | `[5, 7]`, `[30, 70]` | SSS soru sayısı (`null` = araştırmada ne çıkarsa, en fazla ~12) ve yanıt kelime bandı (en fazla üst + 10) |
| `zayif_sahip_desenleri`, `link_yasak_desenleri` | `["/blog/"]`, `["/blog/", "/kampanya/"]` | |
| `cikti_klasoru`, `brief_dosyasi` | `"~/Desktop/Claude Projects/Flormar/Kategori İçerik/"` | |

## 7. Pilot ve revize geçmişi

Bir markanın ilk içeriği pilottur: tek içerik yazılır, kullanıcıya gösterilir, revize alınır. Her revize
`profil.md` -> "Revize geçmişi"ne **kural olarak** yazılır; tek seferlik düzeltme gibi değil, sonraki bütün
içeriklere uygulanacak cümle olarak:

```
- 2026-10-05 · istek: "kategoride" yazılmasın · kural: "kategori / kategoride" kelimesi metinde geçmez; yerine
  "{ürün} ürün grubu" ya da "{marka} {ürün} modelleri arasında" yazılır · ayar.json: kategori_kelimesi_yasak = true
  · yaz: "Flormar fondötenleri arasında ..." · yazma: "Kategoride ..."
```

Bayrağa dönüşebilen revize (`hitap`, `tablo`, `yasak_kalip`, bantlar) `ayar.json`'a da işlenir ki denetim betiği
bir sonraki içerikte yakalasın. Pilot onaylanınca "Pilot" satırı `onaylandı` yapılır; toplu üretim ancak bundan
sonra başlar. Profil değişikliği depoya doğrudan commit edilmez; bkz. 8. bölüm.

## 8. Profil güncelleme akışı (ekip)

Profilleri ekip üyeleri kendi çalışmalarında bu skill ile kurar ve geliştirir; depoyu tek kişi (depo sahibi)
günceller. Böylece aynı markanın iki farklı sürümü depoda yan yana oluşmaz.

1. Ekip üyesi markanın klasörünü (`markalar/{marka}/`) yerelde kurar ya da var olanı günceller: Faz 0 soruları,
   pilot revizeleri, "Revize geçmişi" satırları. Depoya push etmez.
2. Hazır olan `profil.md` + `ayar.json` (ve varsa ekibin kendi kural dosyası) depo sahibine iletilir. İletilen
   sürümde "Kaynak -> Ekip teyidi" satırı teyit edenin adını ve tarihi taşır.
3. Depo sahibi gelen dosyayı depodaki sürümle karşılaştırır:
   - Ekip dosyası depodaki profilin üzerindedir; çelişen kural ekip dosyasındaki haliyle alınır, eski kural
     "Revize geçmişi"ne gerekçesiyle yazılır.
   - Ekip dosyasında olup şablonda alanı olmayan kural şablonun en yakın bölümüne (çoğu zaman "Yaz / yazma
     tablosu" ya da "Yapı") eklenir; bayrağa dönüşebiliyorsa `ayar.json`'a da işlenir.
   - Metodoloji kuralları (rakam yasağı, sahiplik, link seçimi, answer-first SSS) markaya göre değişmez; ekip dosyası
     bunlarla çelişirse depo sahibine sorulur.
4. Birleştirilen profil `icerik_denetim.py` ile o markanın son içeriğinde denenir (bayraklar çalışıyor mu); sonra
   depo sahibi commit eder.

Skill bir profil değişikliği yaptığında bunu kullanıcıya "depo sahibine iletilecek değişiklik" olarak özetler
(değişen alanlar ve revize satırı); kendisi commit önermez. Depo sahibinin kendi oturumunda commit, kullanıcı
istediğinde yapılır.
