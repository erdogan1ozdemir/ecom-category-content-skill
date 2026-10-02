# Marka sayfası içeriği

Çok markalı sitelerde (Boyner, Sephora, Özdilekteyim, Turkcell Pasaj) marka listeleme sayfaları kategori
sayfalarıyla aynı akıştan geçer; farklar aşağıda. Bu dosya yalnız hedef bir marka sayfasıysa okunur (envanter tipi
`marka`; örnek Boyner `/skechers-x-b545`). Tek markalı sitelerde (Flormar, Derimod) marka sayfası yoktur; seri /
koleksiyon sayfaları kategori sayfası gibi işlenir.

## Hedef ve kelime

- **Ana kelime marka adıdır** ("skechers"). Marka sorgusu çoğu zaman gezinme niyetlidir ve markanın kendi sitesi
  ilk sıradadır; perakendeci sayfasının işi "skechers + ürün" ve "skechers modelleri" sorgularında ve marka
  hakkındaki bilgi sorgularında görünmektir.
- `arastirma.py` marka adıyla çalıştırılır; ek tohum olarak "{marka} modelleri" ve markanın sitedeki en büyük ürün
  ailesi ("skechers ayakkabı") verilir (`--ek`).
- SERP'te markanın kendi sitesi, pazar yerleri ve Wikipedia bulunur; rakip içerik olarak **diğer perakendecilerin
  marka sayfaları** okunur, markanın kendi sitesi başlık kaynağı değil bilgi kaynağıdır.

## Hedef teyidi

Marka sayfasında envanter çoğu zaman tek aday verir; çakışmayı yalnız GSC gösterir. Her marka için bakılır:

- **Marka içerik / kampanya sayfaları** (örnek: Boyner `/content/{marka}`) görselli kampanya / karosel sayfalarıdır,
  listeleme değildir. Marka sorgusunun esas sayfası her zaman marka listeleme sayfasıdır (kullanıcı kararı).
  Kampanya sayfası marka sorgusunda gösterim alıyorsa bu yalnız teslim notunda bilgi olarak yazılır; ona link
  verilmez.
- **Alt marka sayfaları** (Calvin Klein Jeans, Tommy Jeans): o çizginin kelimeleri alt marka sayfasınındır; ana
  marka içeriğinde bir kez, link olarak geçer.

## Kelime sahipliği

Marka sayfasının çevresi kalabalıktır: marka + cinsiyet, marka + kategori ve marka + cinsiyet + kategori sayfaları
ayrı ayrı yayında olabilir.

| Kelime | Sahibi | Bu içerikte |
|---|---|---|
| skechers, skechers modelleri, skechers türkiye | marka sayfası | HEDEF |
| skechers kadın, skechers erkek, skechers çocuk | marka + cinsiyet sayfası | başlık olmaz; bir kez, link olarak |
| skechers ayakkabı, skechers bot, skechers terlik | marka + kategori sayfası (varsa) | başlık olmaz; ürün aileleri listesinde link olarak |
| skechers kadın yürüyüş ayakkabısı | marka + cinsiyet + kategori sayfası | başlık olmaz; link olarak ya da hiç |
| skechers memory foam, skechers go walk (seri ve teknoloji adları) | çoğu zaman sahipsiz ya da arama sayfası | SERBEST: seri/teknoloji bölümünde karşılanır |
| skechers hangi ülkenin, skechers orijinal nasıl anlaşılır, skechers kalıbı dar mı | sahipsiz | SERBEST: H2/H3 ya da SSS |

`sahiplik.py --kayit` marka sayfasının canlı kategori kırılımlarını sahip olarak öne alır. Marka + kategori sayfası
olmayan ürün ailesi (SERBEST) gövdede bir paragraf alabilir.

## İçerik

- **Giriş:** marka kimdir (kuruluş yeri ve yılı, neyle bilinir; kaynak: markanın kendi kurumsal sayfası) ve sitede
  hangi ürün aileleri bulunur (canlı kayıttaki kategoriler).
- **Yapı taşları** (araştırma hangilerini destekliyorsa):

| Blok | İçerik |
|---|---|
| {Marka} Modelleri / Ürünleri | sitedeki ürün aileleri; marka + kategori ve marka + cinsiyet linkleri burada |
| {Marka} Serileri / Teknolojileri | markanın kendi adlandırdığı seriler ve teknolojiler; her biri ne işe yarar (kaynak: marka) |
| {Marka} Kalıp ve Numara / Beden | "kalıbı dar mı", "numara büyük mü alınır" aramaları; markanın kendi beden rehberine dayanır |
| {Marka} Kimler İçin / Hangi Kullanım | ürün ailesiyle eşleştirilir |
| {Marka} Orijinal Ürün Nasıl Anlaşılır? | aranıyorsa; yetkili satıcı vurgusu, abartısız |
| {Marka} Fiyatları | fiyatı belirleyen etkenler (seri, teknoloji, malzeme); rakam yok |
| {Marka} Bakım | markanın bakım talimatına dayanır |
| {Site} {Marka} Modelleri | filtreler, cinsiyet ve kategori kırılımları |

- **Marka bilgisi kaynakla yazılır.** Kuruluş yılı, ülke, teknoloji adları markanın resmi sitesinden doğrulanır;
  doğrulanamayan tarih ve iddia yazılmaz. Teknoloji adları markanın yazımıyla geçer.
- **Karşılaştırma yapılmaz:** başka markalarla kıyas, üstünlük iddiası ve rakip marka adı yazılmaz.
- **Ürün gamı:** `sayfa.py {marka URL} --gam` alt kategorilerin ürün sayısını ve örnek ürünlerini verir; içerikte
  ürün aileleri bu ağırlığa göre sıralanır.
- **"{Marka} modelleri / ürünleri / türkiye"** hacmi görünmese de HEDEF sayılır.
- **Marka adı cümlede yalın kalır** ("Calvin Klein, ... markasıdır").
- **Karşılaştırma** (profil tablo kabul ediyorsa tablo, etmiyorsa "•" satırları) marka sayfasında ürün ailelerini
  ya da serileri karşılaştırır; alt marka ile ana markayı karşılaştırmak sahipli kelimeye bölüm açmak olur.
- **Link istisnası:** "Modelleri / Ürünleri" bölümünde 5-6 link bulunabilir (genel kural tek H2'de 4).
- **Etiket link olur:** ürün ailesi maddelerinde etiket marka adını taşır ve ailenin kendi sayfası varsa etiketin
  kendisi linktir (`**[LINK1]:**`).
- **Uzunluk:** profildeki `marka_uzunluk` (varsayılan 1.200-1.800 kelime gövde).
- **Linkler (profildeki bant):** marka + cinsiyet sayfaları (2-3), marka + kategori ya da marka + cinsiyet +
  kategori sayfaları (2-4; Google'da sıralananlar öncelikli), 0-1 genel kategori sayfası. Anchor her zaman marka
  adını taşır ("Skechers kadın ayakkabı"); çıplak "kadın ayakkabı" anchor'ı genel kategori sayfasına aittir.
- Brief satırı Excel'de `Marka` sekmesine yazılır; Word belge adı yine `{slug}: {tam URL}`.
