"""urunler.json -> out/<ad>/*.jpg karusel (1080x1350) + hikaye. Sadece dogrulandi=true oyunlar girer; fiyat uydurulmaz.
Fiyatlar Steam/Epic'ten USD geliyor, TL'ye çevrilmez (döviz kuru tutmayabilir). Kullanım: python render.py [veri/dosya.json]"""
import base64, html, json, os, sys
from playwright.sync_api import sync_playwright

AC, BG, HI = "#8b5cf6", "#0a0a14", "#22d3ee"  # mor, koyu lacivert, cyan — oyunavcisi markası
KAYNAK = sys.argv[1] if len(sys.argv) > 1 else "urunler.json"
d = json.load(open(KAYNAK, encoding="utf-8"))
for k in ("market", "gecerlilik", "kaynak_url", "kontrol_tarihi"):
    if not d.get(k):
        sys.exit(f"Eksik alan: {k}")
urunler = [u for u in d["urunler"] if u.get("dogrulandi") is True and u.get("ad") and u.get("fiyat")]
atilan = len(d["urunler"]) - len(urunler)
if not urunler:
    sys.exit("Doğrulanmış oyun yok, gönderi üretilmedi.")
e = html.escape
FD = "file:///" + os.path.abspath("fontlar").replace("\\", "/")


