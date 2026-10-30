"""veri/<kaynak>_post.json -> out/<ad>/*.jpg + hikaye. Fiyat uydurulmaz, Steam/Epic'ten gelir.
Tek oyunsa (urunler[0] tek eleman): kapak oyunun görseliyle tam dolu, beyaz boşluk yok.
Birden fazla oyunsa (4'te 1 "toplu" gönderi): kapak + ızgara kartları, her kartın görseli de tam dolu (cover).
Kullanım: python render.py [veri/dosya.json]"""
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
e = html.escape
FD = "file:///" + os.path.abspath("fontlar").replace("\\", "/")


def b64(yol):
    return base64.b64encode(open(yol, "rb").read()).decode()


def logo(sinif):
    if not os.path.exists("logo.png"):
        return ""
    return f'<img class="{sinif}" src="data:image/png;base64,{b64("logo.png")}">'


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
.dots{{position:absolute;left:0;right:0;bottom:22px;text-align:center;z-index:5}}
.dots i{{display:inline-block;width:12px;height:12px;border-radius:50%;margin:0 5px;background:#ffffff55}}
.dots i.on{{width:34px;border-radius:8px;background:{HI}}}
.pill{{display:inline-block;background:{AC};font-weight:800;font-size:40px;letter-spacing:4px;padding:8px 30px;border-radius:60px;box-shadow:0 6px 20px #0008}}
"""


def goster(genislik, yukseklik, html_govde, ad):
    sf = "file:///" + os.path.abspath("out/_s.html").replace("\\", "/")
    open("out/_s.html", "w", encoding="utf-8").write(
        f'<html lang="tr"><meta charset="utf-8"><style>{TEMEL}body{{width:{genislik}px;height:{yukseklik}px}}</style>{html_govde}')
    pg.set_viewport_size({"width": genislik, "height": yukseklik})
    pg.goto(sf)
    pg.evaluate("document.fonts.ready")
    pg.screenshot(path=ad, type="jpeg", quality=92)


# ------------------------------------------------------------------ tek oyun
def tekli_govde(u, sayfa_no=None, toplam=None):
    rz = f'<div class="rz bc"><span>İNDİRİM</span><b>%{e(u["indirim"])}</b></div>' if u.get("indirim") else ""
    nt = f'<div class="not bc">{e(u["not"])}</div>' if u.get("not") else ""
    es = f'<div class="es">${e(u["eski_fiyat"])}</div>' if u.get("eski_fiyat") else ""
    dots = ("".join(f'<i class="{"on" if i == sayfa_no else ""}"></i>' for i in range(1, toplam + 1)) if toplam else "")
    css = """
.kapak{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.koyu{position:absolute;inset:0;background:linear-gradient(180deg,#00000066 0%,#00000022 32%,#00000099 68%,#000000ea 100%)}
.rz{position:absolute;right:50px;top:56px;background:""" + HI + """;color:""" + BG + """;font-family:'Barlow Condensed';font-weight:800;border-radius:50%;
 width:200px;height:200px;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 10px 30px #0008;transform:rotate(8deg)}
.rz b{font-size:84px;line-height:.9}.rz span{font-size:30px;letter-spacing:2px}
.not{position:absolute;left:56px;top:270px;background:#ffffffe6;color:""" + BG + """;font-weight:800;font-size:30px;padding:8px 26px;border-radius:14px}
.ad{position:absolute;left:56px;right:56px;bottom:290px;font-family:'Barlow Condensed';text-transform:uppercase;font-weight:800;font-size:84px;line-height:.98;text-shadow:0 6px 20px #000}
.fy{position:absolute;left:56px;bottom:150px;display:flex;align-items:flex-end;gap:26px}
.p{background:""" + AC + """;border-radius:22px;padding:4px 30px 10px;font-family:'Barlow Condensed';font-weight:800;font-size:110px;line-height:1.05;box-shadow:0 8px 24px #0006}
.es{font-size:40px;color:#ffffffaa;text-decoration:line-through;margin-bottom:18px}
.alt{position:absolute;left:0;right:0;bottom:0;padding:18px 56px 26px;font-size:21px;line-height:1.4;color:#ffffffaa}
.alt b{color:#fff}"""
    return (f'<style>{css}</style><img class="kapak" src="data:image/png;base64,{b64(u["gorsel"])}"><div class="koyu"></div>'
            f'<div class="w" style="position:relative;padding:50px 0 0"><span class="pill bc" style="margin-left:56px">{e(d["market"])}</span>{logo("lg")}</div>'
            f'{rz}{nt}<div class="ad">{e(u["ad"])}</div><div class="fy"><div class="p">${e(u["fiyat"])}</div>{es}</div>'
            f'<div class="alt"><b>Kaynak:</b> {e(d["kaynak_url"])} · <b>Kontrol:</b> {e(d["kontrol_tarihi"])}<br>'
            f'Fiyatlar değişebilir, kampanyalar önceden haber vermeden bitebilir.</div>{dots}')


# ------------------------------------------------------------------ toplu (4'te 1)
def kart(u):
    rz = f'<div class="krz bc">%{e(u["indirim"])}</div>' if u.get("indirim") else ""
    return (f'<div class="kart"><img class="kg" src="data:image/png;base64,{b64(u["gorsel"])}"><div class="kkoyu"></div>{rz}'
            f'<div class="kad">{e(u["ad"])}</div><div class="kp bc">${e(u["fiyat"])}</div></div>')


def toplu_kapak_govde(en_yuksek, sayfa_no, toplam):
    dots = "".join(f'<i class="{"on" if i == sayfa_no else ""}"></i>' for i in range(1, toplam + 1))
    css = """
.kapak{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:blur(3px) brightness(.55)}
.koyu{position:absolute;inset:0;background:linear-gradient(180deg,#00000088 0%,#00000055 40%,#000000cc 100%)}
.et{position:absolute;left:56px;top:170px;right:56px;font-size:58px;font-weight:800;color:""" + HI + """;letter-spacing:2px}
.hero{position:absolute;left:56px;right:56px;top:250px;font-family:'Barlow Condensed';font-weight:800;font-size:150px;line-height:.92;text-shadow:0 8px 30px #000}
.hero span{color:""" + AC + """}
.say{position:absolute;left:56px;bottom:260px;font-size:40px;font-weight:600}
.say b{font-size:110px;font-family:'Barlow Condensed';color:""" + AC + """;vertical-align:-12px;margin-right:10px}"""
    return (f'<style>{css}</style><img class="kapak" src="data:image/png;base64,{b64(en_yuksek["gorsel"])}"><div class="koyu"></div>'
            f'<div class="w" style="position:relative;padding:50px 0 0"><span class="pill bc" style="margin-left:56px">{e(d["market"])}</span>{logo("lg")}</div>'
            f'<div class="et bc">Günün fırsatları</div><div class="hero bc"><span>%{e(en_yuksek["indirim"])}</span>indirime varan</div>'
            f'<div class="say"><b>{len(urunler)}</b>oyun seçtik</div>'
            f'<div class="dots" style="bottom:200px">{dots}</div>')


def toplu_izgara_govde(ikili, sayfa_no, toplam):
    dots = "".join(f'<i class="{"on" if i == sayfa_no else ""}"></i>' for i in range(1, toplam + 1))
    css = """
.ig{position:relative;padding:70px 40px 0;display:grid;grid-template-columns:1fr 1fr;gap:24px;height:1230px}
.kart{position:relative;border-radius:30px;overflow:hidden;background:#1a1a24}
.kg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.kkoyu{position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,#000000e6 100%)}
.krz{position:absolute;right:16px;top:16px;background:""" + HI + """;color:""" + BG + """;font-family:'Barlow Condensed';font-weight:800;font-size:34px;padding:4px 16px;border-radius:12px;z-index:2}
.kad{position:absolute;left:20px;right:20px;bottom:66px;font-family:'Barlow Condensed';text-transform:uppercase;font-weight:800;font-size:34px;line-height:1.05;z-index:2;
 display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.kp{position:absolute;left:20px;bottom:18px;font-size:46px;font-weight:800;color:""" + AC + """;z-index:2}
.top{position:absolute;right:56px;top:40px;font-size:34px;color:#ffffff99;font-weight:700;z-index:3}"""
    kartlar = "".join(kart(u) for u in ikili)
    sayfano_yazi = f'<div class="top bc">{sayfa_no - 1}/{toplam - 1}</div>'
    return f'<style>{css}</style><div class="w" style="position:relative;padding:40px 0 0"><span class="pill bc" style="margin-left:56px">{e(d["market"])}</span></div>{sayfano_yazi}<div class="ig">{kartlar}</div><div class="dots">{dots}</div>'


OUT = "out/" + os.path.splitext(os.path.basename(KAYNAK))[0]
import shutil
shutil.rmtree(OUT, ignore_errors=True)  # önceki çalışmadan kalma fazla sayfa kalmasın (ör. toplu->tekli geçişi)
os.makedirs(OUT, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1350})
    if len(urunler) == 1:
        u = urunler[0]
        goster(1080, 1350, tekli_govde(u), f"{OUT}/1.jpg")
        goster(1080, 1920, tekli_govde(u), f"{OUT}/hikaye.jpg")
        uretilen = 1
    else:
        en_yuksek = max(urunler, key=lambda u: int(u.get("indirim") or 0))
        ikililer = [urunler[i:i + 2] for i in range(0, len(urunler), 2)]
        toplam = 1 + len(ikililer)
        goster(1080, 1350, toplu_kapak_govde(en_yuksek, 1, toplam), f"{OUT}/1.jpg")
        for i, ik in enumerate(ikililer, 2):
            goster(1080, 1350, toplu_izgara_govde(ik, i, toplam), f"{OUT}/{i}.jpg")
        goster(1080, 1920, tekli_govde(en_yuksek), f"{OUT}/hikaye.jpg")
        uretilen = toplam
    b.close()
print(f"{uretilen} görsel + hikaye üretildi ({'tek' if len(urunler) == 1 else 'toplu'} mod); doğrulanmadığı için atılan: {atilan}")
