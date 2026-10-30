"""veri/<kaynak>_post.json (tek oyun, dogrulandi=true) -> out/<ad>/*.jpg + hikaye. Fiyat uydurulmaz, Steam/Epic'ten gelir.
Kapak oyunun kendi görseliyle doldurulur (beyaz boşluk yok). Kullanım: python render.py [veri/dosya.json]"""
import base64, html, json, os, sys
from playwright.sync_api import sync_playwright

AC, BG, HI = "#8b5cf6", "#0a0a14", "#22d3ee"  # mor, koyu lacivert, cyan — oyunavcisi markası
KAYNAK = sys.argv[1] if len(sys.argv) > 1 else "urunler.json"
d = json.load(open(KAYNAK, encoding="utf-8"))
for k in ("market", "gecerlilik", "kaynak_url", "kontrol_tarihi"):
    if not d.get(k):
        sys.exit(f"Eksik alan: {k}")
urunler = [u for u in d["urunler"] if u.get("dogrulandi") is True and u.get("ad") and u.get("fiyat") and u.get("gorsel")]
atilan = len(d["urunler"]) - len(urunler)
if not urunler:
    sys.exit("Doğrulanmış, görseli olan oyun yok, gönderi üretilmedi.")
u = urunler[0]  # gonderi.py her çalışmada tek oyun seçip buraya tek elemanlı liste yollar
e = html.escape
FD = "file:///" + os.path.abspath("fontlar").replace("\\", "/")
gorsel_b64 = base64.b64encode(open(u["gorsel"], "rb").read()).decode()


def logo(sinif):
    if not os.path.exists("logo.png"):
        return ""
    return f'<img class="{sinif}" src="data:image/png;base64,{base64.b64encode(open("logo.png", "rb").read()).decode()}">'


def fontface():
    f = ""
    for fam, pre, ws in (("Barlow Condensed", "bc", (700, 800)), ("Inter", "inter", (400, 600))):
        for w in ws:
            for sub, r in (("latin", "U+0000-00FF,U+2000-206F"), ("latin-ext", "U+0100-02AF,U+1E00-1EFF,U+20A0-20CF")):
                f += f"@font-face{{font-family:'{fam}';font-weight:{w};src:url('{FD}/{pre}-{sub}-{w}.woff2');unicode-range:{r}}}"
    return f


TEMEL = fontface() + f"""*{{box-sizing:border-box;margin:0}}
body{{position:relative;overflow:hidden;font-family:'Inter',sans-serif;background:{BG};color:#fff}}
.bc{{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase}}
.kapak{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.koyu{{position:absolute;inset:0;background:linear-gradient(180deg,#00000066 0%,#00000022 32%,#00000099 68%,#000000ea 100%)}}
.pill{{display:inline-block;background:{AC};font-weight:800;font-size:40px;letter-spacing:4px;padding:8px 30px;border-radius:60px;box-shadow:0 6px 20px #0008}}
.rz{{position:absolute;right:50px;top:56px;background:{HI};color:{BG};font-family:'Barlow Condensed';font-weight:800;border-radius:50%;
 width:200px;height:200px;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 10px 30px #0008;transform:rotate(8deg)}}
.rz b{{font-size:84px;line-height:.9}}.rz span{{font-size:30px;letter-spacing:2px}}
.not{{position:absolute;left:56px;top:270px;background:#ffffffe6;color:{BG};font-weight:800;font-size:30px;padding:8px 26px;border-radius:14px}}
.ad{{position:absolute;left:56px;right:56px;bottom:290px;font-family:'Barlow Condensed';text-transform:uppercase;font-weight:800;font-size:84px;line-height:.98;text-shadow:0 6px 20px #000}}
.fy{{position:absolute;left:56px;bottom:150px;display:flex;align-items:flex-end;gap:26px}}
.p{{background:{AC};border-radius:22px;padding:4px 30px 10px;font-family:'Barlow Condensed';font-weight:800;font-size:110px;line-height:1.05;box-shadow:0 8px 24px #0006}}
.es{{font-size:40px;color:#ffffffaa;text-decoration:line-through;margin-bottom:18px}}
.alt{{position:absolute;left:0;right:0;bottom:0;padding:18px 56px 26px;font-size:21px;line-height:1.4;color:#ffffffaa}}
.alt b{{color:#fff}}
"""


def cerceve(genislik, yukseklik, ic):
    return (f'<html lang="tr"><meta charset="utf-8"><style>{TEMEL}body{{width:{genislik}px;height:{yukseklik}px}}</style>'
            f'<img class="kapak" src="data:image/png;base64,{gorsel_b64}"><div class="koyu"></div>{ic}'
            f'<div class="alt"><b>Kaynak:</b> {e(d["kaynak_url"])} · <b>Kontrol:</b> {e(d["kontrol_tarihi"])}<br>'
            f'Fiyatlar değişebilir, kampanyalar önceden haber vermeden bitebilir.</div>')


def govde(logo_sinif):
    rz = f'<div class="rz bc"><span>İNDİRİM</span><b>%{e(u["indirim"])}</b></div>' if u.get("indirim") else ""
    nt = f'<div class="not bc">{e(u["not"])}</div>' if u.get("not") else ""
    es = f'<div class="es">${e(u["eski_fiyat"])}</div>' if u.get("eski_fiyat") else ""
    return (f'<div class="w" style="position:relative;padding:50px 0 0"><span class="pill bc" style="margin-left:56px">{e(d["market"])}</span>{logo(logo_sinif)}</div>'
            f'{rz}{nt}<div class="ad">{e(u["ad"])}</div><div class="fy"><div class="p">${e(u["fiyat"])}</div>{es}</div>')


OUT = "out/" + os.path.splitext(os.path.basename(KAYNAK))[0]
os.makedirs(OUT, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1350})
    sf = "file:///" + os.path.abspath("out/_s.html").replace("\\", "/")
    open("out/_s.html", "w", encoding="utf-8").write(cerceve(1080, 1350, govde("lg")))
    pg.goto(sf)
    pg.evaluate("document.fonts.ready")
    pg.screenshot(path=f"{OUT}/1.jpg", type="jpeg", quality=92)
    pg.set_viewport_size({"width": 1080, "height": 1920})
    open("out/_s.html", "w", encoding="utf-8").write(cerceve(1080, 1920, govde("lg")))
    pg.goto(sf)
    pg.evaluate("document.fonts.ready")
    pg.screenshot(path=f"{OUT}/hikaye.jpg", type="jpeg", quality=90)
    b.close()
print(f"1 görsel + hikaye üretildi; doğrulanmadığı için atılan: {atilan}")
