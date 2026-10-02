#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Betiklerin ortak yardımcıları: marka ayarı (profil), curl ile istek, önbellek dizini, Türkçe
normalizasyon, URL çözümleme ve sınıflandırma.

Marka ayarı: her marka için `markalar/{slug}/ayar.json` (betikler için) ve `profil.md` (okunur kurallar)
bulunur. Betikler `--marka {slug}` ya da `--domain {alan adı}` alır; ayar `baslat()` ile yüklenir ve bu
modüldeki AYAR sözlüğüne yazılır. Ayar yoksa `--domain` ile varsayılan değerlerle çalışılır (Faz 0).

İstekler curl ile atılır: bu makinede Python'un urllib'i kurumsal sertifika zinciri yüzünden SSL hatası
veriyor; curl çalışıyor. Aynı alan adına istekler arasında en az 1,2 saniye beklenir (ECOM_BEKLE ile
değişir); Cloudflare doğrulama sayfası gelirse getir() bekleyip yeniden dener, yine gelirse boş/"cf"
sonucu döner ve çağıran betik bunu raporlar.
"""
import argparse, gzip, json, os, re, subprocess, sys, time, unicodedata
from urllib.parse import urlsplit, urljoin, unquote_plus, parse_qsl, urlencode

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKALAR = os.path.join(SKILL, "markalar")
ONBELLEK_KOK = os.path.expanduser("~/.cache/ecom-kategori-icerik")

VARSAYILAN = {
    "marka": None, "marka_adi": None, "domain": None, "kok_url": None, "sektor": None, "platform": None,
    "location_code": 2792, "language_code": "tr", "ulke": "tr",
    "gsc_property": None, "seomonitor_campaign_id": None,
    "sitemapler": [],                 # boşsa robots.txt + /sitemap.xml + /sitemap_index.xml keşfedilir
    "url_desenleri": [],              # [{"tip", "desen", "kimlik"?, "cinsiyet_slugdan"?}] ilk eşleşen kazanır
    "yalniz_desen": False,            # True: desene uymayan adres envantere girmez (sezgisel sınıflama kapalı)
    "cinsiyet_kimlikleri": {},        # kimlik ya da slug kelimesi -> etiket ("3731": "Kadın")
    "cinsiyet_sekme": {},             # kimlik -> brief sekmesi ("3733": "Çocuk")
    "sekmeler": None,                 # None: envanterden (cinsiyet varsa Kategori + cinsiyetler + Marka)
    "hitap": "siz", "tablo": False, "liste": False, "html": False, "h1_govdede": False, "sss_modulu": True,
    "kategori_kelimesi_yasak": False, "parca_kurali": False, "mektedir": "serbest", "birinci_cogul": "liste_girisi",
    "yasak_kalip": [], "rakip_perakendeciler": [], "dolgu_ek": [],
    "uzunluk": [1500, 2500], "marka_uzunluk": [1200, 1800], "link": [5, 8],
    "sss_baslik": "{kategori} Hakkında Sık Sorulan Sorular",  # SSS H2 kalıbı; içerik JSON'undaki sss_baslik önceliklidir
    "sss": [5, 7], "sss_yanit": [30, 70],      # SSS soru sayısı bandı (null: araştırmada ne çıkarsa) ve yanıt kelime bandı
    "zayif_sahip_desenleri": [], "link_yasak_desenleri": [], "kur_haric": "", "kur_marka": False,
    "cikti_klasoru": None,
}
AYAR = dict(VARSAYILAN)
_DOLGU_AKTIF = None

# --- marka ayarı ---------------------------------------------------------------------------------


def arguman_ekle(ap):
    ap.add_argument("--marka", help="markalar/{slug}/ayar.json içindeki marka (ör. boyner)")
    ap.add_argument("--domain", help="ayar yoksa ya da başka marka denenecekse alan adı (ör. flormar.com.tr)")
    return ap


def _alan(d):
    d = (d or "").lower().strip()
    d = re.sub(r"^https?://", "", d).split("/")[0]
    return d[4:] if d.startswith("www.") else d


def ayar_dosyasi(marka):
    return os.path.join(MARKALAR, marka, "ayar.json")


def baslat(marka=None, domain=None, zorunlu=True):
    """Aktif marka ayarını yükler. Öncelik: --marka, --domain ile eşleşen profil, ECOM_MARKA ortam değişkeni."""
    global _DOLGU_AKTIF
    marka = marka or (None if domain else os.environ.get("ECOM_MARKA"))
    veri = None
    if marka:
        yol = ayar_dosyasi(marka)
        if not os.path.exists(yol):
            sys.exit(f"Marka ayarı yok: {yol}\nFaz 0 (marka kurulumu) yürütülmeli ya da --domain ile çalışılmalı.")
        veri = json.load(open(yol, encoding="utf-8"))
        veri.setdefault("marka", marka)
    elif domain:
        for ad in sorted(os.listdir(MARKALAR)) if os.path.isdir(MARKALAR) else []:
            yol = ayar_dosyasi(ad)
            if not ad.startswith("_") and os.path.exists(yol):
                v = json.load(open(yol, encoding="utf-8"))
                if _alan(v.get("domain")) == _alan(domain):
                    veri = v; veri.setdefault("marka", ad); break
        if veri is None:
            veri = {"domain": _alan(domain), "marka": None}
            print(f"BİLGİ: {_alan(domain)} için marka profili yok; varsayılan ayarlarla çalışılıyor.", file=sys.stderr)
    elif zorunlu:
        sys.exit("--marka ya da --domain gerekli")
    else:
        veri = {}
    AYAR.clear(); AYAR.update(VARSAYILAN); AYAR.update(veri or {})
    if AYAR.get("domain"):
        AYAR["domain"] = _alan(AYAR["domain"])
        AYAR["kok_url"] = AYAR.get("kok_url") or kok_tespit(AYAR["domain"])
        if not AYAR["kok_url"].endswith("/"):
            AYAR["kok_url"] += "/"
    ek = set(AYAR.get("dolgu_ek") or [])
    if AYAR.get("marka_adi"):
        ek |= set(duz(AYAR["marka_adi"]).split())
    _DOLGU_AKTIF = DOLGU | ek
    return AYAR


def kok_tespit(alan):
    """Profilde kok_url yoksa sitenin asıl kökünü (www'li mi, www'siz mi) ana sayfanın yönlendirmesinden bulur;
    sonuç 30 gün önbellekte tutulur. Ulaşılamazsa https://www.{alan}/ varsayılır."""
    yol = os.path.join(ONBELLEK_KOK, alan, "kok.txt")
    if os.path.exists(yol) and time.time() - os.path.getmtime(yol) < 30 * 86400:
        return open(yol).read().strip()
    kok_ = f"https://www.{alan}/"
    try:
        r = subprocess.run(["curl", "-sSL", "-o", "/dev/null", "-m", "20", "-A", UA, "-w", "%{url_effective}", kok_],
                           capture_output=True, text=True)
        p = urlsplit(r.stdout.strip())
        if p.netloc and _alan(p.netloc) == alan:
            kok_ = f"{p.scheme}://{p.netloc}/"
    except Exception:
        pass
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    open(yol, "w").write(kok_)
    return kok_