def foto(u):
    if not u.get("gorsel"):
        return ""
    b = base64.b64encode(open(u["gorsel"], "rb").read()).decode()
    return f'<img class="ph" src="data:image/png;base64,{b}">'


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
body{{width:1080px;height:1350px;position:relative;overflow:hidden;font-family:'Inter',sans-serif;background:{BG};color:#fff}}
.bc{{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase}}
.dmg{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) rotate(-18deg);font-size:150px;font-weight:800;
 color:#ffffff18;border:10px solid #ffffff18;padding:10px 40px;white-space:nowrap;z-index:9}}
.alt{{position:absolute;left:0;right:0;bottom:0;padding:18px 60px 26px;font-size:22px;line-height:1.4;background:#00000066;color:#ffffffbb}}
.alt b{{color:#fff}}
.dots{{position:absolute;left:0;right:0;bottom:122px;text-align:center}}
.dots i{{display:inline-block;width:14px;height:14px;border-radius:50%;margin:0 6px;background:#ffffff44}}
.dots i.on{{width:40px;border-radius:10px;background:{HI}}}
.ph{{object-fit:contain;background:#fff;border-radius:22px}}
.bg{{position:absolute;inset:0;background:radial-gradient(900px 700px at 105% -5%,{AC}55,transparent 70%),radial-gradient(700px 500px at -10% 105%,{HI}33,transparent 70%)}}
.w{{position:relative;padding:60px 60px 0}}
.pill{{display:inline-block;background:{AC};font-weight:800;font-size:44px;letter-spacing:4px;padding:8px 32px;border-radius:60px}}
.lg{{position:absolute;right:56px;top:40px;width:112px;height:112px;border-radius:50%;box-shadow:0 0 30px {AC}88}}
.sy{{position:absolute;right:190px;top:70px;font-size:44px;color:#ffffffaa;font-weight:700}}
.et{{font-size:64px;font-weight:800;color:{HI};letter-spacing:3px;margin-top:46px}}
.hero{{font-size:320px;font-weight:800;line-height:.86;color:#fff;text-shadow:0 10px 60px {AC}}}.hero span{{color:{AC};text-shadow:0 0 50px {AC}88}}
.vr{{font-size:68px;font-weight:800;letter-spacing:2px;margin-top:6px}}
.tar{{display:inline-block;margin-top:26px;background:{HI};color:{BG};font-size:44px;font-weight:800;padding:6px 28px;border-radius:14px}}
.col{{position:absolute;left:0;right:0;top:790px;height:270px}}
.col .t{{position:absolute;width:250px;height:250px;background:#fff;border-radius:34px;box-shadow:0 20px 40px #000a;display:flex;align-items:center;justify-content:center}}
.col .t img{{width:222px;height:222px;object-fit:contain;background:none;border-radius:0}}
.say{{position:absolute;left:60px;bottom:150px;font-size:44px;font-weight:600}}
.say b{{font-size:120px;font-family:'Barlow Condensed';color:{AC};vertical-align:-14px;margin-right:12px}}
.kd{{position:absolute;right:60px;bottom:156px;background:{HI};color:{BG};font-weight:800;font-size:44px;padding:16px 38px;border-radius:60px}}
.g{{display:grid;grid-template-columns:1fr 1fr;gap:26px;margin-top:34px}}
.k{{background:#ffffff12;border:2px solid #ffffff22;border-radius:34px;height:495px;padding:22px 26px 22px;position:relative;display:flex;flex-direction:column;overflow:hidden}}
.k .ph{{height:210px;width:100%;filter:drop-shadow(0 12px 18px #0008);background:#1a1a24}}
.rz{{position:absolute;left:0;top:0;background:{HI};color:{BG};font-family:'Barlow Condensed';font-weight:800;font-size:50px;padding:4px 24px 4px 20px;border-radius:0 0 28px 0;z-index:2}}
.ad{{font-family:'Barlow Condensed';text-transform:uppercase;font-weight:800;font-size:36px;line-height:1.05;margin-top:12px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.fy{{margin-top:auto;display:flex;align-items:flex-end;gap:14px}}
.p{{background:{AC};border-radius:20px;padding:2px 20px 6px;font-family:'Barlow Condensed';font-weight:800;font-size:76px;line-height:1.05;white-space:nowrap}}
.es{{font-size:30px;color:#ffffff99;text-decoration:line-through;margin-bottom:12px;white-space:nowrap}}
.nt{{font-size:22px;color:{HI};margin-top:4px;font-weight:600;min-height:28px}}
.cta{{position:relative;text-align:center;padding-top:70px}}.cta .big{{width:420px;height:420px;border-radius:50%;box-shadow:0 0 90px {AC}99}}
.cta h2{{font-size:116px;font-weight:800;line-height:.95;margin-top:44px}}.cta h2 span{{color:{HI}}}
.cta p{{font-size:42px;color:#ffffffdd;margin-top:22px;line-height:1.35}}
.cta .nk{{margin:34px 70px 0;background:#ffffff12;border-radius:26px;padding:24px 30px;font-size:30px;line-height:1.45;color:#ffffffcc}}
"""
ALT_TXT = (f'<b>Geçerlilik:</b> {e(d["gecerlilik"])} · <b>Kontrol:</b> {e(d["kontrol_tarihi"])} · Fiyatlar değişebilir<br>'
           f'Kaynak: {e(d["kaynak_url"])}')


def cerceve(n, toplam, ic):
    dots = "".join(f'<i class="{"on" if i == n else ""}"></i>' for i in range(1, toplam + 1))
    dm = '<div class="dmg bc">TASLAK</div>' if d.get("demo") else ""
    return (f'<html lang="tr"><meta charset="utf-8"><style>{TEMEL}</style>{ic}'
            f'<div class="dots">{dots}</div><div class="alt">{ALT_TXT}</div>{dm}')


def kart(u):
    rz = f'<div class="rz">%{e(u["indirim"])}</div>' if u.get("indirim") else ""
    return (f'<div class="k">{rz}{foto(u)}<div class="ad">{e(u["ad"])}</div>'
            f'<div class="fy"><div class="p">${e(u["fiyat"])}</div>'
            f'{"<div class=es>$" + e(u["eski_fiyat"]) + "</div>" if u.get("eski_fiyat") else ""}</div>'
            f'<div class="nt">{e(u.get("not", ""))}</div></div>')


def sayfalar():
    ps = 4
    parca = [urunler[i:i + ps] for i in range(0, len(urunler), ps)]
    top = len(parca) + 2
    en = max((int(u["indirim"]) for u in urunler if u.get("indirim")), default=0)
    foto3 = [u for u in sorted(urunler, key=lambda u: -int(u.get("indirim") or 0)) if u.get("gorsel")][:3]
    rot = [(-7, 70, 20), (0, 415, 0), (7, 760, 20)]
    tiles = "".join(f'<div class="t" style="left:{x}px;top:{y}px;transform:rotate({r}deg)">{foto(u)}</div>' for u, (r, x, y) in zip(foto3, rot))
    hero = f'<div class="hero bc"><span>%</span>{en}</div><div class="vr bc">EN YÜKSEK İNDİRİM</div>' if en else f'<div class="hero bc" style="font-size:150px">{e(d["baslik"])}</div>'
    out = [cerceve(1, top, f'<div class="bg"></div><div class="w"><span class="pill bc">{e(d["market"])}</span>{logo("lg")}'
                   f'<div class="et bc">{e(d["baslik"])}</div>{hero}<div class="tar bc">{e(d["gecerlilik"])}</div></div>'
                   f'<div class="col">{tiles}</div><div class="say"><b>{len(urunler)}</b>oyun seçtik</div><div class="kd bc">KAYDIR →</div>')]
    for n, p in enumerate(parca, 2):
        out.append(cerceve(n, top, f'<div class="bg"></div><div class="w"><span class="pill bc">{e(d["market"])}</span>{logo("lg")}'
                           f'<div class="sy bc">{n - 1}/{len(parca)}</div><div class="g">{"".join(kart(u) for u in p)}</div></div>'))
    out.append(cerceve(top, top, f'<div class="bg"></div><div class="cta">{logo("big")}'
                       '<h2 class="bc">Fırsatı <span>kaçırma</span></h2>'
                       '<p>Kaydet, arkadaşına gönder.<br>Her gün yeni oyun fırsatı için takip et.</p>'
                       '<div class="nk">Fiyatlar USD, platforma göre değişebilir. Kampanyalar önceden haber vermeden bitebilir.</div></div>'))
    return out


OUT = "out/" + os.path.splitext(os.path.basename(KAYNAK))[0]
os.makedirs(OUT, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1350})
    sf = sayfalar()
    for n, s in enumerate(sf, 1):
        open("out/_s.html", "w", encoding="utf-8").write(s)
        pg.goto("file:///" + os.path.abspath("out/_s.html").replace("\\", "/"))
        pg.evaluate("document.fonts.ready")
        pg.screenshot(path=f"{OUT}/{n}.jpg", type="jpeg", quality=92)
    kapak = base64.b64encode(open(f"{OUT}/1.jpg", "rb").read()).decode()
    open("out/_s.html", "w", encoding="utf-8").write(
        f'<html lang="tr"><meta charset="utf-8"><style>{TEMEL}body{{width:1080px;height:1920px}}'
        f'.u{{position:absolute;top:110px;left:0;right:0;text-align:center}}.u b{{font-size:110px;font-weight:800;color:{AC}}}'
        f'.u div{{font-size:46px;font-weight:700;margin-top:6px}}'
        f'.k{{position:absolute;left:60px;top:390px;width:960px;border-radius:36px;box-shadow:0 0 80px {AC}66}}'
        f'.a{{position:absolute;bottom:50px;left:0;right:0;text-align:center}}.a span{{background:{HI};color:{BG};font-size:52px;font-weight:800;padding:18px 46px;border-radius:70px}}</style>'
        f'<div class="u bc"><b>Fırsat alarmı</b><div>{e(d["market"])} · {e(d["kontrol_tarihi"])}</div></div>'
        f'<img class="k" src="data:image/jpeg;base64,{kapak}"><div class="a bc"><span>Tüm liste gönderide</span></div>')
    pg.set_viewport_size({"width": 1080, "height": 1920})
    pg.goto("file:///" + os.path.abspath("out/_s.html").replace("\\", "/"))
    pg.evaluate("document.fonts.ready")
    pg.screenshot(path=f"{OUT}/hikaye.jpg", type="jpeg", quality=90)
    b.close()
print(f"{len(sf)} görsel + hikaye üretildi; doğrulanmadığı için atılan: {atilan}")
