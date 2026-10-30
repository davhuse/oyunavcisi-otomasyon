"""Steam+Epic'teki tüm sağlam indirimli/taze oyunları birleştirir. Her 4 paylaşımdan 1'i TOPLU (4-6 oyunluk ızgara),
diğerleri TEK oyunluk (kapak tam dolu). En yüksek indirimli oyun(lar) önce seçilir. -> out/post.json + hikaye.
Günlük paylaşım sayısı GUNLUK_LIMIT'i (gate.py) geçemez. Taze: son TAZE_GUN günde bu oyun paylaşılmamış ya da fiyatı değişmiş.
Oyun/fiyat yalnızca topla.py'nin doğruladığı veriden gelir."""
import json, os, shutil, subprocess, sys, time
from datetime import date, datetime, timedelta, timezone

KAYNAKLAR = ["steam", "epic"]
ETIKET = {"steam": "#steam #steamsale #pcgaming", "epic": "#epicgames #epicgamesstore #ücretsizoyun"}
TAZE_GUN = 5
TOPLU_HER = 4  # her 4 paylaşımdan 1'i toplu (ızgara) olsun
TOPLU_OYUN = 6  # toplu gönderide en fazla kaç oyun
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


def caption_tek(k, baslik, u):
    eski = f' (eski ${u["eski_fiyat"]}, %{u["indirim"]} indirim)' if u.get("indirim") else ""
    satir = [f'{baslik["market"]} · {u["ad"]}', "", f'${u["fiyat"]}{eski}']
    if u.get("not"):
        satir.append(u["not"])
    satir += ["", f'🔗 {u["link"]}', "", f'Kontrol: {baslik["kontrol_tarihi"]}. Fiyatlar değişebilir, kampanyalar önceden haber vermeden bitebilir.',
              f'Kaynak: {baslik["kaynak_url"]}', "", f'#indirim #oyunindirimi #oyunavcisi {ETIKET[k]}']
    return "\n".join(satir)


def caption_toplu(secim):  # secim: [(k, baslik, u), ...]
    satir = ["Günün fırsatları", ""]
    for k, baslik, u in secim:
        eski = f' (eski ${u["eski_fiyat"]}, %{u["indirim"]} indirim)' if u.get("indirim") else ""
        satir.append(f'• {baslik["market"]} · {u["ad"]}: ${u["fiyat"]}{eski}')
    satir += ["", "Linkler yorumlarda/profilde.", "", "Kontrol: " + datetime.now(TR).strftime("%d.%m.%Y") + ". Fiyatlar değişebilir, kampanyalar önceden haber vermeden bitebilir.",
              "", "#indirim #oyunindirimi #oyunavcisi #steam #epicgames"]
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

    toplu_mu = (len(gecmis) + 1) % TOPLU_HER == 0 and len(aday) >= 4  # 4'te 1; en az 4 taze oyun yoksa yine tekli kal
    secim = aday[:TOPLU_OYUN] if toplu_mu else aday[:1]

    damga = time.strftime("%Y%m%d%H%M")
    shutil.rmtree("out/yayin", ignore_errors=True)
    os.makedirs("out/yayin")
    k0 = secim[0][1]  # render.py'nin genel başlık (market/kaynak_url) alanları için ilk oyunun kaynağını kullan
    d_post = {**secim[0][2], "urunler": [u for _, _, _, u in secim]}
    json.dump(d_post, open(f"veri/{k0}_post.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    subprocess.run([sys.executable, "render.py", f"veri/{k0}_post.json"], check=True)
    ad = sorted((f for f in os.listdir(f"out/{k0}_post") if f.endswith(".jpg") and f != "hikaye.jpg"),
               key=lambda f: int(f.split(".")[0]))
    gorseller = []
    for i, f in enumerate(ad, 1):
        shutil.copy(f"out/{k0}_post/{f}", f"out/yayin/{damga}_{k0}_{i}.jpg")
        gorseller.append(f"{damga}_{k0}_{i}.jpg")
    hikaye = f"{damga}_{k0}_hikaye.jpg"
    shutil.copy(f"out/{k0}_post/hikaye.jpg", f"out/yayin/{hikaye}")

    if toplu_mu:
        cap = caption_toplu([(k, d, u) for _, k, d, u in secim])
        kaynak_etiket = "toplu"
    else:
        _, k, d, u = secim[0]
        cap = caption_tek(k, d, u)
        kaynak_etiket = k

    json.dump({"kaynak": kaynak_etiket, "gorseller": gorseller, "hikaye": hikaye, "caption": cap,
               "urunler": [[anahtar(k, u), u["fiyat"]] for _, k, _, u in secim]},
              open("out/post.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Seçilen: {'TOPLU ' + str(len(secim)) + ' oyun' if toplu_mu else secim[0][3]['ad']} "
          f"({'%' + str(secim[0][0]) + ' en yüksek indirim' if toplu_mu else '%' + str(secim[0][0]) + ' indirim'})")
    cikis("true")