def ayni_adres(a, b):
    """Şema, www ve sondaki / farkı gözetmeden iki adresin aynı sayfa olup olmadığı."""
    n = lambda u: re.sub(r"^https?://(www\.)?", "", (u or "").split("#")[0]).rstrip("/").lower()
    return n(a) == n(b)


def ayar_args(a, zorunlu=True):
    return baslat(getattr(a, "marka", None), getattr(a, "domain", None), zorunlu=zorunlu)


def site():
    return AYAR.get("kok_url") or ""


def kisalt(url):
    """Tam adresi yol hâline getirir (tablolarda okunur kalsın)."""
    if not url:
        return url or ""
    p = urlsplit(url)
    if _alan(p.netloc) == AYAR.get("domain"):
        return p.path + ("?" + p.query if p.query else "")
    return url


def onbellek(*parca):
    """Alan adına göre ayrılmış önbellek yolu: ~/.cache/ecom-kategori-icerik/{domain}/..."""
    yol = os.path.join(ONBELLEK_KOK, AYAR.get("domain") or "_genel", *parca)
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    return yol


def genel_onbellek(*parca):
    yol = os.path.join(ONBELLEK_KOK, *parca)
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    return yol


# --- istek ---------------------------------------------------------------------------------------

_SON_ISTEK = {}
BEKLEME = {"suggestqueries.google.com": 0.3, "r.jina.ai": 0.5}


