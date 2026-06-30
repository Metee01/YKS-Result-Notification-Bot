"""
YKS Sonuç Bildirim Botu — Ana Giriş Noktası
=============================================
GitHub Actions tarafından her 5 dakikada bir tetiklenir.
Tek seferlik çalışıp çıkar.
"""

import logging
import sys

import config
import storage
from checker import OsymChecker
from notifier import TelegramNotifier, disable_workflow

# ---------------------------------------------------------------------------
# Loglama ayarları
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Ana çalışma döngüsü (tek seferlik)."""

    logger.info("=" * 60)
    logger.info("🚀 YKS Sonuç Bildirim Botu başlatıldı")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # 1. Konfigürasyon doğrulama
    # ------------------------------------------------------------------
    if not config.validate_config():
        logger.error("❌ Konfigürasyon eksik! Çıkılıyor.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2. Telegram'dan yeni kullanıcıları çek
    # ------------------------------------------------------------------
    notifier = TelegramNotifier()
    logger.info("👥 Yeni kullanıcılar kontrol ediliyor...")
    notifier.process_new_users()
    logger.info("👥 Kayıtlı kullanıcı sayısı: %d", storage.get_user_count())

    # ------------------------------------------------------------------
    # 3. Cache kontrol — daha önce bulunmuş mu?
    # ------------------------------------------------------------------
    if config.is_already_found():
        logger.info(
            "✅ Sonuç daha önce bulunmuş (cache dosyası mevcut). "
            "Tekrar kontrol edilmeyecek."
        )
        return

    # ------------------------------------------------------------------
    # 4. ÖSYM kontrol et
    # ------------------------------------------------------------------
    logger.info("🔎 ÖSYM kontrolleri başlatılıyor...")
    checker = OsymChecker()
    result = checker.run_all_checks()

    # ------------------------------------------------------------------
    # 5. Sonuç değerlendirme
    # ------------------------------------------------------------------
    if result.found:
        logger.info("🎉 SONUÇ BULUNDU!")
        logger.info("   Kaynak : %s", result.source)
        logger.info("   Detay  : %s", result.detail)

        # Telegram bildirimi gönder (Herkese)
        success = notifier.send_result_found_to_all(result.source, result.detail)

        if success:
            logger.info("📨 Telegram bildirimleri gönderildi!")

            # Cache dosyasına yaz
            config.mark_as_found()
            logger.info("💾 Durum cache'e kaydedildi.")

            # Workflow'u devre dışı bırak
            if disable_workflow():
                logger.info("🔒 GitHub Actions workflow devre dışı bırakıldı.")
            else:
                logger.warning(
                    "⚠️  Workflow devre dışı bırakılamadı. "
                    "Manuel olarak kapatmanız gerekebilir."
                )
        else:
            logger.error(
                "❌ Telegram bildirimi gönderilemedi! "
                "Sonraki çalışmada tekrar denenecek."
            )
            # Cache'e YAZMA — sonraki çalışmada tekrar denesin

    else:
        logger.info(
            "⏳ Sonuç henüz açıklanmadı. Sonraki kontrolde tekrar denenecek."
        )

    logger.info("=" * 60)
    logger.info("🏁 Çalışma tamamlandı.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
