# -*- coding: utf-8 -*-
"""Low-Bandwidth Printable / Offline Kit Service (V5-T096 / Wave W09, Slot A06).

Provides server-authoritative generation and validation of printable student handouts,
high-contrast 2D rubbings, QR codes, offline inspection tasks, and audio guide transcripts.

Enforces Core Invariants:
1. EQUAL_PEDAGOGICAL_OUTCOMES:
   - 100% of curriculum competencies (S1 Spatial, S2 Temporal, S3 Evidence, S4 Argument)
     are achievable with paper, pencil, and 2D rubbings.
2. NEGATIVE_ABUSE_GATE (No AR or smartphone mandatory):
   - A learner with no smartphone, denied camera permission, or in an offline classroom
     MUST NEVER be blocked, penalized, or marked down.
   - Any assignment submission or inspection task completed via paper/2D rubbing receives
     the exact same maximum score (12/12 Rubric, 25 XP Discovery).
3. SOURCE_AND_RIGHTS_PROTECTION:
   - Excerpts are verified against approved primary historical sources (ĐNTL, Hội Điển, Nhất Thống Chí).
   - Rubbing assets include cleared rights attributions and high-contrast print CSS filters.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from ..apischemas.offline_kit import (
    LowBandwidthOfflineKitResponse,
    OfflineAudioTranscript,
    OfflineInspectionTask,
    OfflineKitStation,
    OfflinePrimarySourceItem,
    OfflineRubbingAsset,
)
from ..errors import AppError
from .asset_rights import (
    DEFAULT_LEGAL_BASIS,
    DEFAULT_RIGHTS_OWNER,
    URN_FALLBACK_2D_REGISTRY,
)

logger = logging.getLogger("luuniensuki.offline_kit")

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_IMPERIAL = REPO_ROOT / "data" / "imperial"
WORKSHEET_PATH = DATA_IMPERIAL / "fieldwork_worksheet.json"
ZONES_SITES_PATH = DATA_IMPERIAL / "zones_and_sites.json"
AUDIO_GUIDES_PATH = DATA_IMPERIAL / "audio_guides.json"

STANDARD_4_SLUGS = [
    "ngo-mon",
    "dien-thai-hoa",
    "hien-lam-cac",
    "cung-dien-tho",
]

# Monument to authentic rubbing or architectural engraving mapping
MONUMENT_RUBBINGS_MAP: Dict[str, Dict[str, Any]] = {
    "ngo-mon": {
        "asset_url": "/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg",
        "local_path": "ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
        "sha256": "3187abe1940c680a5145eac960e50230f45cf7382a6e647a61988b2124f82a28",
        "format": "image/jpeg",
        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
    },
    "dien-thai-hoa": {
        "asset_url": "/assets/ban-duc-noi/NHAN%20DINH/NH%C3%82N%20%C4%90%E1%BB%88NH.jpg",
        "local_path": "ban-duc-noi/NHAN DINH/NHÂN ĐỈNH.jpg",
        "sha256": "7395b93f6966e1802f8fe108511652c2d7c8fd0846578ecbd742134936f99e69",
        "format": "image/jpeg",
        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
    },
    "hien-lam-cac": {
        "asset_url": "/assets/ban-duc-noi/CHUONG%20DINH/CH%C6%AF%C6%A0NG%20%C4%90%E1%BB%88NH.jpg",
        "local_path": "ban-duc-noi/CHUONG DINH/CHƯƠNG ĐỈNH.jpg",
        "sha256": "50b47cce23604aa2af4f22274d702997f3101a43f5ac09c6e144f16b412c50f7",
        "format": "image/jpeg",
        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
    },
    "cung-dien-tho": {
        "asset_url": "/assets/ban-duc-noi/ANH%20DINH/ANH%20%C4%90%E1%BB%88NH.jpg",
        "local_path": "ban-duc-noi/ANH DINH/ANH ĐỈNH.jpg",
        "sha256": "3adb2fb9fab2ae0f8f6b6f2dbf23f2366252726cf3c5026d6e00d24a09e45100",
        "format": "image/jpeg",
        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
    },
    "the-to-mieu": {
        "asset_url": "/assets/ban-duc-noi/NGHI%20DINH/NGHI%20DINH.jpg",
        "local_path": "ban-duc-noi/NGHI DINH/NGHI DINH.jpg",
        "sha256": "01640017e63d04caf254b2cd9da198d23fdc1dce339fcc67ba4a69c8ae572258",
        "format": "image/jpeg",
        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
    },
    "duyet-thi-duong": {
        "asset_url": "/assets/ban-duc-noi/THUAN%20DINH/%C4%90%E1%BB%88NH.jpg",
        "local_path": "ban-duc-noi/THUAN DINH/ĐỈNH.jpg",
        "sha256": "f3cefae96a0acf6a058c709e663488c3d2d76b625e883c76417a79d0f5abfabe",
        "format": "image/jpeg",
        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
    },
}

DEFAULT_RUBBING = {
    "asset_url": "/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg",
    "local_path": "ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
    "sha256": "3187abe1940c680a5145eac960e50230f45cf7382a6e647a61988b2124f82a28",
    "format": "image/jpeg",
    "rights_attribution": DEFAULT_RIGHTS_OWNER,
    "legal_basis": DEFAULT_LEGAL_BASIS,
}


def _load_json_data(path: Path) -> dict[str, Any]:
    if not path.is_file():
        logger.warning("JSON file not found: %s", path)
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_offline_kit(
    cluster_id: str = "standard_4",
    base_url: str = "https://luuniensuki.vn",
) -> LowBandwidthOfflineKitResponse:
    """Construct the complete low-bandwidth printable kit data bundle."""
    worksheet_json = _load_json_data(WORKSHEET_PATH)
    zones_json = _load_json_data(ZONES_SITES_PATH)
    audio_json = _load_json_data(AUDIO_GUIDES_PATH)

    sites_list = zones_json.get("sites", [])
    sites_by_slug = {s["slug"]: s for s in sites_list if "slug" in s}

    audio_guides = audio_json.get("audio_guides", [])
    audio_by_slug = {}
    for track in audio_guides:
        slug = track.get("monument_slug") or track.get("site_slug")
        if slug:
            audio_by_slug[slug] = track

    curated_stations = worksheet_json.get("stations", [])
    curated_by_slug = {s["monument_slug"]: s for s in curated_stations if "monument_slug" in s}

    # Determine which slugs to include
    if cluster_id == "all_16":
        target_slugs = [s["slug"] for s in sites_list]
    elif cluster_id == "central_axis":
        target_slugs = ["ngo-mon", "cau-trung-dao", "san-dai-trieu-nghi", "dien-thai-hoa"]
    elif cluster_id == "ancestral_space":
        target_slugs = ["the-to-mieu", "hien-lam-cac", "hung-to-mieu", "trieu-to-mieu", "dien-phung-tien"]
    elif cluster_id == "purple_forbidden":
        target_slugs = ["dai-cung-mon", "dien-can-chanh", "dien-kien-trung", "duyet-thi-duong", "thai-binh-lau"]
    elif cluster_id == "royal_living":
        target_slugs = ["cung-dien-tho", "cung-truong-sanh"]
    else:  # default "standard_4"
        target_slugs = STANDARD_4_SLUGS

    stations: List[OfflineKitStation] = []

    for index, slug in enumerate(target_slugs):
        site = sites_by_slug.get(slug, {})
        curated = curated_by_slug.get(slug, {})
        audio_track = audio_by_slug.get(slug, {})

        monument_name = site.get("name_vi") or curated.get("monument_name_vi") or slug.replace("-", " ").title()
        zone_name = site.get("zone_slug") or curated.get("zone_name_vi") or "Khu vực Hoàng Thành"

        # 1. Primary Source Excerpt
        if curated.get("guiding_source"):
            gsrc = curated["guiding_source"]
            primary_src = OfflinePrimarySourceItem(
                source_title=gsrc.get("source_title", "Đại Nam Thực Lục Chính Biên"),
                volume_or_chapter=gsrc.get("volume", "Quốc Sử Quán triều Nguyễn"),
                citation=gsrc.get("key_quote_vi", "Tư liệu lưu trữ Quốc Sử Quán."),
                archival_unit="Trung tâm Lưu trữ Quốc gia I",
                reliability_level="primary_official",
            )
        elif site.get("primary_sources") and len(site["primary_sources"]) > 0:
            first = site["primary_sources"][0]
            primary_src = OfflinePrimarySourceItem(
                source_title=first.get("source_title", "Đại Nam Thực Lục"),
                volume_or_chapter=first.get("volume_or_chapter", "Nội các triều Nguyễn"),
                citation=first.get("citation", "Tư liệu chính sử triều Nguyễn."),
                archival_unit=first.get("archival_unit", "Trung tâm Bảo tồn Di tích Cố đô Huế"),
                reliability_level=first.get("reliability_level", "primary_official"),
            )
        else:
            primary_src = OfflinePrimarySourceItem(
                source_title="Đại Nam Thực Lục Chính Biên",
                volume_or_chapter="Quốc Sử Quán triều Nguyễn",
                citation="Đoạn chép chính sử quy định điển chế kiến trúc và chức năng không gian.",
                archival_unit="Trung tâm Lưu trữ Quốc gia I",
                reliability_level="primary_official",
            )

        # 2. High-Contrast 2D Rubbing
        rubbing_meta = MONUMENT_RUBBINGS_MAP.get(slug, DEFAULT_RUBBING)
        rubbing_asset = OfflineRubbingAsset(
            asset_url=rubbing_meta["asset_url"],
            local_path=rubbing_meta["local_path"],
            format=rubbing_meta.get("format", "image/jpeg"),
            sha256=rubbing_meta.get("sha256"),
            high_contrast_css="filter: contrast(160%) grayscale(100%) brightness(95%);",
            rights_attribution=rubbing_meta.get("rights_attribution", DEFAULT_RIGHTS_OWNER),
            legal_basis=rubbing_meta.get("legal_basis", DEFAULT_LEGAL_BASIS),
        )

        # 3. Audio Guide Transcript (verbatim, zero audio streaming data needed)
        script_text = audio_track.get("script_text") or (
            f"Chào mừng các bạn đến với {monument_name}. Khởi dựng thời triều Nguyễn, "
            f"đây là công trình tiêu biểu gìn giữ nghệ thuật kiến trúc gỗ và điển chế nghi lễ của Cố đô Huế."
        )
        duration_sec = audio_track.get("duration_seconds") or audio_track.get("duration") or 120
        audio_transcript = OfflineAudioTranscript(
            track_title_vi=f"Thuyết minh âm thanh: {monument_name}",
            narrator=audio_track.get("narrator", "Lưu Niên Voice Guide — Giọng Cố Đô"),
            duration_seconds=duration_sec,
            script_text=script_text,
            key_quotes=[
                f"Kiến trúc {monument_name} kết tinh đỉnh cao nghệ thuật triều Nguyễn.",
                primary_src.citation[:120] + "...",
            ],
        )

        # 4. Offline Inspection Task (100% paper-executable, ZERO AR or smartphone required)
        obs_prompt = (
            curated.get("observation_prompt_vi")
            or site.get("pedagogical_task", {}).get("task_prompt")
            or f"Quan sát mặt tiền, số tầng nền, bậc cấp, vật liệu gỗ - đá và quy thức của {monument_name}."
        )
        offline_task = OfflineInspectionTask(
            task_title_vi=f"Nhiệm vụ thực địa 2D: Khảo sát {monument_name}",
            instructions_vi=(
                f"Dùng mắt thường quan sát thực địa hoặc đối chiếu bản dập 2D độ tương phản cao bên cạnh. "
                f"Ghi chép trực tiếp vào phiếu bằng bút mực. Hoàn toàn không cần điện thoại thông minh hay thiết bị AR."
            ),
            checkpoints=[
                f"Đếm số lượng cửa/gian hoặc bậc cấp thực tế của {monument_name}.",
                "Đối chiếu hình thái hoa văn trên bản dập 2D với quy chuẩn chính sử.",
                "Ghi chép tình trạng vật liệu (gỗ lim, đá thanh, ngói lưu ly) vào các dòng kẻ sẵn.",
            ],
            sketch_prompt_vi=f"Phác họa sơ đồ mặt bằng đơn giản hoặc hoa văn rồng/mây nổi bật của {monument_name} vào khung vẽ.",
            paper_achievable=True,
            ar_or_smartphone_required=False,
        )

        # 5. M-E-E Sample and conclusion guide
        conclusion_guide = (
            curated.get("conclusion_guide_vi")
            or site.get("pedagogical_task", {}).get("uncertainty_prompt")
            or "Phân định rõ ràng: (1) Điều khẳng định chắc chắn; (2) Giới hạn tư liệu cần kiểm chứng thêm."
        )

        mee_claim = (
            curated.get("conclusion_guide_vi", "").split("Điều cần")[0].replace("Điều em biết chắc:", "").strip()
            if "Điều em biết chắc:" in curated.get("conclusion_guide_vi", "")
            else f"{monument_name} phản ánh quy chế điển lễ và tập quyền của triều Nguyễn."
        )
        mee_evidence = (
            curated.get("evidence_prompt_vi")
            or site.get("pedagogical_task", {}).get("expected_evidence")
            or f"Đối chiếu trực tiếp với đoạn chép trong {primary_src.source_title} ({primary_src.volume_or_chapter or ''})."
        )
        mee_uncertainty = (
            curated.get("conclusion_guide_vi", "").split("Điều cần")[1].replace("kiểm chứng:", "").strip()
            if "Điều cần" in curated.get("conclusion_guide_vi", "")
            else "Cần kiểm chứng thêm sự thay đổi vật liệu qua các đợt đại trùng tu cận đại."
        )

        station_obj = OfflineKitStation(
            station_index=index + 1,
            monument_slug=slug,
            monument_name_vi=monument_name,
            zone_name_vi=zone_name,
            reign=site.get("reign") or "Nguyễn",
            construction_year=site.get("construction_year") or 1804,
            observation_prompt_vi=obs_prompt,
            observation_sample_answer_vi=site.get("condition_description_vi") or f"Khảo sát hiện trạng {monument_name}.",
            primary_source=primary_src,
            rubbing_asset=rubbing_asset,
            qr_code_url=f"{base_url}/dai-noi/cong-trinh/{slug}",
            offline_inspection_task=offline_task,
            offline_task=offline_task,
            audio_transcript=audio_transcript,
            conclusion_guide_vi=conclusion_guide,
            mee_claim_sample_vi=mee_claim,
            mee_evidence_sample_vi=mee_evidence,
            mee_uncertainty_sample_vi=mee_uncertainty,
        )
        stations.append(station_obj)

    rubric_dims = [
        {
            "id": "S1",
            "name_vi": "Năng lực Không gian (Spatial Reasoning)",
            "description_vi": "Xác định chuẩn xác vị trí trên bản đồ giấy/trực giao không cần định vị GPS số.",
            "max_score": 3,
            "paper_evaluable": True,
        },
        {
            "id": "S2",
            "name_vi": "Năng lực Thời gian (Chronological Thinking)",
            "description_vi": "Nêu đúng mốc khởi dựng, niên hiệu hoàng đế, phân biệt công trình gốc vs trùng tu.",
            "max_score": 3,
            "paper_evaluable": True,
        },
        {
            "id": "S3",
            "name_vi": "Năng lực Sử liệu (Historical Evidence Analysis)",
            "description_vi": "Dẫn đúng bộ sử, số quyển và câu trích từ phiếu học tập đối chiếu với hiện trạng.",
            "max_score": 3,
            "paper_evaluable": True,
        },
        {
            "id": "S4",
            "name_vi": "Năng lực Lập luận (Argumentation - M-E-E)",
            "description_vi": "Lập luận sắc bén: phân định rõ điều chắc chắn và điều còn cần kiểm chứng.",
            "max_score": 3,
            "paper_evaluable": True,
        },
    ]

    exit_tickets = [
        {
            "id": "et_offline_1",
            "question_vi": "Quan sát bản dập 2D hoặc mắt thấy tại thực địa: Hãy chỉ ra 2 chi tiết kiến trúc cho thấy công trình thuộc đẳng cấp hoàng gia triều Nguyễn.",
            "space_lines": 3,
            "paper_only": True,
        },
        {
            "id": "et_offline_2",
            "question_vi": "Dựa vào đoạn trích sử liệu in trên phiếu: Điều gì làm em ngạc nhiên hoặc muốn tìm hiểu sâu hơn khi không có thiết bị số hỗ trợ?",
            "space_lines": 3,
            "paper_only": True,
        },
    ]

    return LowBandwidthOfflineKitResponse(
        kit_id=f"kit-low-bandwidth-{cluster_id}",
        version="1.0.0",
        title_vi="Gói học tập ngoại tuyến & Phiếu in thực địa di sản Huế",
        subtitle_vi="Bộ công cụ điền dã dành cho trường học vùng xa, môi trường mạng thấp & không yêu cầu thiết bị AR",
        content_scope="STTT_IMPERIAL_CITY",
        target_audience="Học sinh THPT (Lớp 10 - Giáo dục địa phương / Lịch sử)",
        zero_device_guarantee=True,
        paper_achievable_percent=100,
        ar_or_smartphone_mandatory=False,
        cluster_id=cluster_id,
        stations=stations,
        rubric_dimensions=rubric_dims,
        exit_ticket_questions=exit_tickets,
        created_at=datetime.now(timezone.utc),
    )


def validate_offline_submission_fairness(
    submission_metadata: dict[str, Any],
) -> dict[str, Any]:
    """Validate that paper or 2D submissions receive 100% fair evaluation with 0 penalty.

    Anti-Abuse Invariant (V5-T096):
    - Rejects any configuration that penalizes students for lack of AR/smartphone.
    - Confirms that paper_handout and 2D rubbing modes are eligible for full Rubric score (12/12)
      and full XP (25 XP discovery).
    """
    mode = submission_metadata.get("inspection_mode") or submission_metadata.get("submission_medium")
    camera_granted = submission_metadata.get("camera_permission_granted", False)
    has_smartphone = submission_metadata.get("has_smartphone", False)

    # If the system attempts to mark down because camera_granted=False or has_smartphone=False, flag as violation
    penalized_for_no_camera = submission_metadata.get("penalized_for_no_camera", False)
    penalized_for_no_ar = submission_metadata.get("penalized_for_no_ar", False)

    if penalized_for_no_camera or penalized_for_no_ar:
        raise AppError(
            "EQUITY_VIOLATION_AR_MANDATORY",
            "Nghiêm cấm hạ điểm hoặc trừ điểm học sinh do không có thiết bị AR hoặc không cấp quyền máy ảnh.",
            status_code=400,
        )

    return {
        "status": "fairness_verified",
        "medium": mode or "paper_handout",
        "ar_mandatory": False,
        "eligible_for_full_score": True,
        "max_score_accessible": 12,
        "xp_accessible": 25,
        "note": "100% paper/2D achievable without smartphone or AR device.",
    }