def _bekle(url):
    host = urlsplit(url).netloc
    asgari = BEKLEME.get(host, float(os.environ.get("ECOM_BEKLE", "1.2")))
    gecen = time.time() - _SON_ISTEK.get(host, 0)
    if gecen < asgari:
        time.sleep(asgari - gecen)
    _SON_ISTEK[host] = time.time()


def cloudflare_mi(govde):
    bas = (govde or "")[:3000]
    return ("Just a moment..." in bas or "cf-browser-verification" in bas or "challenge-platform" in bas
            or "Attention Required! | Cloudflare" in bas)


def istek(url, saniye=40, ek_baslik=(), bayt=False):
    """Tek istek: {kod, son_url, basliklar, govde}. Yönlendirmeler izlenir."""
    _bekle(url)
    komut = ["curl", "-sSL", "--compressed", "-m", str(saniye), "-A", UA, "-H", "Accept-Language: tr-TR,tr;q=0.9",
             "-D", "-", "-w", "\n__ECOM__%{http_code} %{url_effective}"]
    for b in ek_baslik:
        komut += ["-H", b]
    r = subprocess.run(komut + [url], capture_output=True)
    ham = r.stdout or b""
    i = ham.rfind(b"\n__ECOM__")
    son = ham[i + 9:].decode("utf-8", "ignore").split(" ", 1) if i >= 0 else ["0", url]
    ham = ham[:i] if i >= 0 else ham
    # -D - başlıkları gövdenin önüne yazar; yönlendirmede birden çok başlık bloğu olur
    basliklar, govde = {}, ham
    while govde[:5] == b"HTTP/":
        j = govde.find(b"\r\n\r\n")
        k = 4
        if j < 0:
            j = govde.find(b"\n\n"); k = 2
        if j < 0:
            break
        blok, govde = govde[:j].decode("latin-1", "ignore"), govde[j + k:]
        basliklar = {}
        for satir in blok.splitlines()[1:]:
            if ":" in satir:
                a, v = satir.split(":", 1)
                basliklar[a.strip().lower()] = v.strip()
    if govde[:2] == b"\x1f\x8b":
        try:
            govde = gzip.decompress(govde)
        except Exception:
            pass
    return {"kod": int(son[0]) if son[0].isdigit() else 0, "son_url": son[1] if len(son) > 1 else url,
            "basliklar": basliklar, "govde": govde if bayt else govde.decode("utf-8", "ignore")}


def getir(url, saniye=40, deneme=3, bekle=4, ek_baslik=()):
    """URL'yi curl ile indirir. Cloudflare doğrulama sayfası gelirse bekleyip yeniden dener."""
    govde = ""
    for i in range(deneme):
        govde = istek(url, saniye, ek_baslik)["govde"]
        if govde and not cloudflare_mi(govde):
            return govde
        if i < deneme - 1:
            time.sleep(bekle * (i + 1))
    return govde


def getir_json(url, saniye=40, ek_baslik=("Accept: application/json",)):
    try:
        return json.loads(getir(url, saniye, deneme=1, ek_baslik=ek_baslik))
    except Exception:
        return None


def durum_kodu(url, saniye=25):
    _bekle(url)
    r = subprocess.run(["curl", "-sSL", "-o", "/dev/null", "-m", str(saniye), "-A", UA,
                        "-w", "%{http_code}", url], capture_output=True, text=True)
    return r.stdout.strip()


# --- Türkçe normalizasyon (Boyner skill'indeki düzeltilmiş hâl; aynen korunur) --------------------

# Kelimenin niyetini değiştirmeyen ekler: "kadın mont modelleri" ile "kadın mont" aynı sayfanın kelimesidir.
# Markanın kendi adı (ör. "boyner", "flormar") profildeki marka_adi / dolgu_ek ile eklenir.
DOLGU = {"model", "modelleri", "modeli", "modeller", "cesitleri", "cesit", "cesidi", "fiyatlari", "fiyat",
         "fiyati", "urunleri", "urun", "urunler", "ve", "ile", "icin", "x", "online", "satin", "al"}
