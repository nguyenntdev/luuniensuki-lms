# -*- coding: utf-8 -*-
"""Bilingual Vietnamese/English Pedagogical Glossary & Epigraphy Domain (V5-T098).

Implements core domain rules, provenance tracking, and negative abuse defenses
for multilingual learning supports across Cửu Đỉnh and the Imperial City:
1. Pedagogical Glossary:
   - Vietnamese term (`term_vi`), English translation (`term_en`).
   - Hán–Nôm epigraphy readings (`term_han_nom`, `reading_quoc_ngu`).
   - Bilingual definitions and contextual usage examples (`definition_vi`, `definition_en`).
   - Category classification (relic, epigraphy, architecture, ritual, symbolism, etc.).
2. Translation Provenance & Bilingual Citation:
   - Origin tracking (human_epigrapher, scholarly_lexicon, machine_translated, ai_generated, etc.).
   - Bibliographic linkage to HistoricalSource records and precise citation locators.
   - Expert epigrapher / translator sign-off tracking.
3. Negative Abuse Guardrails:
   - Mismatched, placeholder, or untranslated Vietnamese copied into English is flagged
     with explicit uncertainty and blocked from verified status.
   - Machine-translated or AI-generated glosses MUST carry prominent uncertainty labels
     and CANNOT be promoted to verified without human epigrapher sign-off and scholarly citation.
   - Unreviewed or provisional glosses cannot be presented as verified historical facts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GlossaryCategory(str, Enum):
    """Pedagogical domain category for historical terms."""
    relic = "relic"
    epigraphy = "epigraphy"
    architecture = "architecture"
    ritual = "ritual"
    symbolism = "symbolism"
    geography = "geography"
    flora_fauna = "flora_fauna"
    technique = "technique"
    governance = "governance"
    general = "general"


class GlossaryReviewStatus(str, Enum):
    """Review and epistemic verification status of the glossary entry."""
    unreviewed = "unreviewed"
    provisional = "provisional"
    uncertain = "uncertain"
    verified = "verified"
    disputed = "disputed"
    rejected = "rejected"


class TranslationOrigin(str, Enum):
    """Provenance origin of the term's translation or gloss."""
    human_epigrapher = "human_epigrapher"
    scholarly_lexicon = "scholarly_lexicon"
    machine_translated = "machine_translated"
    ai_generated = "ai_generated"
    provisional_draft = "provisional_draft"
    unspecified_seed = "unspecified_seed"


VERIFIED_GLOSSARY_STATUSES: frozenset[str] = frozenset({
    GlossaryReviewStatus.verified.value,
    "verified",
    "expert_reviewed",
    "human_verified",
})

UNREVIEWED_GLOSSARY_STATUSES: frozenset[str] = frozenset({
    GlossaryReviewStatus.unreviewed.value,
    GlossaryReviewStatus.provisional.value,
    GlossaryReviewStatus.uncertain.value,
    "unreviewed",
    "provisional",
    "uncertain",
})

# Disqualified placeholder, test, or fabricated tokens
DISQUALIFIED_TRANSLATION_MARKERS: frozenset[str] = frozenset({
    "unknown",
    "none",
    "n/a",
    "na",
    "null",
    "undefined",
    "todo",
    "tbd",
    "placeholder",
    "fake",
    "dummy",
    "test",
    "untranslated",
    "translation pending",
    "chua ro",
    "chua co",
    "chưa rõ",
    "chưa dịch",
    "dang cap nhat",
    "đang cập nhật",
})


class GlossaryValidationError(ValueError):
    """Base error for glossary domain validation failures."""
    pass


class MismatchedTranslationError(GlossaryValidationError):
    """Raised when translations are mismatched, placeholder, or untranslated copies."""
    pass


class UnreviewedTranslationPromotionError(GlossaryValidationError):
    """Raised when an unreviewed or machine-translated gloss attempts promotion to verified."""
    pass


