"""
YKS Sonuç Bildirim Botu — Depolama (Storage)
==============================================
Kullanıcı ID'lerini ve Telegram update ID'lerini dosyada saklar.
"""

import json
import logging

import config

logger = logging.getLogger(__name__)


def load_users() -> list[int]:
    """Kayıtlı kullanıcıların chat_id listesini döndürür."""
    if not config.USERS_STORAGE_FILE.exists():
        return []

    try:
        content = config.USERS_STORAGE_FILE.read_text(encoding="utf-8")
        if not content.strip():
            return []
        users = json.loads(content)
        return users if isinstance(users, list) else []
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Kullanıcılar yüklenirken hata oluştu: %s", e)
        return []


def save_users(users: list[int]) -> None:
    """Kullanıcıların chat_id listesini JSON olarak kaydeder."""
    unique_users = sorted(set(users))
    try:
        config.USERS_STORAGE_FILE.write_text(
            json.dumps(unique_users, indent=2), encoding="utf-8"
        )
    except OSError as e:
        logger.error("Kullanıcılar kaydedilirken hata oluştu: %s", e)


def add_user(chat_id: int) -> bool:
    """Yeni bir kullanıcı ekler. Eklenirse True, zaten varsa False döner."""
    users = load_users()
    if chat_id not in users:
        users.append(chat_id)
        save_users(users)
        return True
    return False


def get_user_count() -> int:
    """Toplam kayıtlı kullanıcı sayısını döndürür."""
    return len(load_users())


def load_last_update_id() -> int:
    """Son işlenen Telegram update_id değerini döndürür."""
    if not config.LAST_UPDATE_ID_FILE.exists():
        return 0
    try:
        return int(config.LAST_UPDATE_ID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return 0


def save_last_update_id(update_id: int) -> None:
    """Son işlenen Telegram update_id değerini kaydeder."""
    try:
        config.LAST_UPDATE_ID_FILE.write_text(str(update_id), encoding="utf-8")
    except OSError as e:
        logger.error("update_id kaydedilirken hata oluştu: %s", e)