# Sahiplik dışı bırakılacak kalıplar: kampanya, gezinme ve konu dışı sorgular
KAPSAM_DISI_KALIP = (r"\b(1 alana|2 al|bedava|defolu|toptan|indirim|outlet|kampanya|ikinci el|2 el|sahibinden|"
                     r"ruyada|eksi|kadinlar kulubu|sikayet|guvenilir mi|com tr|nerede satilir|magazalari?)\b")
RENKLER = {"siyah", "beyaz", "kirmiz", "mavi", "lacivert", "yesil", "sar", "pembe", "mor", "gri", "bej", "kahvereng",
           "bordo", "turuncu", "haki", "ekru", "krem", "fume", "antrasit", "vizon", "lila", "gumus", "altin"}
ES_ANLAM = {"bayan": "kadin", "bay": "erkek", "kiz": "kiz", "tisort": "t shirt", "tshirt": "t shirt",
            "sneakers": "sneaker", "jean": "jean", "kot": "jean"}
# Pazar yerleri ve genel perakendeciler: her markada rakip sayılır (sitede sayfası yoksa).
PAZAR_YERLERI = ["trendyol", "hepsiburada", "n11", "amazon", "ciceksepeti", "pttavm", "morhipo", "modanisa",
                 "boyner", "beymen", "a101", "bim", "migros", "teknosa", "mediamarkt", "vatan", "gratis", "watsons",
                 "rossmann", "sephora", "koctas", "ikea", "english home", "madame coco", "lcw", "lc waikiki"]


def duz(s):
    """Türkçe harfleri ASCII'ye katlar, küçültür; slug ile kelimeyi aynı zemine indirir."""
    s = (s or "").replace("İ", "i").replace("I", "i").lower()
    s = s.translate(str.maketrans("çğıöşüâîû", "cgiosuaiu"))
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def kok(w):
    """Çok hafif gövdeleme: çoğul ve iyelik eklerini atar, ünsüz yumuşamasını geri alır
    (montlar, montu, montlari -> mont · ayakkabisi, ayakkabi -> ayakkab · kulakligi -> kulaklik)."""
    for ek in ("lari", "leri", "lar", "ler"):
        if w.endswith(ek) and len(w) - len(ek) >= 3:
            w = w[:-len(ek)]
            break
    if len(w) >= 6 and w[-2:] in ("si", "su") and w[-3] in "aeiou":
        w = w[:-2]                                   # ayakkabi-si, corab-i gibi 3. tekil iyelik
    if len(w) >= 6 and w[-2:] in ("gi", "gu"):
        return w[:-2] + "k"                          # kulaklig-i -> kulaklik, gozlug-u -> gozluk
    if len(w) >= 5 and w[-2:] in ("bi", "bu"):
        return w[:-2] + "p"                          # corab-i -> corap; ayakkabi -> ayakkap (tutarlı kalır)
    if len(w) >= 5 and w[-1] == "b":
        return w[:-1] + "p"
    if len(w) >= 5 and w[-1] in "iu" and w[-2] not in "aeiou":
        w = w[:-1]
    return w


def kumeler(metin):
    """Kelime ya da slug -> niyet taşıyan kök kümesi (dolgu ekleri atılmış, eş anlamlılar birleştirilmiş)."""
    dolgu = _DOLGU_AKTIF if _DOLGU_AKTIF is not None else DOLGU
    out = set()
    for t in duz(metin).split():
        if t in dolgu or kok(t) in dolgu:
            continue
        k = kok(t)
        out.update(ES_ANLAM.get(k, ES_ANLAM.get(t, k)).split())
    return frozenset(out)


# --- cinsiyet --------------------------------------------------------------------------------------

GENEL_CINSIYET = {"kadin": "Kadın", "erkek": "Erkek", "kiz-cocuk": "Kız Çocuk", "erkek-cocuk": "Erkek Çocuk",
                  "cocuk": "Çocuk", "kiz-bebek": "Kız Bebek", "erkek-bebek": "Erkek Bebek", "bebek": "Bebek",
                  "unisex": "Unisex", "bayan": "Kadın"}
GENEL_SEKME = {"kadin": "Kadın", "bayan": "Kadın", "erkek": "Erkek", "kiz-cocuk": "Çocuk", "erkek-cocuk": "Çocuk",
               "cocuk": "Çocuk", "kiz-bebek": "Bebek", "erkek-bebek": "Bebek", "bebek": "Bebek", "unisex": "Kategori"}