def is_placeholder_text(text: Optional[str]) -> bool:
    """Check if a string contains placeholder, dummy, or fabricated tokens."""
    if not text or not str(text).strip():
        return True
    s = str(text).strip().lower()
    if s in DISQUALIFIED_TRANSLATION_MARKERS:
        return True
    words = set(re.findall(r"\w+", s))
    if words and words.issubset(DISQUALIFIED_TRANSLATION_MARKERS):
        return True
    if any(marker in s for marker in ("translation pending", "chưa dịch", "dummy translation", "placeholder")):
        return True
    return False


def detect_translation_mismatch(
    term_vi: str,
    term_en: str,
    definition_vi: Optional[str] = None,
    definition_en: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """Detect whether a translation has mismatches, untranslated duplication, or placeholders.
    
    Returns:
        (is_mismatched, reason)
    """
    if not term_vi or not term_vi.strip():
        return True, "Vietnamese term cannot be empty."
    if not term_en or not term_en.strip():
        return True, "English term cannot be empty."

    # Check for placeholder markers
    if is_placeholder_text(term_en):
        return True, f"English term contains placeholder or dummy text: '{term_en}'."
    if definition_en and is_placeholder_text(definition_en):
        return True, "English definition contains placeholder or dummy text."

    # Check for untranslated definition copy-paste (identical Vietnamese copied into English)
    if definition_vi and definition_en:
        norm_vi = re.sub(r"\s+", " ", definition_vi.strip().lower())
        norm_en = re.sub(r"\s+", " ", definition_en.strip().lower())
        if len(norm_vi) > 20 and norm_vi == norm_en:
            return True, "English definition is an exact duplicate of Vietnamese definition (untranslated copy)."

    return False, None


def build_translation_provenance(
    origin: str | TranslationOrigin,
    translator_or_reviewer: Optional[str] = None,
    citation_locator: Optional[str] = None,
    is_machine_translated: bool = False,
    is_uncertain: bool = False,
    uncertainty_label: Optional[str] = None,
    source_title: Optional[str] = None,
    confidence: Optional[float] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    """Construct an immutable structured provenance dictionary for glossary translations."""
    origin_val = origin.value if isinstance(origin, Enum) else str(origin)
    return {
        "origin": origin_val,
        "translator_or_reviewer": translator_or_reviewer.strip() if translator_or_reviewer else None,
        "reviewed_at": datetime.now(timezone.utc).isoformat() if translator_or_reviewer else None,
        "citation_locator": citation_locator.strip() if citation_locator else None,
        "source_title": source_title.strip() if source_title else None,
        "is_machine_translated": bool(is_machine_translated),
        "is_uncertain": bool(is_uncertain),
        "uncertainty_label": uncertainty_label.strip() if uncertainty_label else None,
        "confidence": confidence if confidence is not None else (0.95 if translator_or_reviewer else 0.50),
        "notes": notes.strip() if notes else None,
    }


def validate_glossary_term_invariants(
    term_key: str,
    term_vi: str,
    term_en: str,
    definition_vi: str,
    definition_en: str,
    review_status: str | GlossaryReviewStatus,
    origin: str | TranslationOrigin,
    term_han_nom: Optional[str] = None,
    reading_quoc_ngu: Optional[str] = None,
    epigrapher_signoff: Optional[str] = None,
    source_id: Optional[UUID | str] = None,
    citation_locator: Optional[str] = None,
    is_machine_translated: bool = False,
    is_uncertain: bool = False,
    uncertainty_label: Optional[str] = None,
) -> dict[str, Any]:
    """Validate all domain invariants and negative abuse defenses for a glossary term.
    
    Returns:
        dict with normalized flags: {'is_uncertain': bool, 'uncertainty_label': str, 'review_status': str}
    """
    status_str = review_status.value if isinstance(review_status, Enum) else str(review_status)
    origin_str = origin.value if isinstance(origin, Enum) else str(origin)
    is_verified = status_str in VERIFIED_GLOSSARY_STATUSES

    # 1. Basic field validity
    if not term_key or not term_key.strip():
        raise GlossaryValidationError("term_key must be non-empty.")
    if not term_vi or not term_vi.strip():
        raise GlossaryValidationError("term_vi must be non-empty.")
    if not term_en or not term_en.strip():
        raise GlossaryValidationError("term_en must be non-empty.")
    if not definition_vi or not definition_vi.strip():
        raise GlossaryValidationError("definition_vi must be non-empty.")
    if not definition_en or not definition_en.strip():
        raise GlossaryValidationError("definition_en must be non-empty.")

    # 2. Translation mismatch & placeholder detection
    is_mismatched, mismatch_reason = detect_translation_mismatch(
        term_vi=term_vi,
        term_en=term_en,
        definition_vi=definition_vi,
        definition_en=definition_en,
    )

    if is_verified and is_mismatched:
        raise MismatchedTranslationError(
            f"Negative Abuse: Mismatched or placeholder translation cannot be verified: {mismatch_reason}"
        )

    # 3. Machine-translated and AI-generated verification guardrail
    is_machine = is_machine_translated or origin_str == TranslationOrigin.machine_translated.value
    if is_verified:
        if is_machine and (not epigrapher_signoff or not epigrapher_signoff.strip()):
            raise UnreviewedTranslationPromotionError(
                "Negative Abuse: Machine-translated glosses cannot be marked verified "
                "without human reviewer sign-off."
            )
        if not epigrapher_signoff or not epigrapher_signoff.strip():
            raise UnreviewedTranslationPromotionError(
                "Negative Abuse: Unreviewed translation cannot be promoted to verified "
                "without human epigrapher sign-off."
            )
        has_citation = bool(source_id or (citation_locator and len(citation_locator.strip()) >= 4))
        if not has_citation:
            raise UnreviewedTranslationPromotionError(
                "Negative Abuse: Verified glossary term must include an authoritative source citation."
            )
        if is_uncertain:
            raise GlossaryValidationError(
                "Term cannot be simultaneously marked as verified and uncertain."
            )
        # Hán-Nôm epigraphy reading check
        if term_han_nom and term_han_nom.strip() and (not reading_quoc_ngu or not reading_quoc_ngu.strip()):
            raise GlossaryValidationError(
                "Verified Hán–Nôm term must include Sino-Vietnamese reading (reading_quoc_ngu)."
            )

    # 4. Uncertainty enforcement for non-verified or mismatched states
    effective_uncertain = bool(is_uncertain)
    effective_label = uncertainty_label

    if is_mismatched:
        effective_uncertain = True
        if not effective_label:
            effective_label = f"Bản dịch đối chiếu chưa hoàn thiện: {mismatch_reason}"

    if is_machine and not is_verified:
        effective_uncertain = True
        if not effective_label:
            effective_label = "Bản dịch máy tự động — chưa qua thẩm định chuyên gia Hán–Nôm."

    if status_str in UNREVIEWED_GLOSSARY_STATUSES:
        effective_uncertain = True
        if not effective_label:
            effective_label = "Thuật ngữ đang trong quá trình khảo cứu và biên soạn đối chiếu."

    return {
        "is_uncertain": effective_uncertain,
        "uncertainty_label": effective_label,
        "review_status": status_str,
        "is_machine_translated": is_machine,
    }


# --------------------------------------------------------------------------- #
# Canonical Cửu Đỉnh Pedagogical Glossary Seed Data
# --------------------------------------------------------------------------- #
CANONICAL_PEDAGOGICAL_GLOSSARY: list[dict[str, Any]] = [
    {
        "term_key": "cao-dinh",
        "term_vi": "Cao Đỉnh",
        "term_en": "Cao Urn (The Supreme Urn)",
        "term_han_nom": "高鼎",
        "reading_quoc_ngu": "Cao Đỉnh",
        "category": GlossaryCategory.relic.value,
        "definition_vi": "Chiếc đỉnh lớn nhất đặt ở vị trí trung tâm trong Cửu Đỉnh, biểu trưng cho sự nghiệp vĩ đại của Thế Tổ Cao Hoàng Đế (Gia Long).",
        "definition_en": "The central and foremost urn among the Nine Dynastic Urns, symbolizing the supreme achievement of Emperor Gia Long.",
        "contextual_usage_vi": "Cao Đỉnh được đúc vào năm Minh Mạng thứ 16 (1835) và đặt ở gian chính giữa sân Thế Miếu.",
        "contextual_usage_en": "Cao Dinh was cast in the 16th year of Minh Mang reign (1835) and placed at the central position of the The Mieu courtyard.",
        "review_status": GlossaryReviewStatus.verified.value,
        "origin": TranslationOrigin.human_epigrapher.value,
        "epigrapher_signoff": "Prof. Nguyen Dinh Chien / National Museum of History",
        "citation_locator": "Đại Nam Thực Lục, Đệ nhị kỷ, Quyển 162",
        "bilingual_citation": {
            "title_vi": "Đại Nam Thực Lục Chính Biên",
            "title_en": "Veritable Records of Dai Nam",
            "locator": "Đệ nhị kỷ, Quyển 162, tờ 12a-14b",
        },
        "is_machine_translated": False,
        "is_uncertain": False,
        "related_entity_slugs": ["cao-dinh"],
    },
    {
        "term_key": "huyen-dinh",
        "term_vi": "Huyền Đỉnh",
        "term_en": "Huyen Urn (The Profound Urn)",
        "term_han_nom": "玄鼎",
        "reading_quoc_ngu": "Huyền Đỉnh",
        "category": GlossaryCategory.relic.value,
        "definition_vi": "Chiếc đỉnh thứ chín đặt ở mút phía bắc của Cửu Đỉnh; chữ 'Huyền' biểu trưng cho sự sâu xa, huyền diệu và tĩnh lặng.",
        "definition_en": "The ninth urn situated at the northern end of the Nine Dynastic Urns; 'Huyen' denotes profundity, transcendence, and serenity.",
        "contextual_usage_vi": "Huyền Đỉnh tương ứng với quẻ Càn trong Kinh Dịch theo phối trí phương vị phương Bắc.",
        "contextual_usage_en": "Huyen Dinh corresponds to the northern directional placement in the cosmological layout.",
        "review_status": GlossaryReviewStatus.verified.value,
        "origin": TranslationOrigin.human_epigrapher.value,
        "epigrapher_signoff": "Institute of Han-Nom Studies Review Board",
        "citation_locator": "Khâm Định Đại Nam Hội Điển Sự Lệ, Quyển 214",
        "bilingual_citation": {
            "title_vi": "Khâm Định Đại Nam Hội Điển Sự Lệ",
            "title_en": "Administrative Compendium of Dai Nam",
            "locator": "Quyển 214, Bộ Công — Đúc Cửu Đỉnh",
        },
        "is_machine_translated": False,
        "is_uncertain": False,
        "related_entity_slugs": ["huyen-dinh"],
    },
    {
        "term_key": "bach-dang-giang",
        "term_vi": "Bạch Đằng Giang",
        "term_en": "Bach Dang River",
        "term_han_nom": "白藤江",
        "reading_quoc_ngu": "Bạch Đằng Giang",
        "category": GlossaryCategory.geography.value,
        "definition_vi": "Con sông lịch sử gắn liền với ba chiến thắng oanh liệt chống giặc ngoại xâm phương Bắc của dân tộc Việt Nam, được khắc họa trên Nghị Đỉnh.",
        "definition_en": "The historic river celebrated for three glorious naval victories against northern invasions in Vietnamese history, depicted on the Nghi Urn.",
        "contextual_usage_vi": "Hình tượng Bạch Đằng Giang trên Cửu Đỉnh ghi nhận chủ quyền lãnh thổ và võ công hiển hách của dân tộc.",
        "contextual_usage_en": "The depiction of Bach Dang River on the Nine Urns commemorates national sovereignty and martial triumphs.",
        "review_status": GlossaryReviewStatus.verified.value,
        "origin": TranslationOrigin.scholarly_lexicon.value,
        "epigrapher_signoff": "Epigraphic Commission for Hue Monuments",
        "citation_locator": "Đại Nam Nhất Thống Chí, Tỉnh Quảng Yên",
        "bilingual_citation": {
            "title_vi": "Đại Nam Nhất Thống Chí",
            "title_en": "Comprehensive Gazetteer of Dai Nam",
            "locator": "Tỉnh Quảng Yên, Mục Sông núi",
        },
        "is_machine_translated": False,
        "is_uncertain": False,
        "related_entity_slugs": ["nghi-dinh-11"],
    },
    {
        "term_key": "phap-lam",
        "term_vi": "Pháp lam",
        "term_en": "Hue Enamelware (Cloisonné/Champlevé enamels)",
        "term_han_nom": "琺瑯",
        "reading_quoc_ngu": "Pháp lam",
        "category": GlossaryCategory.technique.value,
        "definition_vi": "Nghệ thuật tráng men màu trên cốt kim loại (đồng hoặc đồng thau) đặc trưng của mỹ thuật cung đình triều Nguyễn.",
        "definition_en": "The art of vitreous polychrome enamel applied to copper substrate, a signature royal decorative art of the Nguyen Dynasty court.",
        "contextual_usage_vi": "Xưởng Pháp lam tượng cục được vua Minh Mạng thành lập năm 1827 để chế tác đồ ngự dụng và trang trí cung điện.",
        "contextual_usage_en": "The royal enamel atelier was founded by Emperor Minh Mang in 1827 to produce imperial ware and palace ornamentation.",
        "review_status": GlossaryReviewStatus.verified.value,
        "origin": TranslationOrigin.scholarly_lexicon.value,
        "epigrapher_signoff": "Hue Imperial Craft Preservation Group",
        "citation_locator": "Mỹ thuật Huế, Viện Mỹ thuật, 1998, tr. 142",
        "bilingual_citation": {
            "title_vi": "Nghiên cứu Pháp lam Huế",
            "title_en": "Studies on Hue Imperial Enamelware",
            "locator": "Trang 142-148",
        },
        "is_machine_translated": False,
        "is_uncertain": False,
        "related_entity_slugs": [],
    },
    {
        "term_key": "dan-moc",
        "term_vi": "Đàn Mộc",
        "term_en": "Sandalwood Tree",
        "term_han_nom": "檀木",
        "reading_quoc_ngu": "Đàn Mộc",
        "category": GlossaryCategory.flora_fauna.value,
        "definition_vi": "Loài cây gỗ đàn hương quý hiếm đúc trên Nghị Đỉnh; chữ Hán trên đỉnh còn mờ và đang được khảo cứu văn bia đối chiếu thác bản.",
        "definition_en": "Sandalwood depicted on the Nghi Urn; the bronze-cast glyph remains eroded and is under ongoing epigraphic investigation.",
        "contextual_usage_vi": "Chữ Đàn Mộc trên Nghị Đỉnh là một trong các đồ án cần khảo cứu thêm về mặt minh văn.",
        "contextual_usage_en": "The Dan Moc inscription on the Nghi Urn is subject to ongoing epigraphic comparison against rubbings.",
        "review_status": GlossaryReviewStatus.uncertain.value,
        "origin": TranslationOrigin.provisional_draft.value,
        "is_machine_translated": False,
        "is_uncertain": True,
        "uncertainty_label": "Chữ Hán trên đỉnh đồng mờ nhạt — tư liệu đang khảo cứu đối chiếu thác bản.",
        "related_entity_slugs": ["nghi-dinh-03"],
    },
    {
        "term_key": "dang-son-ngu",
        "term_vi": "Đăng Sơn Ngư",
        "term_en": "Climbing perch fish",
        "term_han_nom": None,
        "reading_quoc_ngu": "Đăng Sơn Ngư",
        "category": GlossaryCategory.flora_fauna.value,
        "definition_vi": "Cá rô leo cây được đúc trên Thuần Đỉnh; chưa tìm thấy minh văn Hán tự nguyên bản trên đỉnh.",
        "definition_en": "Climbing perch fish depicted on Thuan Urn; original Han script glyph not yet confirmed.",
        "contextual_usage_vi": "Đăng Sơn Ngư là một trong 4 đồ án khuyết chữ Hán trong đợt kiểm kê Cửu Đỉnh.",
        "contextual_usage_en": "Dang Son Ngu is one of the 4 motifs lacking verified Han-Nom glyphs.",
        "review_status": GlossaryReviewStatus.unreviewed.value,
        "origin": TranslationOrigin.machine_translated.value,
        "is_machine_translated": True,
        "is_uncertain": True,
        "uncertainty_label": "Bản dịch máy tự động — chưa qua thẩm định chuyên gia Hán–Nôm.",
        "related_entity_slugs": ["thuan-dinh-13"],
    },
]
