"""
YKS Sonuç Bildirim Botu — ÖSYM Kontrol Stratejileri
=====================================================
3 farklı kaynağı kontrol ederek YKS sonuçlarının açıklanıp açıklanmadığını tespit eder.
"""

import logging
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    """Tek bir kontrol stratejisinin sonucu."""
    found: bool
    source: str
    detail: str


class OsymChecker:
    """ÖSYM web sitelerini kontrol eden ana sınıf."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(config.REQUEST_HEADERS)

    # ------------------------------------------------------------------
    # Ana metod — tüm stratejileri sırayla dener
    # ------------------------------------------------------------------
    def run_all_checks(self) -> CheckResult:
        """
        3 stratejiyi sırayla çalıştırır.
        İlk başarılı sonuçta döner. Hiçbiri bulamazsa found=False döner.
        """
        strategies = [
            ("ÖSYM Ana Sayfa", self.check_osym_homepage),
            ("ÖSYM Sonuç Sayfası", self.check_sonuc_page),
            ("Google Haber", self.check_news_rss),
        ]

        for name, strategy_fn in strategies:
            try:
                logger.info("🔍 Strateji kontrol ediliyor: %s", name)
                result = strategy_fn()
                if result.found:
                    logger.info("✅ Sonuç bulundu! Kaynak: %s", name)
                    return result
                logger.info("   ↳ Sonuç bulunamadı.")
            except Exception:
                logger.exception("⚠️  Strateji başarısız oldu: %s", name)

        return CheckResult(
            found=False,
            source="",
            detail="Hiçbir strateji sonuç bulamadı.",
        )

    # ------------------------------------------------------------------
    # Strateji 1: ÖSYM Ana Sayfa Duyuru Taraması
    # ------------------------------------------------------------------
    def check_osym_homepage(self) -> CheckResult:
        """
        osym.gov.tr ana sayfasındaki duyurularda
        YKS sonuç açıklandı ifadelerini arar.

        ÖNEMLİ: Tüm sayfa metni yerine TEK TEK duyuru satırlarında arama
        yapar. Bu sayede "YKS" ve "Sonuç" kelimeleri sayfanın farklı
        yerlerinde geçse bile false positive oluşmaz.
        """
        response = self.session.get(
            config.OSYM_HOMEPAGE_URL,
            timeout=config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Her bir duyuru satırını ayrı ayrı kontrol et
        # (link metinleri + metin satırları)
        candidate_lines: list[str] = []

        # 1. Link metinleri
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            if text and len(text) > 5:
                candidate_lines.append(text)

        # 2. Sayfa metin satırları
        page_text = soup.get_text(separator="\n", strip=True)
        for line in page_text.split("\n"):
            stripped = line.strip()
            if stripped and len(stripped) > 5:
                candidate_lines.append(stripped)

        # Her satırda anahtar kelime gruplarını kontrol et
        for keyword_group in config.HOMEPAGE_KEYWORDS:
            upper_keywords = [kw.upper() for kw in keyword_group]
            for line in candidate_lines:
                upper_line = line.upper()
                if all(kw in upper_line for kw in upper_keywords):
                    return CheckResult(
                        found=True,
                        source="ÖSYM Ana Sayfa Duyurusu",
                        detail=f"Duyuru: {line}",
                    )

        return CheckResult(found=False, source="", detail="")

    # ------------------------------------------------------------------
    # Strateji 2: Sonuç Sayfası Kontrolü
    # ------------------------------------------------------------------
    def check_sonuc_page(self) -> CheckResult:
        """
        sonuc.osym.gov.tr sayfasında 2026-YKS sonuç belgesi ifadelerini arar.
        """
        response = self.session.get(
            config.OSYM_SONUC_URL,
            timeout=config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        page_text = soup.get_text(separator=" ", strip=True).upper()

        for keyword_group in config.SONUC_PAGE_KEYWORDS:
            upper_keywords = [kw.upper() for kw in keyword_group]
            if all(kw in page_text for kw in upper_keywords):
                return CheckResult(
                    found=True,
                    source="ÖSYM Sonuç Sayfası (sonuc.osym.gov.tr)",
                    detail=f"Anahtar kelimeler bulundu: {keyword_group}",
                )

        return CheckResult(found=False, source="", detail="")

    # ------------------------------------------------------------------
    # Strateji 3: Google Haber RSS Kontrolü (Yedek)
    # ------------------------------------------------------------------

    # Soru formundaki haberler false positive — sonuç henüz açıklanmamış demek
    _NEWS_EXCLUDE_PATTERNS: list[str] = [
        "AÇIKLANDI MI",
        "AÇIKLANACAK",
        "NE ZAMAN",
        "BEKLENİYOR",
        "TAHMİN",
    ]

    def check_news_rss(self) -> CheckResult:
        """
        Google News RSS üzerinden YKS 2026 sonuç haberlerini arar.
        Soru formundaki haberleri ("açıklandı mı?") filtreler.
        """
        response = self.session.get(
            config.GOOGLE_NEWS_RSS_URL,
            timeout=config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")

        if not items:
            return CheckResult(found=False, source="", detail="Haber bulunamadı.")

        # Son haberleri kontrol et
        upper_keywords = [kw.upper() for kw in config.NEWS_KEYWORDS]

        for item in items[:10]:  # Son 10 haber
            title = (item.find("title").get_text(strip=True)
                     if item.find("title") else "")
            description = (item.find("description").get_text(strip=True)
                           if item.find("description") else "")

            upper_title = title.upper()
            combined = upper_title + " " + description.upper()

            # Tüm anahtar kelimeler geçiyor mu?
            if not all(kw in combined for kw in upper_keywords):
                continue

            # Soru formundaki haberleri hariç tut
            if any(excl in upper_title for excl in self._NEWS_EXCLUDE_PATTERNS):
                logger.info("   ↳ Soru formu filtre: %s", title[:80])
                continue

            return CheckResult(
                found=True,
                source="Google Haber",
                detail=f"Haber başlığı: {title}",
            )

        return CheckResult(found=False, source="", detail="İlgili haber bulunamadı.")

