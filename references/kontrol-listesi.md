# Teslim öncesi kontrol listesi

## Profil

- [ ] `markalar/{slug}/profil.md` bu içerik yazılmadan önce okundu mu? Revize geçmişindeki kurallar uygulandı mı?
- [ ] Markanın ilk içeriğiyse (pilot) kullanıcıya gösterilip onay alınmadan başka içerik üretilmedi mi?
- [ ] Pilot revizeleri profile kural olarak, bayrağa dönüşebilenler `ayar.json`'a işlendi mi?

## Hedef ve sahiplik

- [ ] Hedef URL dört sinyalle teyit edildi mi (envanter, canlı kayıt, SERP, GSC)? Canonical kendisi mi, index açık mı?
- [ ] `sayfa.py` kaydında boş kalan alan var mı; varsa `--pw` denendi ya da kullanıcıya söylendi mi?
- [ ] `sahiplik.py` tablosu elle gözden geçirildi mi? SERBEST'teki marka ve renk kelimeleri ayıklandı mı?
- [ ] "N aday sayfa" notu taşıyan sahipler `--teyit` ya da `sayfa.py` ile tek adrese indirildi mi?
- [ ] GSC'de aynı sorguda iki site sayfası görünüyorsa kullanıcıya bildirildi mi?

## Brief

- [ ] Main KW hacmi 12 aylık ortalama mı? Mevsimsel kategoride zirve ayı ve son üç ay DİKKAT'te mi?
- [ ] İkincil kelimelerde BAŞKA SAYFA ya da KAPSAM DIŞI kelimesi var mı? (olmamalı)
- [ ] Her H2'nin araştırmada bir dayanağı var mı ve kurguda yazılı mı?
- [ ] İskelet bu kategorinin doğasına mı göre kuruldu, yoksa başka bir kategorinin başlıkları mı taşındı?
- [ ] Üç ya da daha fazla rakipte geçen konular karşılandı mı? Başlıklardan biri başka sayfanın kelimesi mi? (olmamalı)
- [ ] Kurgu satırlarında canlı kayıttan gelen somut adlar var mı? TON satırı profile uyuyor mu?
- [ ] Link sayısı profildeki bantta mı, her link bölümü ve cümlesiyle yazılı mı, roller dağılmış mı?
- [ ] "Kapsam Dışı Kelimeler" sütunu dolu mu, sahipler tam yol olarak yazılı mı?
- [ ] SSS soruları PAA / otomatik tamamlama / SERBEST sorulardan mı? Başka sayfanın kelimesini taşıyan soru var mı?
- [ ] Yanıt biçimi metni kopyalandı mı (hitap profile göre)? Mevcut Durum sütunu dolu mu?

## İçerik

- [ ] Gövde başlıksız girişle açılıyor mu (profil `h1_govdede: true` ise H1 + giriş), ilk cümle ana kelimeyle tanım mı?
- [ ] Her H2'nin ilk cümlesi başlığın sorusunu doğrudan yanıtlıyor mu?
- [ ] Hitap baştan sona profildeki gibi mi (siz / sen)? Karşı hitap, profil dışı birinci çoğul var mı?
- [ ] Profildeki yaz / yazma tablosu ve marka özel kalıplar ("kategori" yasağı, "parça", marka adı yazımı) uygulandı mı?
- [ ] Yazılan her tür, marka, malzeme ve kalıp `sayfa.py` çıktısında var mı?
- [ ] Taslak bittikten sonra canlı kayıt bir kez daha okundu mu: sayfada olup içerikte olmayan ne var?
- [ ] BAŞKA SAYFA kelimeleri metinde en fazla bir kez ve anchor olarak mı geçiyor?
- [ ] **Anchor'ı sil, cümle hâlâ anlamlı mı?** "...göz atabilirsiniz" biçiminde link cümlesi var mı?
- [ ] Bu sayfanın ana kelimesi başka sayfaya anchor olmuş mu? (olmamalı)
- [ ] Madde satırları var mı? İlk cümleleri özneyi kuruyor ve bilgi ekliyor mu?
- [ ] Sayısal değerlerin kaynağı var mı? Ürün sayısı, fiyat, indirim, yıl, "bu sezon" geçiyor mu? (geçmemeli)
- [ ] Dayanaksız üstünlük iddiası ("en iyi", "en kaliteli") ya da sektör kısıtına aykırı iddia (sağlık) var mı?
- [ ] Bilgi taşımayan paragraf var mı? Her paragraf "okuyucu ne öğrendi" sorusundan geçti mi?
- [ ] Site hizmet cümleleri siteden teyit edildi mi, rakam içeriyor mu? (içermemeli)
- [ ] SSS soru sayısı profildeki bantta mı (`sss`)? Yanıtlar `sss_yanit` bandında (varsayılan 30-70 kelime), ilk cümle
  doğrudan yanıt, gövdeyi tekrar etmiyor mu? Bu içerik için farklı bant istendiyse denetim `--uzunluk` / `--sss`
  ile mi çalıştırıldı?
- [ ] Gövde uzunluğu profildeki bantta ve içerikli rakiplerin medyanının üzerinde mi; altındaysa gerekçesi var mı?
- [ ] Başlıklar aranabilir ifadeler mi, ana kelimeyi ya da ürün adını taşıyor mu?
- [ ] Yüklem dağılımı tek kipe mi kilitlenmiş? Özne ile yüklem uyuşuyor mu, ana kelime cümlede çekimli mi?
- [ ] Tanımlar ve sayımlar metin boyunca tutarlı mı? Gövde ile SSS aynı soruya aynı yanıtı mı veriyor?
- [ ] Kalın etiketli maddelerin ilk cümlesi etiket silinince de anlamlı mı?
- [ ] Profil tablo / liste kabul etmiyorsa tablo kalmış mı? (olmamalı; "•  " satırları ve "1. " adımlar)
- [ ] İhtiyaca göre tür eşleştirmesi, iki seçenek karşılaştırması ve numaralı karar adımları var mı?
- [ ] Kesin yargılar profile göre yumuşatıldı mı? Uzun cümleler noktalı virgülle mi uzatılmış?
- [ ] Ticari kelimeler profilin izin verdiği ölçüde karşılandı mı? Net fiyat ya da aralık var mı? (olmamalı)
- [ ] İçerik baştan sona bir kez okundu mu (özne-yüklem, anlam, iç çelişki, tek tanım, gövde-SSS uyumu)?
- [ ] Word belgesinin adı `{slug}: {tam URL}` mi?

## Otomatik denetim

```bash
python3 scripts/icerik_denetim.py --marka {slug} --json icerik.json --sahiplik sahiplik.json --arastirma arastirma.json --kayit kayit.json --canli
```

Betik bulgu bulursa 1 koduyla çıkar; bulgular giderilmeden çıktı üretilmez. `NOT:` satırları okunarak karar
verilecek adaylardır (kalıp ifade, zamana bağlı söz, karşılanmayan SERBEST kelime).

## Teslim

Çıktılar profildeki çıktı klasörüne kaydedilir: brief Excel'i ve içerik Word dosyası (HTML yalnız istenirse).
Kullanıcıya dört şey söylenir: hangi bilgi hangi kaynaktan alındı; ne yazılmadı ve neden (sahibi başka sayfa olan
kelimeler, teyit edilemeyen bilgiler, okunamayan alanlar); hangi konuda karar ya da teyit bekleniyor (site
düzeyinde çakışma, canonical, CMS'te SSS modülü, profil soruları); site düzeyi çakışmalar.
