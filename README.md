# YKS Sonuç Bildirim Botu 🎓📬

<div align="center">

**ÖSYM web sitesini otomatik olarak kontrol eden ve YKS sonuçları açıklandığı anda
kayıt olan herkese Telegram üzerinden anlık bildirim gönderen açık kaynaklı bot.**

[![GitHub Stars](https://img.shields.io/github/stars/Metee01/YKS-Result-Notification-Bot?style=social)](https://github.com/Metee01/YKS-Result-Notification-Bot)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![GitHub Actions](https://img.shields.io/badge/Powered%20by-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/Lisans-MIT-green.svg)](LICENSE)

[**🤖 Botu Başlat →**](https://t.me/yks_sonuc_bildirim_bot)

</div>

---

## 🚀 Proje Hakkında

YKS sonuçlarının açıklanma anını sürekli F5 yaparak beklemek yerine, Telegram üzerinden `/start` diyerek bota kayıt olun — sonuçlar açıklandığında anında haberiniz olsun.

### Nasıl Çalışır?

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Actions (her 5 dk)                              │
│  ├── 1. Yeni /start kullanıcılarını kaydet              │
│  ├── 2. ÖSYM'yi 3 farklı stratejiyle kontrol et         │
│  └── 3. Sonuç varsa → herkese Telegram bildirimi gönder │
└─────────────────────────────────────────────────────────┘
```

| Adım | Açıklama |
|------|----------|
| 👥 **Kullanıcı Kaydı** | Bota `/start` yazan herkes otomatik olarak sisteme dahil edilir |
| 🏠 **ÖSYM Ana Sayfa** | `osym.gov.tr` duyurularında sonuç ibaresi taranır |
| 📊 **Sonuç Sayfası** | `sonuc.osym.gov.tr` sayfasında 2026-YKS sonuç belgesi aranır |
| 📰 **Google Haberler** | Haber RSS'inde "YKS sonuçları açıklandı" ifadesi aranır |
| 📬 **Toplu Bildirim** | Sonuç tespit edildiğinde kayıtlı tüm kullanıcılara mesaj gönderilir |
| 🔒 **Otomatik Kapanma** | Bildirim gönderildikten sonra bot kendini otomatik devre dışı bırakır |

---

## 📁 Proje Yapısı

```
├── .github/workflows/
│   └── yks-checker.yml    # GitHub Actions cron workflow
├── main.py                # Ana giriş noktası
├── checker.py             # ÖSYM kontrol stratejileri (3 farklı kaynak)
├── notifier.py            # Telegram bildirim sistemi (toplu mesaj + admin bildirimi)
├── storage.py             # Kullanıcı veritabanı (users.json) yönetimi
├── config.py              # Konfigürasyon ve ortam değişkenleri
├── requirements.txt       # Python bağımlılıkları
└── README.md
```

---

## ❓ Sıkça Sorulan Sorular

<details>
<summary><strong>Bot ne kadar sıklıkla kontrol ediyor?</strong></summary>

Her **5 dakikada** bir. GitHub Actions cron yoğun saatlerde 5-15 dk gecikme yapabilir.
</details>

<details>
<summary><strong>Bota <code>/start</code> dedim, hemen mesaj gelmedi?</strong></summary>

Bot GitHub Actions üzerinde 5 dakikada bir çalıştığı için "Bot Aktif" mesajı en fazla 5 dakika içinde ulaşır. Bu durum ücretsiz altyapının doğal bir getirisidir.
</details>

<details>
<summary><strong>Kişisel verilerimi kullanıyor mu?</strong></summary>

**Hayır.** Bot sadece ÖSYM'nin kamuya açık sayfalarını kontrol eder. T.C. kimlik numarası veya şifre gibi bilgilere kesinlikle erişmez. Yalnızca size mesaj atabilmek için Telegram Chat ID'nizi tutar.
</details>

<details>
<summary><strong>Sonuç açıklandıktan sonra tekrar tekrar mesaj gelir mi?</strong></summary>

Hayır. Bot sonucu tespit edip bildirimi gönderdikten sonra kendini otomatik olarak devre dışı bırakır. Sadece tek bir sefer bildirim yollar.
</details>

---

## 🤝 Destek Olun

Bu proje tamamen açık kaynaklı ve ücretsizdir.

Eğer faydalı buluyorsanız, **⭐ Star** vererek projeye destek olabilirsiniz!

---

<div align="center">

🌐 **Geliştirici:** [metee.com.tr](https://metee.com.tr)

*Öğrencilere kolaylık sağlamak amacıyla geliştirilmiş açık kaynak bir projedir.*

</div>