def cinsiyetler():
    """Kimlik/slug -> cinsiyet etiketi. Profilde tanım varsa o, yoksa genel Türkçe slug kelimeleri."""
    return AYAR.get("cinsiyet_kimlikleri") or GENEL_CINSIYET


def cinsiyet_etiketi(g):
    return (cinsiyetler().get(g) or GENEL_CINSIYET.get(g)) if g else None


def cinsiyet_kokleri():
    return frozenset(k for g in set(cinsiyetler().values()) | set(GENEL_CINSIYET.values()) for k in kumeler(g)) \
        | kumeler("bebek çocuk kız")


def sekme_adi_cinsiyet(g):
    if not g:
        return None
    return (AYAR.get("cinsiyet_sekme") or {}).get(g) or GENEL_SEKME.get(g) or cinsiyet_etiketi(g)


# --- URL çözümleme ve sınıflandırma ---------------------------------------------------------------

LISTE_TIPLERI = ("kategori", "cinsiyet_kategori", "marka", "marka_kategori", "marka_cinsiyet",
                 "marka_cinsiyet_kategori", "kategori_filtre", "cinsiyet_kategori_filtre", "marka_filtre",
                 "marka_kategori_filtre", "marka_cinsiyet_filtre", "marka_cinsiyet_kategori_filtre", "arama")
# Filtre sayılmayan sorgu parametreleri (izleme, sayfalama, sıralama)
SORGU_HARIC = re.compile(r"^(utm_\w+|gclid|fbclid|srsltid|yclid|msclkid|_ga|ref|page|sayfa|pg|p|sort|siralama|"
                         r"orderby|order|sorting|pagesize|limit|view|_pos|_sid|_ss|variant|currency|lang)$", re.I)
DIL_ONEK = {"en", "de", "fr", "ar", "ru", "es", "it", "nl", "az", "ka", "ro", "bg", "el", "uk", "en-us", "en-gb",
            "de-de", "ar-sa", "en-tr", "tr-en"}
SEZ_URUN = re.compile(r"/products?/[^/]+|/p/[^/]+|/urun/[^/]+|-p-\d+|-p\d{4,}(?:\.html)?$|/p/?$|"
                      r"-\d{8,14}/?$|/[^/]*-(?:pm|prd)-?\d+|/product-detail/|/urun-detay/", re.I)
SEZ_ICERIK = {"blog", "blogs", "mag", "content", "icerik", "rehber", "dergi", "haber", "haberler", "makale",
              "makaleler", "stil-rehberi", "journal", "magazine", "news", "article", "articles", "tavsiyeler"}
SEZ_DIGER = re.compile(r"(^|[/-])(hakkimizda|hakkinda|iletisim|bize-ulasin|kvkk|gizlilik|cerez|sozlesme|"
                       r"kosullar|yardim|sss|sikca-sorulan|magazalar|magazalarimiz|kariyer|uyelik|hesabim|account|"
                       r"login|giris|uye-ol|kayit|sepet|cart|checkout|siparis|iade|kargo|biz-kimiz|kunye|"
                       r"bilgi-toplumu|aydinlatma|politika|wishlist|favoriler|pages)([/-]|$)", re.I)
SEZ_MARKA = {"marka", "markalar", "brand", "brands", "markas"}
SEZ_KATEGORI = {"c", "collections", "collection", "kategori", "kategoriler", "category", "categories", "k",
                "koleksiyon", "list", "liste", "shop", "magaza"}
YAPISAL = SEZ_KATEGORI | SEZ_MARKA | {"tr", "tr-tr"}
IPUCU = [(r"product|urun|produkt|\bitems?\b|devices?\b|cihaz", "urun"), (r"blog|post|article|haber|news|journal|content", "icerik"),
         (r"brand|marka|vendor|manufacturer", "marka"),
         (r"categor|kategori|collection|koleksiyon|listing|special", "kategori"),
         (r"flatpage|static|cms|\bpages?\b|pages_|sayfa", "diger")]


