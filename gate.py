"""Sabit saat yok: her tetiklemede (15-30 dk) taze+sağlam içerik varsa paylaşır.
Tek koruma günlük tavan: bugün (TR günü) zaten GUNLUK_LIMIT kadar paylaşım yapıldıysa durur, spam'e dönüşmesin diye."""
import json, os
from datetime import datetime, timedelta, timezone

GUNLUK_LIMIT = 25  # kullanıcı: 20-30 arası, 50-60 olmasın
TR = timezone(timedelta(hours=3))


def bugunku_sayi(gecmis, bugun):
    return sum(1 for g in gecmis if datetime.strptime(g["tarih"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).astimezone(TR).date() == bugun)


if __name__ == "__main__":
    bugun = datetime.now(TR).date()
    gecmis = json.load(open("gecmis.json", encoding="utf-8")) if os.path.exists("gecmis.json") else []
    sayi = bugunku_sayi(gecmis, bugun)
    devam = sayi < GUNLUK_LIMIT
    print(f"Şimdi (TR): {datetime.now(TR).strftime('%H:%M')} | bugün paylaşılan: {sayi}/{GUNLUK_LIMIT} | karar:", "paylaş" if devam else "günlük tavan doldu, bekle")
    if os.environ.get("GITHUB_OUTPUT"):
        open(os.environ["GITHUB_OUTPUT"], "a").write(f"devam={'true' if devam else 'false'}\n")
