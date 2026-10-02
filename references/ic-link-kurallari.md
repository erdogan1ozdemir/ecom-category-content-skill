# İç link seçimi ve yerleşimi

İçerik başına profildeki bant kadar iç link kullanılır (varsayılan **5-8**). Daha azı sayfayı kategori ağacından
kopuk bırakır; daha fazlası gövdeyi link tarlasına çevirir ve her linkin taşıdığı değeri böler.

## Link metne sonradan eklenmez

Önce anchor'ın geçtiği cümlenin metinde zaten var olması gerekir. Ölçü: **anchor'ı sil, cümle hâlâ anlamlı
mı?** Değilse cümle linki taşımak için kurulmuştur, yeniden yazılır.

| Yerine | Böyle |
|---|---|
| "[Kadın kaban] modellerine de göz atabilirsiniz." | "Diz altına inen, yün karışımlı modeller mont değil [kadın kaban] sınıfına girer." |
| "Markalar arasında [Columbia kadın mont] da bulunuyor." | "Yağmurlu havalar için su geçirmez membranlı [Columbia kadın mont] modelleri öne çıkar." |
| "Ayakkabı için [kadın bot] kategorisini inceleyebilirsiniz." | "Uzun bir parka, bilekte biten düz tabanlı bir [kadın bot] ile dengelenir." |

## Dağılım

Linkler şu rollere dağılır. Her rol dolmak zorunda değildir, ama dağılım tek role yığılmaz:

| Rol | Adet | Hedef | Metindeki yeri |
|---|---|---|---|
| Üst kategori | 1 | bir üst seviye (kadın dış giyim, yüz makyajı) | giriş |
| Alt kategori (hub -> spoke) | 2-4 | bu sayfanın alt türleri (kadın şişme mont; yüksek kapatıcı fondöten) | Çeşitleri listesi |
| Kardeş / komşu kategori | 0-1 | aynı seviyede karıştırılan tür (kadın kaban; kapatıcı) | Çeşitleri ya da Nasıl Seçilir |
| Marka + kategori | 1-2 | Google'da sıralanan marka + kategori sayfası (çok markalı sitede) | Markaları |
| Tamamlayıcı kategori (çapraz) | 1-2 | birlikte kullanılan ürün (kadın bot; makyaj bazı) | Kombin / Kullanım |
| Öteki cinsiyet | 0-1 | erkek mont | kapanış ya da SSS, yalnız doğal bağlam varsa |

**Alt kategorisi olmayan sayfada** alt kategori rolü boş kalır; boşluk kardeş, tamamlayıcı ve (çok markalı
sitede) marka + kategori linkleriyle doldurulur. **Tek markalı sitede** (Flormar, Derimod) marka rolü yoktur;
seri / koleksiyon sayfası kalıcı bir ürün grubuysa onun yerine geçebilir.

**Tablo içindeki linkler** (profil tablo kabul ediyorsa) bölüm link sayımına dahildir.

Alt kategori linkleri önceliklidir: üst sayfa ile alt sayfalar arasındaki bağ hem kullanıcının yolunu hem de
hangi sayfanın hangi kelimeye ait olduğunu arama motoruna anlatır.

## Kurallar

- **Anchor, hedef sayfanın ana kelimesidir** ("kadın şişme mont", "Columbia kadın mont"): insanların arattığı
  terim. "Buraya", "tıklayın", "bu modeller", çıplak URL kullanılmaz. Anchor en fazla 4-5 kelime.
- **Bu sayfanın ana kelimesi hiçbir linkin anchor'ı olamaz.**
- **Sayfa kendine link vermez.**
- **Aynı hedefe iki kez link verilmez;** aynı ada sahip iki sayfadan yalnız biri (teyitli olan) kullanılır.
- **Benzer niyetli iki sayfadan birine link verilir.**
- **Noindex sayfaya link verilmez** (`icerik_denetim.py --canli` kontrol eder). Sahibi noindex olan kelime düz
  metinle geçer ve durum teslim notunda bildirilir.
- **Blog, içerik / kampanya, outlet ve ürün sayfalarına link verilmez** (profildeki `link_yasak_desenleri`;
  envanter tipi `icerik`, `urun`, `diger` denetimde bulgu); kategori içeriğinin linkleri listeleme sayfaları
  arasındadır.
- **Hedef canlı ve dolu olmalı:** 200 döner, canonical'ı kendisidir, en az 8 ürünü vardır (daha azı olan alt
  tür linklenmez, metinde düz geçer). Bir adresin envanterde olması canlı ve dolu olduğunu göstermez; sayfanın
  canlı kaydındaki alt kategori adresleri esastır. Canonical'ı başka sayfayı gösteren adrese değil, canonical
  adresin kendisine link verilir.
- **Marka linki yalnız marka + kategori sayfasına verilir** (varsa), markanın ana sayfasına değil: bağlam
  kategoriyse hedef de kategori kırılımıdır. Seçim ölçütü: site haritasında ve GSC'de o kelimede sıralanan sayfa.
- **Anchor, sayfanın adına değil sıralandığı aramaya göre yazılır** (kullanıcı kararı). Sayfanın H1'i "Ray-Ban
  Kadın Gözlük" olsa da "ray-ban kadın güneş gözlüğü" sorgusunda sıralanıyorsa anchor o sorgudur.
- **Arama sayfasına yalnız o arama için açılmış H3'ten link verilir** (bkz. `sahiplik-ve-cannibalization.md`,
  Zayıf sahipler). Adres Google'da / GSC'de sıralanan arama adresidir. Bu linkler `--canli` ile okunmaz,
  denetimde NOT olarak kalır.
- **Filtre sayfasına (`?renk=`) link** yalnız o adres sitemap envanterinde varsa verilir.
- **Kampanya, outlet ve tarihli sayfalara** link verilmez; içerik kalıcıdır, o sayfalar değil.
- Tek paragrafta en fazla 2, tek H2'de en fazla 4 link (alt kategori linklerinin toplandığı Çeşitleri bölümü
  dışında 2'yi geçmemesi iyi olur). Giriş paragrafında en fazla 1.
- SSS yanıtlarında link en fazla 1 kez kullanılır; SSS modülü şemaya girerse link düz metne döner.

## Adayları bulmak

```bash
python3 scripts/envanter.py --marka {slug} iliskili {hedef URL}   # üst, alt, akraba, marka, filtre ve arama sayfaları
python3 scripts/sayfa.py --marka {slug} {hedef URL}               # sayfadaki alt / kardeş kategori ve marka kırılımları (canlı)
python3 scripts/envanter.py --marka {slug} sahip "kadın bot"      # tamamlayıcı kategori için sahibi bul
```

Alt kategori adayları için öncelik `sayfa.py` çıktısındaki "Alt kategoriler" listesidir (yöntemi `yontem`'de):
sitenin o sayfada gerçekten gösterdiği alt kırılımlar bunlardır. "html:kategori-menusu" yöntemiyle gelen liste
kardeş kategorileri de içerebilir; breadcrumb ve yol ile ayrılır. `envanter.py iliskili` daha geniş ama eski /
aynı adlı adresleri de getirebilir.

Brief'te her link, yerleşeceği bölüm ve cümleyle birlikte yazılır:

```
1. kadın şişme mont : https://www.boyner.com.tr/kadin-sisme-mont-x-g3731-c23896555
   H2 · Kadın Mont Çeşitleri bölümünde, "Şişme mont" maddesinin tanım cümlesinde.
```