def sitemap_ipucu(ad):
    """Sitemap dosya adından tip ipucu: sitemap-products-1.xml -> urun, sitemap_collections_1 -> kategori."""
    ad = duz(urlsplit(ad).path + " " + (urlsplit(ad).query or ""))   # yol da ipucu taşır: /api/categories/.../sitemap.xml
    ad = re.sub(r"sitemaps?|xml|gz", " ", ad)          # "sitemap" kelimesi "item" içerir; ipucu yalnız dosya adından
    for desen, tip in IPUCU:
        if re.search(desen, ad):
            return tip
    return None


def temiz_sorgu(q):
    """Filtre değerini taşıyan parametreleri tutar; izleme, sayfalama ve sıralama atılır."""
    parca = [(k, v) for k, v in parse_qsl(q or "", keep_blank_values=False) if not SORGU_HARIC.match(k)]
    return urlencode(parca, safe=",+:") if parca else ""


def _tip(b, g, c, q):
    parca = [x for x, v in (("marka", b), ("cinsiyet", g), ("kategori", c)) if v]
    return ("_".join(parca) or "kategori") + ("_filtre" if q else "")


def _cinsiyet_ayir(tokenler):
    """['kadin','dis','giyim'] -> ('kadin', ['dis','giyim']). İkili cinsiyet önce ('kiz cocuk')."""
    anahtarlar = cinsiyetler()
    for i in range(len(tokenler) - 1):
        ikili = tokenler[i] + "-" + tokenler[i + 1]
        if ikili in GENEL_CINSIYET or ikili in anahtarlar:
            return ikili, tokenler[:i] + tokenler[i + 2:]
    for i, t in enumerate(tokenler):
        if t in GENEL_CINSIYET or t in anahtarlar:
            return t, tokenler[:i] + tokenler[i + 1:]
    return None, tokenler


def _kimlik_ayikla(son):
    """Slug sonundaki kimliği ayırır: mont-c123 -> ('mont', '123') · kadin-dis-giyim-691 -> (..., '691')."""
    son = re.sub(r"\.(html?|aspx|php)$", "", son)
    m = re.match(r"^(.*?)[-_](?:c|cat|k)?-?(\d{2,})$", son)
    if m and m.group(1):
        return m.group(1), m.group(2)
    return son, None


def _liste_kur(origin, yol, sorgu, segmentler, tip_zorla=None, yontem="sezgisel"):
    """Listeleme adresi için slug, cinsiyet (g), kategori ailesi (c), marka (b) ve tipi kurar."""
    seg = [s for s in segmentler if s.lower() not in YAPISAL]
    b = None
    if segmentler and segmentler[0].lower() in SEZ_MARKA and len(segmentler) >= 2:
        b = segmentler[1].lower()
        seg = segmentler[2:]
        tip_zorla = None
    if not seg and b:
        return {"url": origin + yol + ("?" + sorgu if sorgu else ""), "slug": b,
                "b": b, "g": None, "c": None, "q": sorgu, "tip": _tip(b, None, None, sorgu), "yontem": yontem}
    if not seg:
        return None
    son, kimlik = _kimlik_ayikla(seg[-1])
    g, kalan = _cinsiyet_ayir(son.lower().split("-"))
    ust_g = None
    for s in seg[:-1]:                         # /kadin/giyim/mont: cinsiyet üst segmentte
        sg, sk = _cinsiyet_ayir(s.lower().split("-"))
        if sg and not sk:
            ust_g = sg
    if g and not kalan:                        # /kadin/ sayfası cinsiyet değil, en üst kategoridir
        g, kalan = None, son.lower().split("-")
    g = g or ust_g
    slug = son if not ust_g or ust_g in son else ust_g + "-" + son
    ust = [s.lower() for s in seg[:-1] if _cinsiyet_ayir(s.lower().split("-"))[0] is None
           or _cinsiyet_ayir(s.lower().split("-"))[1]]
    c = kimlik or "/".join(ust + ["-".join(kalan)])
    tip = _tip(b, g, c, sorgu)
    if tip_zorla == "marka" and not b:
        b, c, g = (son.lower(), None, None)
        tip = _tip(b, None, None, sorgu)
    return {"url": origin + yol + ("?" + sorgu if sorgu else ""), "slug": slug, "b": b, "g": g, "c": c,
            "q": sorgu, "tip": tip, "yontem": yontem}


