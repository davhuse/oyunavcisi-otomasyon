"""Zamanlayıcı geç/eksik çalışsa da günde 4 paylaşımı garanti eder (Fit Algoritma'daki gate.py ile aynı mantık).
Her 15-30 dakikada çalışır; son geçen paylaşım saatinin penceresinde henüz paylaşım yoksa 'devam=true' der."""
import json, os
from datetime import datetime, timedelta, timezone

SAATLER = [(9, 0), (13, 0), (18, 0), (21, 30)]  # Türkiye saati
TR = timezone(timedelta(hours=3))


def karar(simdi, paylasimlar):
    gecen = [s for s in (simdi.replace(hour=h, minute=m, second=0, microsecond=0) for h, m in SAATLER) if s <= simdi]
    if not gecen:
        return False, "-"  # gece yarısı - 09:00 arası paylaşım yok
    return not any(p >= gecen[-1] for p in paylasimlar), gecen[-1].strftime("%H:%M")


if __name__ == "__main__":
    t = lambda h, m=0: datetime(2026, 10, 29, h, m, tzinfo=TR)
    assert karar(t(8), []) == (False, "-")
    assert karar(t(9, 5), []) == (True, "09:00")
    assert karar(t(12), [t(9, 30)]) == (False, "09:00")
    assert karar(t(13, 20), [t(9, 30)]) == (True, "13:00")
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        devam, pencere = True, "elle"
    else:
        # geçmişteki saatler UTC yazılıyor
        gecmis = json.load(open("gecmis.json", encoding="utf-8")) if os.path.exists("gecmis.json") else []
        devam, pencere = karar(datetime.now(TR), [datetime.strptime(g["tarih"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc) for g in gecmis])
    print("Şimdi (TR):", datetime.now(TR).strftime("%H:%M"), "| pencere:", pencere, "| karar:", "paylaş" if devam else "bekle")
    if os.environ.get("GITHUB_OUTPUT"):
        open(os.environ["GITHUB_OUTPUT"], "a").write(f"devam={'true' if devam else 'false'}\n")
