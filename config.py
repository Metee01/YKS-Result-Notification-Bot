"""
YKS Sonuç Bildirim Botu — Konfigürasyon
========================================
Ortam değişkenleri, URL tanımları, anahtar kelimeler ve cache yönetimi.
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Lokal geliştirme için .env desteği (opsiyonel)
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # GitHub Actions ortamında dotenv gerekmez

# ---------------------------------------------------------------------------
# Telegram Ayarları
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "")

TELEGRAM_API_BASE: str = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
TELEGRAM_SEND_URL: str = f"{TELEGRAM_API_BASE}/sendMessage"
TELEGRAM_GET_UPDATES_URL: str = f"{TELEGRAM_API_BASE}/getUpdates"

# ---------------------------------------------------------------------------
# Tanıtım / Proje Linkleri
# ---------------------------------------------------------------------------
GITHUB_REPO_URL: str = "https://github.com/Metee01/YKS-Result-Notification-Bot"
DEVELOPER_WEBSITE: str = "https://metee.com.tr"

# ---------------------------------------------------------------------------
# GitHub Actions Ayarları (workflow devre dışı bırakma için)
# ---------------------------------------------------------------------------
GITHUB_TOKEN: str = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY: str = os.environ.get("GITHUB_REPOSITORY", "")  # "user/repo"
GITHUB_API_BASE: str = "https://api.github.com"

# ---------------------------------------------------------------------------
# ÖSYM URL'leri
# ---------------------------------------------------------------------------
OSYM_HOMEPAGE_URL: str = "https://www.osym.gov.tr"
OSYM_SONUC_URL: str = "https://sonuc.osym.gov.tr"
GOOGLE_NEWS_RSS_URL: str = (
    "https://news.google.com/rss/search"
    "?q=YKS+2026+sonu%C3%A7+a%C3%A7%C4%B1kland%C4%B1&hl=tr&gl=TR&ceid=TR:tr"
)

# ---------------------------------------------------------------------------
# HTTP Ayarları
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT: int = 15  # saniye
USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
REQUEST_HEADERS: dict = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ---------------------------------------------------------------------------
# Anahtar Kelimeler (Sonuç tespiti için)
# ---------------------------------------------------------------------------
# Ana sayfa duyurularında aranacak — HEPSİ aynı SATIRDA/DUYURUDA geçmeli
# "Açıklandı" kelimesi her grupta ZORUNLU (false positive önleme)
HOMEPAGE_KEYWORDS: list[list[str]] = [
    ["2026-YKS", "Sonuçları Açıklandı"],
    ["2026-YKS", "Sonuç", "Açıklandı"],
    ["YKS", "Sonuçları Açıklandı"],
    ["2026", "YKS", "Açıklandı"],
]

# Sonuç sayfasında aranacak — sadece 2026-YKS yetmez,
# sonuç sayfasında "Sonuç Belgesi" veya benzeri ifade de geçmeli
SONUC_PAGE_KEYWORDS: list[list[str]] = [
    ["2026-YKS", "Sonuç Belgesi"],
    ["2026-YKS", "Sınav Sonucu"],
    ["2026-YKS", "Sonuçları"],
]

# Haber aramasında aranacak
NEWS_KEYWORDS: list[str] = ["YKS", "2026", "sonuç", "açıklandı"]

# ---------------------------------------------------------------------------
# Cache / Durum Yönetimi / Kullanıcı Depolama
# ---------------------------------------------------------------------------
RESULT_FOUND_FLAG: Path = Path(".result_found")
USERS_STORAGE_FILE: Path = Path("users.json")
LAST_UPDATE_ID_FILE: Path = Path("last_update_id.txt")


def is_already_found() -> bool:
    """Sonuç daha önce bulunmuş mu kontrol et."""
    return RESULT_FOUND_FLAG.exists()


def mark_as_found() -> None:
    """Sonuç bulunduğunu cache dosyasına yaz."""
    RESULT_FOUND_FLAG.write_text("found", encoding="utf-8")


# ---------------------------------------------------------------------------
# Doğrulama
# ---------------------------------------------------------------------------
def validate_config() -> bool:
    """Zorunlu konfigürasyon değerlerini kontrol et."""
    errors: list[str] = []

    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN ayarlanmamış!")
    if not TELEGRAM_CHAT_ID:
        errors.append("TELEGRAM_CHAT_ID ayarlanmamış!")

    if errors:
        for err in errors:
            print(f"❌ HATA: {err}", file=sys.stderr)
        print(
            "\n💡 İpucu: GitHub Actions'da Settings → Secrets → Actions bölümünden "
            "bu değerleri ekleyin.",
            file=sys.stderr,
        )
        return False

    return True