def _desenden(desen, m, origin, yol, ham_sorgu, sorgu):
    gd = {k: v for k, v in m.groupdict().items() if v is not None}
    tip = desen.get("tip", "liste")
    if gd.get("arama"):
        return {"url": origin + yol + "?" + ham_sorgu, "slug": unquote_plus(gd["arama"]).strip(), "b": None,
                "g": None, "c": None, "q": "", "tip": "arama", "yontem": "profil"}
    slug = gd.get("slug") or yol.strip("/").split("/")[-1]
    b, g, c = gd.get("b"), gd.get("g"), gd.get("c")
    kaynak = gd.get("kimlik") or yol
    for ad, kd in (desen.get("kimlik") or {}).items():
        mm = re.search(kd, kaynak)
        if mm:
            b, g, c = (mm.group(1) if ad == "b" else b, mm.group(1) if ad == "g" else g, mm.group(1) if ad == "c" else c)
    q = gd["q"] if "q" in gd else sorgu
    if g is None and desen.get("cinsiyet_slugdan", True) and tip in ("liste", "kategori"):
        g, _ = _cinsiyet_ayir(slug.lower().split("-"))
    if tip in ("liste", "kategori", "marka"):
        if tip == "marka" and not b:
            b = slug
        if tip != "liste" and not c and tip != "marka":
            c = slug                                   # kimliksiz kategori deseni: aile anahtarı slug'dır
        tip = _tip(b, g, c, q)
    return {"url": origin + yol + ("?" + q if q else ""), "slug": slug, "b": b, "g": g, "c": c, "q": q,
            "tip": tip, "yontem": "profil"}


_ENV_TIP = None


def _envanter_tipi(url):
    """Belirsiz kalan adres envanterde varsa (sitemap ipucuyla sınıflanmış) oradaki kayıt kullanılır."""
    global _ENV_TIP
    if _ENV_TIP is None:
        _ENV_TIP = {}
        yol = os.path.join(ONBELLEK_KOK, AYAR.get("domain") or "_", "envanter.json")
        if os.path.exists(yol):
            try:
                for s in json.load(open(yol, encoding="utf-8"))["sayfalar"]:
                    _ENV_TIP[s["url"]] = s
            except Exception:
                pass
    return _ENV_TIP.get(url)


def url_coz(url, ipucu=None):
    """Sitenin adresini parçalar: {url, slug, b (marka), g (cinsiyet), c (kategori ailesi), q (filtre), tip, yontem}.

    Sıra: (1) profildeki url_desenleri, (2) sezgisel kurallar (ürün, arama, içerik, marka, kategori işaretleri),
    (3) sitemap ipucu (envanter kurulurken) ya da envanterdeki kayıt, (4) belirsiz -> tip "diger".
    Alan adı aktif markanınki değilse None döner."""
    if not url:
        return None
    url = url.strip().replace("&amp;", "&")
    kok_ = site()
    if not kok_:
        return None
    if url.startswith("//"):
        url = "https:" + url
    if not re.match(r"https?://", url):
        url = urljoin(kok_, url.lstrip("/") if not url.startswith("/") else url)
    p = urlsplit(url)
    if _alan(p.netloc) != AYAR.get("domain"):
        return None
    ku = urlsplit(kok_)
    origin = f"{ku.scheme}://{ku.netloc}"
    yol = re.sub(r"/{2,}", "/", p.path or "/")
    ham_sorgu = p.query
    sorgu = temiz_sorgu(ham_sorgu)
    goreli = yol + ("?" + ham_sorgu if ham_sorgu else "")
    for desen in AYAR.get("url_desenleri") or []:
        m = re.search(desen["desen"], goreli)
        if m:
            if desen.get("tip") in ("urun", "icerik", "diger"):
                return {"url": origin + yol, "slug": yol.strip("/").split("/")[-1], "b": None, "g": None, "c": None,
                        "q": "", "tip": desen["tip"], "yontem": "profil"}
            r = _desenden(desen, m, origin, yol, ham_sorgu, sorgu)
            if r:
                return r
    if AYAR.get("yalniz_desen"):
        return None              # profil yalnız kendi desenlerini kabul ediyor (ör. Boyner): eşleşmeyen adres yok sayılır
    return _sezgisel(origin, yol, ham_sorgu, sorgu, ipucu)


