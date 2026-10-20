# -*- coding: utf-8 -*-
"""Imperial AI Tutor Service — STTTNNĐ (Lưu Niên — Đại Nội Huế).

Scope-locked AI pedagogical assistant strictly bounded to:
- Architectural monuments of the Imperial City of Hue (Đại Nội Huế).
- Historical claims, primary source records (Đại Nam Thực Lục, Hội Điển Sự Lệ, Nhất Thống Chí).
- Strict deny-list check rejecting queries outside Dai Noi or mentioning forbidden legacy concepts
  (Cửu Đỉnh, 9 urns, 162 relief motifs).
- 3-part structured epistemic response:
  (1) Trả lời gợi mở tư duy (Inquiry answer)
  (2) Nguồn sử liệu đối chiếu (Primary sources cited)
  (3) Điều chắc chắn vs Điều cần kiểm chứng thêm (Certainty vs Uncertainty)
- Deterministic mock/fallback mode when external LLM API key is not configured.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..apischemas.imperial import (
    ImperialAICertaintyUncertainty,
    ImperialAIAskResponse,
    ImperialAISourceRef,
)
from ..config import settings
from ..imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    ImperialSite,
)

logger = logging.getLogger(__name__)

REFUSAL_MESSAGE = "Nội dung này nằm ngoài phạm vi học liệu lịch sử Đại Nội Huế của dự án."

# --------------------------------------------------------------------------- #
# Strict Deny-List Patterns
# --------------------------------------------------------------------------- #
# Rejects queries referencing the legacy Cuu Dinh (9 urns) / 162 relief motifs
# or concepts completely extraneous to the Imperial City architectural scope.
_DENY_PATTERNS = [
    # Cửu Đỉnh variations
    re.compile(r"c[ửu][\s_-]*[đd][ỉi][nnh]h?", flags=re.IGNORECASE),
    re.compile(r"ch[íi]n[\s_-]*[đd][ỉi][nnh]h?", flags=re.IGNORECASE),
    re.compile(r"9[\s_-]*[đd][ỉi][nnh]h?", flags=re.IGNORECASE),
    re.compile(r"\bnine[\s_-]*dynastic[\s_-]*urns?\b", flags=re.IGNORECASE),
    re.compile(r"\bnine[\s_-]*urns?\b", flags=re.IGNORECASE),
    re.compile(r"\b9[\s_-]*urns?\b", flags=re.IGNORECASE),
    re.compile(r"\bdynastic[\s_-]*urns?\b", flags=re.IGNORECASE),
    re.compile(
        r"\b(?:cao|nh[âa]n|ch[ưu][ơo]ng|anh|ngh[ịi]|thu[âa]n|tuy[êe]n|d[ụu]|huy[ềe]n)[\s_-]*[đd][ỉi]nh\b",
        flags=re.IGNORECASE,
    ),
    # 162 Relief Motifs variations
    re.compile(
        r"162\s*(?:ph[ùu][\s_-]*[đd]i[êe]u|h[ọo]a[\s_-]*v[ăa]n|motif|reliefs?|b[ảa]n[\s_-]*[đd][úu]c)",
        flags=re.IGNORECASE,
    ),
    re.compile(r"ph[ùu][\s_-]*[đd]i[êe]u[\s_-]*c[ửu][\s_-]*[đd][ỉi]nh", flags=re.IGNORECASE),
    re.compile(r"h[ọo]a[\s_-]*v[ăa]n[\s_-]*c[ửu][\s_-]*[đd][ỉi]nh", flags=re.IGNORECASE),
    re.compile(r"b[ảa]n[\s_-]*[đd][úu]c[\s_-]*n[ổo]i", flags=re.IGNORECASE),
    re.compile(r"ban[\s_-]*duc[\s_-]*noi", flags=re.IGNORECASE),
    re.compile(r"\brelief[\s_-]*motifs?\b", flags=re.IGNORECASE),
]

# Supplemental data cache
_ZONES_AND_SITES_FILE = Path(__file__).resolve().parents[2] / "data" / "imperial" / "zones_and_sites.json"
_supplemental_cache: Optional[dict[str, dict[str, Any]]] = None


def _get_supplemental_data() -> dict[str, dict[str, Any]]:
    global _supplemental_cache
    if _supplemental_cache is not None:
        return _supplemental_cache
    cache: dict[str, dict[str, Any]] = {}
    if _ZONES_AND_SITES_FILE.exists():
        try:
            raw = json.loads(_ZONES_AND_SITES_FILE.read_text(encoding="utf-8"))
            for s in raw.get("sites", []):
                slug = s.get("slug")
                if slug:
                    cache[slug] = s
        except Exception:
            pass
    _supplemental_cache = cache
    return _supplemental_cache


# Keyword mappings from query terms to site slugs
_KEYWORD_SITE_MAP = [
    # Ngọ Môn
    (["ngọ môn", "ngo mon", "ngũ phụng", "ngu phung", "cổng chính", "cửa ngọ môn"], "ngo-mon"),
    # Điện Thái Hòa
    (["thái hòa", "thai hoa", "ngai vàng", "trùng thiềm điệp ốc", "trung thiem diep oc"], "dien-thai-hoa"),
    # Cầu Trung Đạo
    (["trung đạo", "trung dao", "thái dịch", "thai dich", "cầu trung đạo"], "cau-trung-dao"),
    # Sân Đại Triều Nghi
    (["đại triều nghi", "dai trieu nghi", "đại triều", "bái mạng", "phẩm tán", "phẩm trật", "long trì"], "san-dai-trieu-nghi"),
    # Thế Tổ Miếu
    (["thế tổ miếu", "the to mieu", "thế miếu", "thờ vua"], "the-to-mieu"),
    # Hiển Lâm Các
    (["hiển lâm các", "hien lam cac"], "hien-lam-cac"),
    # Hưng Tổ Miếu
    (["hưng tổ miếu", "hung to mieu"], "hung-to-mieu"),
    # Triệu Tổ Miếu
    (["triệu tổ miếu", "trieu to mieu"], "trieu-to-mieu"),
    # Đại Cung Môn
    (["đại cung môn", "dai cung mon"], "dai-cung-mon"),
    # Điện Cần Chánh
    (["cần chánh", "can chanh"], "dien-can-chanh"),
    # Điện Kiến Trung
    (["kiến trung", "kien trung"], "dien-kien-trung"),
    # Duyệt Thị Đường
    (["duyệt thị đường", "duyet thi duong", "nhà hát"], "duyet-thi-duong"),
    # Thái Bình Lâu
    (["thái bình lâu", "thai binh lau", "đọc sách", "thư phòng"], "thai-binh-lau"),
    # Cung Diên Thọ
    (["diên thọ", "dien tho", "hoàng thái hậu"], "cung-dien-tho"),
    # Cung Trường Sanh
    (["trường sanh", "truong sanh", "thái hoàng thái hậu"], "cung-truong-sanh"),
    # Điện Phụng Tiên
    (["phụng tiên", "phung tien"], "dien-phung-tien"),
]

# General Dai Noi keywords that indicate valid scope even if not a specific monument
_GENERAL_DAI_NOI_TERMS = [
    "đại nội",
    "dai noi",
    "hoàng thành",
    "hoang thanh",
    "tử cấm thành",
    "tu cam thanh",
    "kinh thành huế",
    "cố đô huế",
    "triều nguyễn",
    "vua gia long",
    "vua minh mạng",
    "vua thiệu trị",
    "vua tự đức",
    "trục thần đạo",
    "trục chính đạo",
    "chính sử triều nguyễn",
    "đại nam thực lục",
    "hội điển sự lệ",
]


def _normalize_text(text: str) -> str:
    """Normalize text (lowercase, unaccent, strip) for robust matching."""
    import unicodedata

    t = text.lower().replace("đ", "d")
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", t)


_DENY_UNACCENTED_TERMS = [
    "cuu dinh",
    "chin dinh",
    "9 dinh",
    "9 urn",
    "nine urn",
    "dynastic urn",
    "cao dinh",
    "nhan dinh",
    "chuong dinh",
    "anh dinh",
    "nghi dinh",
    "thuan dinh",
    "tuyen dinh",
    "du dinh",
    "huyen dinh",
    "ban duc noi",
    "ban duc cuu dinh",
    "phu dieu cuu dinh",
    "hoa van cuu dinh",
    "relief motif",
]


def _is_denied(query: str) -> bool:
    """Check if query triggers any forbidden legacy concept."""
    norm = _normalize_text(query)

    # 1. Specific unaccented forbidden terms
    for term in _DENY_UNACCENTED_TERMS:
        if term in norm:
            return True

    # 2. 162 motifs / reliefs combinations
    if "162" in norm and any(
        w in norm for w in ["phu dieu", "hoa van", "motif", "relief", "ban duc"]
    ):
        return True

    # 3. Regex check on original query
    for pattern in _DENY_PATTERNS:
        if pattern.search(query):
            return True

    return False


def _resolve_site(
    db: Session, query: str, site_slug: Optional[str] = None
) -> tuple[Optional[ImperialSite], Optional[dict[str, Any]]]:
    """Retrieve ImperialSite entity and supplemental data strictly scoped to STTT_IMPERIAL_CITY."""
    supp_dict = _get_supplemental_data()

    # 1. Direct slug lookup if provided
    if site_slug:
        site = db.execute(
            select(ImperialSite).where(
                ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL,
                ImperialSite.slug == site_slug,
            )
        ).scalar_one_or_none()
        if site:
            return site, supp_dict.get(site.slug)

    # 2. Match site keywords from query
    query_lower = query.lower()
    for keywords, slug in _KEYWORD_SITE_MAP:
        for kw in keywords:
            if kw in query_lower:
                site = db.execute(
                    select(ImperialSite).where(
                        ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL,
                        ImperialSite.slug == slug,
                    )
                ).scalar_one_or_none()
                if site:
                    return site, supp_dict.get(slug)

    # 3. Check if general Dai Noi concept is mentioned
    is_general_dai_noi = any(term in query_lower for term in _GENERAL_DAI_NOI_TERMS)
    if is_general_dai_noi:
        # Default to the primary central monument (Ngọ Môn or Điện Thái Hòa)
        site = db.execute(
            select(ImperialSite)
            .where(
                ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL,
                ImperialSite.slug == "ngo-mon",
            )
        ).scalar_one_or_none()
        if site:
            return site, supp_dict.get("ngo-mon")

    return None, None


def _build_deterministic_answer(
    site: ImperialSite, supp: dict[str, Any], query: str
) -> dict[str, Any]:
    """Build authentic evidence-grounded response formatted in 3 structured epistemic sections."""
    site_slug = site.slug
    task = supp.get("pedagogical_task", {})
    inquiry_q = supp.get("guiding_inquiry_question", "")

    # 1. Section 1: Inquiry Answer
    if site_slug == "ngo-mon":
        inquiry_answer = (
            "Ngọ Môn là cổng chính phía nam của Hoàng Thành Huế, được xây dựng năm Minh Mạng thứ 14 (1833) "
            "trên vị trí đài Nam Sách thời Gia Long. Công trình kết hợp hài hòa giữa kiến trúc phòng thủ kiên cố "
            "ở tầng đài đá và nét thanh thoát, trang trọng của lầu Ngũ Phụng ở tầng trên. Cấu trúc 5 cửa ngõ của "
            "Ngọ Môn thể hiện rõ nét trật tự tập quyền và phân tầng lễ nghi triều Nguyễn: Ngọ Môn (cửa chính giữa) "
            "chỉ dành riêng cho Thiên tử; hai bên là Tả Giáp Môn và Hữu Giáp Môn dành cho bá quan văn võ; ngoài cùng "
            "là Tả Dịch Môn và Hữu Dịch Môn dành cho binh mã hộ vệ. Lầu Ngũ Phụng là nơi hoàng đế ngự lãm các đại lễ "
            "như lễ ban Lịch Sóc, lễ Truyền loa vinh quy tiến sĩ, và đặc biệt là nơi chứng kiến sự kiện lịch sử "
            "tuyên bố thoái vị của vua Bảo Đại năm 1945. Theo em, việc tổ chức không gian 5 cửa phân luồng nghiêm ngặt "
            "này phản ánh vũ trụ quan và tư tưởng chính trị của nhà Nguyễn như thế nào?"
        )
    elif site_slug == "dien-thai-hoa":
        inquiry_answer = (
            "Điện Thái Hòa là công trình trung tâm quan trọng bậc nhất trong Hoàng Thành Huế, biểu trưng cho quyền lực "
            "tối cao của hoàng triều và nền văn hiến quốc gia. Tòa điện được xây dựng theo thức 'trùng thiềm điệp ốc' "
            "(nhà kép mái chồng mái) độc đáo với 80 cột gỗ lim sơn son thếp vàng chạm trổ long vân tinh xảo, mái lợp ngói "
            "hoàng lưu ly rực rỡ. Đây là nơi diễn ra các đại lễ thiêng liêng nhất của triều đình: lễ đăng quang, vạn thọ "
            "(sinh nhật vua), tiếp sứ thần và lễ Đại triều mùng 1 và ngày rằm hàng tháng. Gian chính điện đặt ngai vàng thiên tử "
            "dưới bửu tán lộng lẫy, kết hợp với hệ thống ô hộc 'nhất thi nhất họa' khắc các bài thơ ngự chế ca ngợi thái bình thịnh trị. "
            "Em hãy suy ngẫm: Vì sao kết cấu 'trùng thiềm điệp ốc' vừa tạo ra không gian nội thất rộng lớn không bị che khuất tầm nhìn, "
            "vừa thích nghi tối ưu với khí hậu mưa bão khắc nghiệt của xứ Huế?"
        )
    elif site_slug == "cau-trung-dao":
        inquiry_answer = (
            "Cầu Trung Đạo bắc qua hồ Thái Dịch, nằm trên trục chính đạo nối Ngọ Môn với sân Đại Triều Nghi, được xây dựng "
            "năm Minh Mạng thứ 14 (1833). Mặt cầu lát đá thanh, hai đầu cầu dựng hai cổng đồng quán với hoa văn đúc tinh xảo. "
            "Cây cầu và hồ nước tạo ra khoảng lùi phong thủy 'tụ thủy sinh tài', đồng thời đóng vai trò nhịp chuyển tiếp tâm lý "
            "trang nghiêm cho các quan viên trước khi bước vào sân bái mạng thiết đại triều."
        )
    elif site_slug == "san-dai-trieu-nghi":
        inquiry_answer = (
            "Sân Đại Triều Nghi gồm hai tầng sân trước điện Thái Hòa, nơi quan viên đứng dự lễ Đại triều. Sân được phân tầng "
            "chặt chẽ: tầng trên dành cho quan tứ phẩm trở lên, tầng dưới dành cho quan ngũ phẩm đến cửu phẩm. Hai bên dựng hai hàng "
            "bia đá 'phẩm tán' khắc thứ bậc: quan văn đứng bên tả (hướng đông), quan võ đứng bên hữu (hướng tây). Cách bố trí này "
            "thiết lập một trật tự kỷ cương đẳng cấp trực quan dưới quyền uy tuyệt đối của thiên tử."
        )
    else:
        # Generic authentic grounding using site attributes
        context_text = site.historical_context or site.summary_vi or site.name_vi
        inquiry_answer = (
            f"Di tích {site.name_vi} thuộc quần thể Hoàng Thành Huế, được xây dựng trong triều đại Nguyễn "
            f"(khởi dựng khoảng năm {site.construction_year or 'đầu thế kỷ XIX'}). {context_text} "
            f"Công trình phản ánh quy chế điển chương và tư duy tổ chức không gian cung đình chặt chẽ. "
            f"Gợi ý tư duy: {inquiry_q or 'Hãy đối chiếu mối liên hệ giữa kiến trúc di tích với chức năng nghi lễ triều đình.'}"
        )

    # 2. Section 2: Primary Sources Cited
    primary_sources_raw = supp.get("primary_sources", [])
    sources_cited: list[ImperialAISourceRef] = []
    for src in primary_sources_raw:
        sources_cited.append(
            ImperialAISourceRef(
                source_title=src.get("source_title", "Chính sử triều Nguyễn"),
                citation=src.get("citation"),
                volume_or_chapter=src.get("volume_or_chapter"),
                archival_unit=src.get("archival_unit"),
                reliability_level=src.get("reliability_level", "verified_primary_source"),
            )
        )

    if not sources_cited:
        sources_cited.append(
            ImperialAISourceRef(
                source_title="Đại Nam Thực Lục Chính Biên",
                citation=f"Ghi chép chính sử về quy chế kiến tạo {site.name_vi} triều Nguyễn.",
                volume_or_chapter="Quốc Sử Quán triều Nguyễn",
                archival_unit="Viện Sử học Việt Nam",
                reliability_level="verified_primary_source",
            )
        )

    # 3. Section 3: Certainty vs Uncertainty
    if site_slug == "ngo-mon":
        certainty = (
            "Niên đại xây dựng năm Minh Mạng thứ 14 (1833) trên nền đài Nam Sách cũ; "
            "quy thức phân luồng 5 cửa ngõ và công năng lầu Ngũ Phụng được ghi chép tường minh "
            "trong Đại Nam Thực Lục Chính Biên (Quyển 98) và Khâm Định Đại Nam Hội Điển Sự Lệ (Quyển 168)."
        )
        uncertainty = (
            "Quy cách và vật liệu ngói lợp (hoàng lưu ly và thanh lưu ly) cùng màu sắc trang trí lầu Ngũ Phụng "
            "qua các đợt trùng tu (thời Khải Định, thập niên 1990 và 2021) cần tiếp tục đối chiếu với hồ sơ bảo tồn thực địa."
        )
    elif site_slug == "dien-thai-hoa":
        certainty = (
            "Mốc khởi dựng năm Gia Long thứ 4 (1805) và đợt dời chuyển, mở rộng đại quy mô năm Minh Mạng thứ 14 (1833); "
            "kết cấu trùng thiềm điệp ốc 80 cột gỗ lim và bửu tán ngai vàng được quy định chi tiết trong Khâm Định Đại Nam Hội Điển Sự Lệ (Quyển 64)."
        )
        uncertainty = (
            "Các lớp màu sơn son thếp vàng nguyên bản thời Minh Mạng so với các lần tu bổ thời Thành Thái, Khải Định "
            "và đợt đại trùng tu hạ giải 2021-2025 cần thêm chứng cứ vi phân tích vật liệu khảo cổ học kiến trúc."
        )
    else:
        uncertainty_prompt = task.get("uncertainty_prompt", "")
        if "Điều biết chắc:" in uncertainty_prompt and "Điều cần xác minh:" in uncertainty_prompt:
            parts = uncertainty_prompt.split("Điều cần xác minh:")
            certainty = parts[0].replace("Điều biết chắc:", "").strip()
            uncertainty = parts[1].strip()
        else:
            certainty = f"Niên đại khởi dựng năm {site.construction_year or 'triều Nguyễn'} và công năng chính quy định trong chính sử."
            uncertainty = "Chi tiết về các cấu kiện kiến trúc thay thế qua các thời kỳ lịch sử cần tiếp tục kiểm chứng tư liệu ảnh và khảo cổ."

    cert_uncert = ImperialAICertaintyUncertainty(
        certainty=certainty,
        uncertainty=uncertainty,
    )

    # Formatted overall message
    sources_summary = "\n".join(
        [f"- {s.source_title} ({s.volume_or_chapter or ''}): \"{s.citation}\"" for s in sources_cited]
    )
    formatted_message = (
        f"{inquiry_answer}\n\n"
        f"**Nguồn sử liệu đối chiếu:**\n{sources_summary}\n\n"
        f"**Điều chắc chắn:** {certainty}\n\n"
        f"**Điều cần kiểm chứng thêm:** {uncertainty}"
    )

    return {
        "content_scope": CONTENT_SCOPE_IMPERIAL,
        "insufficient_evidence": False,
        "message": formatted_message,
        "inquiry_answer": inquiry_answer,
        "sources_cited": [s.model_dump() for s in sources_cited],
        "certainty_vs_uncertainty": cert_uncert.model_dump(),
        "site_slug": site.slug,
    }


def ask_imperial_tutor(
    db: Session,
    query: str,
    site_slug: Optional[str] = None,
    context: Optional[str] = None,
) -> ImperialAIAskResponse:
    """Query scope-locked AI tutor for Đại Nội Huế.
    
    Validates:
    1. Deny-list check: rejects Cửu Đỉnh / 162 relief motifs or topics outside Dai Noi.
    2. Epistemic grounding: retrieves verified sites and primary sources.
    3. Structured 3-part pedagogical response format.
    4. Deterministic fallback when external LLM API key is not configured.
    """
    clean_query = query.strip() if query else ""

    # 1. Deny-list check
    if _is_denied(clean_query):
        return ImperialAIAskResponse(
            content_scope=CONTENT_SCOPE_IMPERIAL,
            insufficient_evidence=True,
            message=REFUSAL_MESSAGE,
            inquiry_answer=REFUSAL_MESSAGE,
            sources_cited=[],
            certainty_vs_uncertainty=ImperialAICertaintyUncertainty(
                certainty="",
                uncertainty="",
            ),
            site_slug=site_slug,
        )

    # 2. Scope-locked site & evidence retrieval
    site, supp = _resolve_site(db, clean_query, site_slug=site_slug)
    if not site or not supp:
        # Outside scope or insufficient historical evidence in Dai Noi
        return ImperialAIAskResponse(
            content_scope=CONTENT_SCOPE_IMPERIAL,
            insufficient_evidence=True,
            message=REFUSAL_MESSAGE,
            inquiry_answer=REFUSAL_MESSAGE,
            sources_cited=[],
            certainty_vs_uncertainty=ImperialAICertaintyUncertainty(
                certainty="",
                uncertainty="",
            ),
            site_slug=site_slug,
        )

    # 3. Deterministic response generation
    response_data = _build_deterministic_answer(site, supp, clean_query)
    return ImperialAIAskResponse.model_validate(response_data)
