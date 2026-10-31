"""Steam özel indirimler + Epic ücretsiz oyunlar -> veri/<kaynak>.json. Fiyatlar Steam/Epic API'sinden, uydurulmaz.
Yetişkin/cinsel içerikli oyunlar elenir: Steam content_descriptors 3 (Adult Only Sexual Content) veya 4 (Frequent Nudity/Sexual Content)
içeren ya da required_age>=18 olan oyunlar atılır (bkz. https://partner.steamgames.com/doc/store/application/depots#content_descriptors)."""
import html, json, os, re, sys, time
import requests

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}
YETISKIN_DESC = {3, 4}
MIN_INDIRIM = 30  # bundan düşük indirimler "sağlam" sayılmaz, paylaşılmaz (ücretsiz oyun %100 sayıldığı için her zaman geçer)
N = 25


def al(url, **k):
    for d in range(3):
        try:
            r = requests.get(url, headers={**H, **k.pop("headers", {})}, timeout=25, **k)
            if r.ok:
                return r
        except requests.RequestException:
            pass
        time.sleep(2 * (d + 1))
    raise RuntimeError(f"Ulaşılamadı: {url}")


def uygun_mu(d):
    """Steam appdetails'teki bir oyun yetişkin/cinsel içerikli mi?"""
    if d.get("required_age", 0) and int(d["required_age"]) >= 18:
        return False
    return not (YETISKIN_DESC & set(d.get("content_descriptors", {}).get("ids", [])))


def oyun(ad, fiyat, eski, gorsel, link, not_=""):
    ok = bool(ad) and 0 <= fiyat < 10000 and gorsel and link  # 0 = ücretsiz oyun, geçerli
    y = round((1 - fiyat / eski) * 100) if ok and eski and eski > fiyat else None
    return {"ad": ad, "fiyat": f"{fiyat:.2f}", "eski_fiyat": f"{eski:.2f}" if y else "", "indirim": str(y) if y else "",
            "not": not_, "gorsel_url": gorsel, "link": link, "dogrulandi": ok and y is not None}


def steam():
    j = al("https://store.steampowered.com/api/featuredcategories?cc=tr&l=turkish").json()
    ids = [it["id"] for it in j.get("specials", {}).get("items", [])]
    for bas in (0, 100):  # öne çıkan liste yalnızca ~10 oyun; indirimli aramadan havuzu genişlet (id logo adresinde)
        try:
            for it in al("https://store.steampowered.com/search/results/", params={"specials": 1, "json": 1, "cc": "tr", "l": "turkish", "count": 100, "start": bas}).json()["items"]:
                m = re.search(r"/apps/(\d+)/", it.get("logo", ""))
                if m and int(m.group(1)) not in ids:
                    ids.append(int(m.group(1)))
        except Exception:
            pass  # arama çalışmazsa öne çıkan listeyle devam
    out = []
    for i in ids[:150]:
        if sum(1 for o in out if o["dogrulandi"] and int(o["indirim"] or 0) >= MIN_INDIRIM) >= N:
            break
        try:
            r = al("https://store.steampowered.com/api/appdetails", params={"appids": i, "cc": "tr", "l": "turkish"}).json()
            d = r.get(str(i), {}).get("data")
        except Exception:
            d = None
        if not d or not uygun_mu(d) or not d.get("price_overview"):
            continue
        p = d["price_overview"]
        out.append(oyun(d["name"], p["final"] / 100, p["initial"] / 100, [f"https://cdn.akamai.steamstatic.com/steam/apps/{i}/library_600x900_2x.jpg",
                         f"https://cdn.akamai.steamstatic.com/steam/apps/{i}/library_600x900.jpg", d.get("header_image", "")],
                        f"https://store.steampowered.com/app/{i}/"))
        time.sleep(0.3)  # Steam'i yormamak için
    return {"market": "Steam", "tema": "oyun", "baslik": "Özel indirimler", "gecerlilik": "Steam mağazası",
            "kaynak_url": "store.steampowered.com", "para": "USD"}, out


def epic():
    j = al("https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=tr").json()
    out = []
    for e in j["data"]["Catalog"]["searchStore"]["elements"]:
        teklif = (e.get("promotions") or {}).get("promotionalOffers") or []
        fiyat = e.get("price", {}).get("totalPrice", {})
        if not teklif or fiyat.get("discountPrice", -1) != 0:  # yalnızca şu an gerçekten 0 TL olanlar
            continue
        eski = fiyat.get("originalPrice", 0) / 100
        gorsel = [im["url"] for tip in ("OfferImageTall", "OfferImageWide", "Thumbnail") for im in e.get("keyImages", []) if im.get("type") == tip]
        slug = (e.get("catalogNs", {}).get("mappings") or [{}])[0].get("pageSlug") or e.get("urlSlug") or e.get("productSlug", "")
        link = f"https://store.epicgames.com/tr/p/{slug}" if slug else ""
        if not link:
            continue
        out.append(oyun(e["title"], 0.0, eski, gorsel, link, "Sınırlı süre ücretsiz"))
    return {"market": "Epic Games", "tema": "oyun", "baslik": "Şu an ücretsiz", "gecerlilik": "Sınırlı süre",
            "kaynak_url": "epicgames.com", "para": "USD"}, out


KAYNAKLAR = {"steam": steam, "epic": epic}

if __name__ == "__main__":
    assert uygun_mu({"required_age": 0, "content_descriptors": {"ids": [1, 2, 5]}}) is True  # GTA gibi: şiddet var, cinsel içerik yok
    assert uygun_mu({"required_age": 0, "content_descriptors": {"ids": [1, 3, 4, 5]}}) is False  # cinsel içerik descriptor'ı
    assert uygun_mu({"required_age": 18, "content_descriptors": {"ids": []}}) is False  # 18+ yaş sınırı
    os.makedirs("veri", exist_ok=True)
    for k in (sys.argv[1:] or KAYNAKLAR):
        try:
            baslik, ham = KAYNAKLAR[k]()
        except Exception as e:
            print(f"{k}: HATA {e}")
            continue
        iyi = [o for o in ham if o["dogrulandi"] and int(o.get("indirim") or 0) >= MIN_INDIRIM][:N]
        os.makedirs(f"gorseller/{k}", exist_ok=True)
        for i, o in enumerate(iyi, 1):
            try:
                for url in filter(None, o.pop("gorsel_url")):  # en yüksek çözünürlüklü dikey görselden başla, olmazsa sıradakine düş
                    try:
                        r = al(url)
                    except RuntimeError:
                        continue
                    if r.headers.get("content-type", "").startswith("image"):
                        break
                else:
                    raise RuntimeError("görsel yok")
                yol = f"gorseller/{k}/{i}.img"
                open(yol, "wb").write(r.content)
                o["gorsel"] = yol
            except Exception:
                o["dogrulandi"] = False
        iyi = [o for o in iyi if o["dogrulandi"]]
        veri = {**baslik, "kontrol_tarihi": time.strftime("%d.%m.%Y"), "demo": False, "urunler": iyi}
        json.dump(veri, open(f"veri/{k}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{k}: okunan {len(ham)}, uygun+doğrulanan {len(iyi)}")
