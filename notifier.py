"""
YKS Sonuç Bildirim Botu — Telegram Bildirim Gönderici
=======================================================
Telegram Bot API ile mesaj gönderir, kullanıcıları yönetir
ve GitHub Actions workflow'unu devre dışı bırakır.
"""

import logging
from datetime import datetime, timezone, timedelta

import requests

import config
import storage

logger = logging.getLogger(__name__)

# Türkiye saat dilimi (UTC+3)
TZ_TR = timezone(timedelta(hours=3))


def _promo_footer() -> str:
    """Mesajlara eklenecek tanıtım footer'ını oluşturur."""
    site = config.DEVELOPER_WEBSITE.replace("https://", "")
    return (
        "\n\n———\n"
        f"🌐 Geliştirici: [{site}]({config.DEVELOPER_WEBSITE})\n"
        f"⭐ [Projeye destek olmak için GitHub'da Star verin!]({config.GITHUB_REPO_URL})"
    )


class TelegramNotifier:
    """Telegram Bot API üzerinden bildirim gönderir."""

    def __init__(self) -> None:
        self.session = requests.Session()

    # ------------------------------------------------------------------
    # Temel mesaj gönderme
    # ------------------------------------------------------------------
    def send_message(self, text: str, chat_id: int | str | None = None) -> bool:
        """
        Telegram üzerinden mesaj gönderir.
        Başarılıysa True döner.
        """
        target_chat_id = chat_id if chat_id is not None else config.TELEGRAM_CHAT_ID
        payload = {
            "chat_id": target_chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        try:
            response = self.session.post(
                config.TELEGRAM_SEND_URL,
                json=payload,
                timeout=config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            result = response.json()
            if result.get("ok"):
                return True

            logger.error("❌ Telegram API hatası: %s", result)
            return False

        except requests.RequestException:
            logger.exception("❌ Telegram mesajı gönderilemedi (chat_id: %s)", target_chat_id)
            return False

    # ------------------------------------------------------------------
    # Admin'e özel bildirim
    # ------------------------------------------------------------------
    def _notify_admin(self, text: str) -> None:
        """Admin'e sessizce bildirim gönderir, hata olursa sadece loglar."""
        try:
            self.send_message(text, chat_id=config.TELEGRAM_CHAT_ID)
        except Exception as e:
            logger.error("Admin bildirimi gönderilemedi: %s", e)

    # ------------------------------------------------------------------
    # Sonuç bulundu — herkese gönder
    # ------------------------------------------------------------------
    def send_result_found_to_all(self, source: str, detail: str) -> bool:
        """Sonuç bulundu bildirimi kayıtlı tüm kullanıcılara gönderir."""
        now = datetime.now(TZ_TR).strftime("%d.%m.%Y - %H:%M")

        message = (
            "🎉 *YKS 2026 SONUÇLARI AÇIKLANDI!* 🎉\n"
            "\n"
            "📋 Sonuçlarınızı görüntülemek için:\n"
            "🔗 https://sonuc.osym.gov.tr\n"
            "\n"
            f"📅 *Tespit Zamanı:* {now}\n"
            f"🔍 *Kaynak:* {source}\n"
        )

        if detail:
            message += f"📝 *Detay:* {detail}\n"

        message += "\nBaşarılar! 🍀"
        message += _promo_footer()

        # Tüm kullanıcıları yükle
        users = storage.load_users()

        # Admin'i garanti olarak ekle
        try:
            admin_id = int(config.TELEGRAM_CHAT_ID)
            if admin_id not in users:
                users.append(admin_id)
        except ValueError:
            pass

        success_count = 0
        fail_count = 0

        for user_id in users:
            if self.send_message(message, chat_id=user_id):
                success_count += 1

                # Admin'e her başarılı gönderimi bildir (kendine hariç)
                if str(user_id) != str(config.TELEGRAM_CHAT_ID):
                    self._notify_admin(
                        f"✅ `{user_id}` ID'li kullanıcıya YKS sonuç bildirimi gönderildi."
                    )
            else:
                fail_count += 1
                logger.warning("⚠️  Mesaj gönderilemedi -> chat_id: %s", user_id)

        # Admin'e özet rapor gönder
        self._notify_admin(
            f"📊 *Sonuç Bildirimi Özeti*\n"
            f"✅ Başarılı: {success_count}\n"
            f"❌ Başarısız: {fail_count}\n"
            f"👥 Toplam Kullanıcı: {len(users)}"
        )

        return success_count > 0

    # ------------------------------------------------------------------
    # Yeni kullanıcıya hoş geldin mesajı
    # ------------------------------------------------------------------
    def send_startup_test(self, chat_id: int | str | None = None) -> bool:
        """Yeni kullanıcıya hoş geldin mesajı gönderir."""
        now = datetime.now(TZ_TR).strftime("%d.%m.%Y %H:%M")

        message = (
            "🤖 *YKS Sonuç Bildirim Botu Aktif!*\n"
            "\n"
            f"⏰ Kayıt Zamanı: {now}\n"
            "🔄 Kontrol aralığı: Her 5 dakikada bir\n"
            "🎯 Hedef: YKS 2026 sonuç duyurusu\n"
            "\n"
            "Bot çalışıyor, sonuçlar açıklandığında "
            "sana haber vereceğim! 📬"
        )
        message += _promo_footer()

        return self.send_message(message, chat_id=chat_id)

    # ------------------------------------------------------------------
    # Yeni kullanıcıları Telegram'dan çek ve kaydet
    # ------------------------------------------------------------------
    def process_new_users(self) -> None:
        """Telegram'dan yeni mesajları çeker, /start diyenleri kaydeder."""
        last_update_id = storage.load_last_update_id()
        params = {"offset": last_update_id + 1, "timeout": 5}

        try:
            response = self.session.get(
                config.TELEGRAM_GET_UPDATES_URL,
                params=params,
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                logger.error("getUpdates başarısız: %s", data)
                return

            updates = data.get("result", [])
            if not updates:
                return

            max_update_id = last_update_id
            new_user_count = 0

            for update in updates:
                update_id = update["update_id"]
                if update_id > max_update_id:
                    max_update_id = update_id

                msg = update.get("message")
                if not msg:
                    continue

                text = msg.get("text", "")
                chat = msg.get("chat", {})
                chat_id = chat.get("id")
                first_name = chat.get("first_name", "Bilinmiyor")

                if text.startswith("/start") and chat_id:
                    if storage.add_user(chat_id):
                        new_user_count += 1
                        logger.info("✅ Yeni kullanıcı: %s (id: %s)", first_name, chat_id)

                        # Kullanıcıya hoş geldin mesajı
                        self.send_startup_test(chat_id=chat_id)

                        # Admin'e bildirim
                        total = storage.get_user_count()
                        self._notify_admin(
                            f"👤 *Yeni Kullanıcı Katıldı!*\n"
                            f"📛 İsim: {first_name}\n"
                            f"🆔 Chat ID: `{chat_id}`\n"
                            f"📊 Toplam Kullanıcı: {total}"
                        )

            # Son işlenen update_id'yi kaydet
            if max_update_id > last_update_id:
                storage.save_last_update_id(max_update_id)

            if new_user_count > 0:
                logger.info(
                    "👥 %d yeni kullanıcı eklendi. Toplam: %d",
                    new_user_count,
                    storage.get_user_count(),
                )

        except requests.RequestException as e:
            logger.error("Telegram güncellemeleri alınırken ağ hatası: %s", e)
        except Exception as e:
            logger.error("Yeni kullanıcılar işlenirken beklenmeyen hata: %s", e)


def disable_workflow() -> bool:
    """
    GitHub Actions workflow'unu devre dışı bırakır.
    Sonuç bulunduktan sonra gereksiz çalışmaları engeller.
    """
    if not config.GITHUB_TOKEN or not config.GITHUB_REPOSITORY:
        logger.warning(
            "⚠️  GitHub token veya repository bilgisi bulunamadı. "
            "Workflow devre dışı bırakılamadı."
        )
        return False

    try:
        headers = {
            "Authorization": f"Bearer {config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Workflow'ları listele
        workflows_url = (
            f"{config.GITHUB_API_BASE}/repos/{config.GITHUB_REPOSITORY}"
            "/actions/workflows"
        )
        response = requests.get(
            workflows_url, headers=headers, timeout=config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        workflows = response.json().get("workflows", [])

        # yks-checker workflow'unu bul
        target_workflow = None
        for wf in workflows:
            if "yks" in wf.get("name", "").lower() or "yks" in wf.get("path", "").lower():
                target_workflow = wf
                break

        if not target_workflow:
            logger.warning("⚠️  YKS checker workflow bulunamadı.")
            return False

        # Workflow'u devre dışı bırak
        disable_url = (
            f"{config.GITHUB_API_BASE}/repos/{config.GITHUB_REPOSITORY}"
            f"/actions/workflows/{target_workflow['id']}/disable"
        )
        response = requests.put(
            disable_url, headers=headers, timeout=config.REQUEST_TIMEOUT
        )
        response.raise_for_status()

        logger.info("🔒 GitHub Actions workflow devre dışı bırakıldı!")
        return True

    except Exception:
        logger.exception("⚠️  Workflow devre dışı bırakılırken hata oluştu.")
        return False
