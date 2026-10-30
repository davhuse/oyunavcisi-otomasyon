"""Sıradaki kaynağı (steam/epic) ve henüz paylaşılmamış oyunları seçer, görselleri ve caption'ı üretir -> out/post.json
Kaynak: en uzun süredir paylaşılmayan ve en az 4 'taze' oyunu olan. Taze: son TAZE_GUN günde paylaşılmamış ya da fiyatı değişmiş.
Oyun/fiyat yalnızca topla.py'nin Steam/Epic API'sinden doğruladığı veriden gelir."""
import json, os, shutil, subprocess, sys, time
from datetime import date, datetime, timedelta, timezone

KAYNAKLAR = ["steam", "epic"]
ETIKET = {"steam": "#steam #steamsale #pcgaming", "epic": "#epicgames #epicgamesstore #ücretsizoyun"}
OYUN_SAYISI = 8
TAZE_GUN = 5
TR = timezone(timedelta(hours=3))


def yukle(f, bos):
    return json.load(open(f, encoding="utf-8")) if os.path.exists(f) else bos


gecmis = yukle("gecmis.json", [])
paylasilan = yukle("paylasilan.json", {})  # "kaynak|oyun adı" -> "YYYY-MM-DD|fiyat"


def anahtar(k, u):
    return f"{k}|{u['ad']}"


def taze(k, u, bugun):
    kayit = paylasilan.get(anahtar(k, u))
    if not kayit:
        return True
    gun, fiyat = kayit.split("|")
    return fiyat != u["fiyat"] or (bugun - date.fromisoformat(gun)).days >= TAZE_GUN


def son(k):
    t = [g["tarih"] for g in gecmis if g["kaynak"] == k]
    return t[-1] if t else ""


def caption(d, k):
    satir = [f'{d["market"]} · {d["baslik"]} ({d["gecerlilik"]})', ""]
    for u in d["urunler"][:4]:
        eski = f' (eski ${u["eski_fiyat"]}, %{u["indirim"]} indirim)' if u.get("indirim") else ""
        satir.append(f'• {u["ad"]}: ${u["fiyat"]}{eski}')
    if len(d["urunler"]) > 4:
        satir.append(f'…ve {len(d["urunler"]) - 4} oyun daha, kaydır.')
    satir += ["", f'Kontrol: {d["kontrol_tarihi"]}. Fiyatlar değişebilir, kampanyalar önceden haber vermeden bitebilir.',
              f'Kaynak: {d["kaynak_url"]}', "", f'#indirim #oyunindirimi #oyunavcisi {ETIKET[k]}']
    return "\n".join(satir)


def cikis(devam):
    if os.environ.get("GITHUB_OUTPUT"):
        open(os.environ["GITHUB_OUTPUT"], "a").write(f"devam={devam}\n")


if __name__ == "__main__":
    subprocess.run([sys.executable, "topla.py"], check=True)
    if not any(os.path.exists(f"veri/{k}.json") for k in KAYNAKLAR):
        cikis("false")
        sys.exit("Steam/Epic'ten veri alınamadı: API değişmiş ya da erişim engellenmiş olabilir")
    bugun = datetime.now(TR).date()
    devam = "false"
    for k in sorted(KAYNAKLAR, key=son):
        if not os.path.exists(f"veri/{k}.json"):
            continue
        d = json.load(open(f"veri/{k}.json", encoding="utf-8"))
        secilen = [u for u in d["urunler"] if taze(k, u, bugun)][:OYUN_SAYISI]
        if len(secilen) < 1:  # Epic'te günde tek ücretsiz oyun olabilir; 1 bile yeni içerikse paylaş
            print(f"{k}: yeni oyun yok, atlandı")
            continue
        d["urunler"] = secilen
        json.dump(d, open(f"veri/{k}_post.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        subprocess.run([sys.executable, "render.py", f"veri/{k}_post.json"], check=True)
        damga = time.strftime("%Y%m%d%H%M")
        shutil.rmtree("out/yayin", ignore_errors=True)
        os.makedirs("out/yayin")
        ad = sorted(f for f in os.listdir(f"out/{k}_post") if f.endswith(".jpg") and f != "hikaye.jpg")
        gorseller = []
        for i, f in enumerate(ad, 1):
            shutil.copy(f"out/{k}_post/{f}", f"out/yayin/{damga}_{k}_{i}.jpg")
            gorseller.append(f"{damga}_{k}_{i}.jpg")
        hikaye = f"{damga}_{k}_hikaye.jpg"
        shutil.copy(f"out/{k}_post/hikaye.jpg", f"out/yayin/{hikaye}")
        json.dump({"kaynak": k, "gorseller": gorseller, "hikaye": hikaye, "caption": caption(d, k),
                   "urunler": [[anahtar(k, u), u["fiyat"]] for u in secilen]},
                  open("out/post.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"Seçilen kaynak: {k}, {len(secilen)} oyun, {len(gorseller)} görsel")
        devam = "true"
        break
    else:
        print("Paylaşılacak yeni içerik yok")
    cikis(devam)
