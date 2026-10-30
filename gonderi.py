"""Steam+Epic'teki tüm sağlam indirimli/taze oyunları birleştirir, en yüksek indirimli olanı seçip tek oyunluk
gönderi + hikaye üretir -> out/post.json. Günlük paylaşım sayısı GUNLUK_LIMIT'i (gate.py) geçemez.
Taze: son TAZE_GUN günde bu oyun paylaşılmamış ya da fiyatı değişmiş. Oyun/fiyat yalnızca topla.py'nin doğruladığı veriden gelir."""
import json, os, shutil, subprocess, sys, time
from datetime import date, datetime, timedelta, timezone

KAYNAKLAR = ["steam", "epic"]
ETIKET = {"steam": "#steam #steamsale #pcgaming", "epic": "#epicgames #epicgamesstore #ücretsizoyun"}
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


def caption(k, baslik, u):
    eski = f' (eski ${u["eski_fiyat"]}, %{u["indirim"]} indirim)' if u.get("indirim") else ""
    satir = [f'{baslik["market"]} · {u["ad"]}', "", f'${u["fiyat"]}{eski}']
    if u.get("not"):
        satir.append(u["not"])
    satir += ["", f'🔗 {u["link"]}', "", f'Kontrol: {baslik["kontrol_tarihi"]}. Fiyatlar değişebilir, kampanyalar önceden haber vermeden bitebilir.',
              f'Kaynak: {baslik["kaynak_url"]}', "", f'#indirim #oyunindirimi #oyunavcisi {ETIKET[k]}']
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
    aday = []  # (indirim, kaynak, başlık_bilgisi, oyun)
    for k in KAYNAKLAR:
        if not os.path.exists(f"veri/{k}.json"):
            continue
        d = json.load(open(f"veri/{k}.json", encoding="utf-8"))
        for u in d["urunler"]:
            if taze(k, u, bugun):
                aday.append((int(u.get("indirim") or 0), k, d, u))
    if not aday:
        print("Paylaşılacak yeni/taze oyun yok")
        cikis("false")
        sys.exit(0)
    aday.sort(key=lambda a: -a[0])  # en yüksek indirim önce
    _, k, d, u = aday[0]
    d2 = {**d, "urunler": [u]}
    json.dump(d2, open(f"veri/{k}_post.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    subprocess.run([sys.executable, "render.py", f"veri/{k}_post.json"], check=True)
    damga = time.strftime("%Y%m%d%H%M")
    shutil.rmtree("out/yayin", ignore_errors=True)
    os.makedirs("out/yayin")
    shutil.copy(f"out/{k}_post/1.jpg", f"out/yayin/{damga}_{k}_1.jpg")
    hikaye = f"{damga}_{k}_hikaye.jpg"
    shutil.copy(f"out/{k}_post/hikaye.jpg", f"out/yayin/{hikaye}")
    json.dump({"kaynak": k, "gorseller": [f"{damga}_{k}_1.jpg"], "hikaye": hikaye, "caption": caption(k, d, u),
               "urunler": [[anahtar(k, u), u["fiyat"]]]},
              open("out/post.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Seçilen: {k} · {u['ad']} (%{u.get('indirim', 0)} indirim)")
    cikis("true")