def _sezgisel(origin, yol, ham_sorgu, sorgu, ipucu):
    seg = [s for s in yol.split("/") if s]
    alt = [s.lower() for s in seg]
    duz_yol = origin + yol

    def sabit(tip, yontem, slug=None):
        return {"url": duz_yol, "slug": slug or (seg[-1] if seg else ""), "b": None, "g": None, "c": None,
                "q": "", "tip": tip, "yontem": yontem}
    if alt and alt[0] in DIL_ONEK and alt[0] != (AYAR.get("language_code") or "tr"):
        return sabit("diger", "sezgisel:dil-oneki")
    qd = dict(parse_qsl(ham_sorgu or ""))
    aranan = qd.get("q") or qd.get("query") or qd.get("search") or qd.get("aranan") or qd.get("text")
    if aranan and alt[:2] == ["collections", "vendors"]:            # Shopify marka (vendor) listesi
        return {"url": duz_yol + "?q=" + aranan, "slug": aranan, "b": duz(aranan).replace(" ", "-"), "g": None,
                "c": None, "q": "", "tip": "marka", "yontem": "sezgisel:shopify-vendor"}
    if (alt and alt[-1] in ("search", "arama", "ara", "s", "searchresults")) or (aranan and (not seg or alt[0] in ("search", "arama", "ara"))):
        return {"url": duz_yol + "?" + ham_sorgu, "slug": unquote_plus(aranan or ""), "b": None, "g": None,
                "c": None, "q": "", "tip": "arama", "yontem": "sezgisel:arama"}
    if not seg:
        return sabit("diger", "sezgisel:anasayfa", "anasayfa")
    if alt[0] == "collections" and len(alt) >= 3 and alt[2] == "products":
        return sabit("urun", "sezgisel:shopify-urun")
    if SEZ_URUN.search(yol):
        return sabit("urun", "sezgisel:urun-deseni")
    if alt[0] in SEZ_ICERIK or (len(alt) > 1 and alt[0] in ("tr", "tr-tr") and alt[1] in SEZ_ICERIK):
        return sabit("icerik", "sezgisel:icerik-oneki")
    if SEZ_DIGER.search(yol):
        return sabit("diger", "sezgisel:kurumsal-sayfa")
    if alt[0] in SEZ_MARKA and len(alt) >= 2:
        return _liste_kur(origin, yol, sorgu, seg, yontem="sezgisel:marka-oneki")
    if alt[0] in SEZ_KATEGORI or re.search(r"-c-?\d+(?:\.html)?/?$", yol) or (alt[0] in ("tr",) and len(alt) > 1):
        if alt[0] == "collections" and len(alt) == 2 and alt[1] in ("all", "vendors", "types"):
            return sabit("diger", "sezgisel:shopify-genel")
        return _liste_kur(origin, yol, sorgu, seg, yontem="sezgisel:kategori-oneki")
    if ipucu in ("urun", "icerik", "diger"):
        return sabit(ipucu, "sitemap-ipucu")
    if ipucu in ("kategori", "marka"):
        return _liste_kur(origin, yol, sorgu, seg, tip_zorla=ipucu, yontem="sitemap-ipucu")
    env = _envanter_tipi(duz_yol + ("?" + sorgu if sorgu else ""))
    if env:
        return {k: env.get(k) for k in ("url", "slug", "b", "g", "c", "q", "tip")} | {"yontem": "envanter"}
    r = _liste_kur(origin, yol, sorgu, seg, yontem="belirsiz")
    if r:
        r["tip"] = "diger"
    return r


def liste_mi(p):
    return bool(p) and p.get("tip") in LISTE_TIPLERI


def slug_adi(url):
    """Belge adı için kısa ad: kadin-mont, fondoten, kadin-bot."""
    p = url_coz(url)
    if p and p.get("slug"):
        return re.sub(r"[^a-z0-9]+", "-", duz(p["slug"])).strip("-")
    return re.sub(r"\W+", "-", urlsplit(url).path).strip("-") or "sayfa"


def rakip_listesi():
    """Profildeki rakip perakendeciler + pazar yerleri; markanın kendisi hariç."""
    kendi = duz(AYAR.get("marka_adi") or "")
    liste = list(dict.fromkeys([duz(x) for x in (AYAR.get("rakip_perakendeciler") or []) + PAZAR_YERLERI]))
    return [x for x in liste if x and x != kendi]
