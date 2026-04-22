"""
AI teacher helpers for live heritage sessions.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..models import LiveEvent, RagDocument

VALID_MODES = {"hint-first", "direct-answer"}
CHECKPOINT_EVENT_TYPE = "ai_teacher_checkpoint"
_INTERACTION_EVENT_TYPES = {
    "ai_teacher_user_message",
    "ai_voice_request",
    "voice_user_final",
}

_CLUSTER_PATTERNS: dict[str, tuple[str, ...]] = {
    "dinh": (
        "dinh",
        "cao dinh",
        "nhan dinh",
        "chuong dinh",
        "anh dinh",
    ),
    "hoa_tiet": (
        "hoa tiet",
        "hoa van",
        "hinh cham",
        "linh vat",
        "cham khac",
        "hoa la",
    ),
    "chu_khac": (
        "chu khac",
        "minh van",
        "van tu",
        "bia chu",
        "han nom",
        "chu han",
    ),
    "boi_canh_lich_su": (
        "lich su",
        "trieu nguyen",
        "boi canh",
        "thoi ky",
        "gia tri",
        "vai tro",
    ),
}

_CLUSTER_LABELS: dict[str, str] = {
    "dinh": "cum tri thuc ve tung dinh",
    "hoa_tiet": "cum tri thuc ve hoa tiet/hinh cham",
    "chu_khac": "cum tri thuc ve chu khac/minh van",
    "boi_canh_lich_su": "cum tri thuc ve boi canh lich su",
    "tong_quan": "cum tri thuc tong quan Cuu Dinh",
}

_CLUSTER_SCRIPT: dict[str, str] = {
    "dinh": (
        "Khung day hoc: (1) xac dinh ten dinh va boi canh, "
        "(2) giai ma bieu tuong chinh, (3) lien he thong diep lich su."
    ),
    "hoa_tiet": (
        "Khung day hoc: (1) mo ta hinh dang hoa tiet, (2) dien giai y nghia, "
        "(3) lien he voi thoi dai va gia tri nghe thuat."
    ),
    "chu_khac": (
        "Khung day hoc: (1) doc dung ngu canh chu khac, (2) tach tu khoa chinh, "
        "(3) giai thich thong diep duoc khac tren dinh."
    ),
    "boi_canh_lich_su": (
        "Khung day hoc: (1) dat moc thoi gian, (2) noi su kien/chu de lien quan, "
        "(3) ket noi voi gia tri giao duc di san hien nay."
    ),
    "tong_quan": (
        "Khung day hoc: (1) neu buc tranh tong the, (2) chon 1 diem nhan de dao sau, "
        "(3) ket noi y nghia bieu tuong va boi canh lich su."
    ),
}

_FALLBACK_REFERENCES: tuple[dict[str, str], ...] = (
    {
        "source_type": "context",
        "source_id": "cuu-dinh-overview",
        "title": "Tong quan Cuu Dinh (nguon noi bo)",
        "snippet": (
            "Cuu Dinh la bo dong dinh trieu Nguyen, ket hop gia tri lich su, "
            "bieu tuong quyen luc va nghe thuat duc dong."
        ),
    },
    {
        "source_type": "context",
        "source_id": "heritage-reading-method",
        "title": "Phuong phap doc hinh cham di san",
        "snippet": (
            "Uu tien 3 buoc: mo ta hinh the, nhan dien bieu tuong, "
            "doi chieu voi boi canh lich su."
        ),
    },
)


def normalize_mode(mode: str | None) -> str:
    value = (mode or "hint-first").strip().lower()
    if value in VALID_MODES:
        return value
    return "hint-first"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(value: datetime | None) -> datetime:
    if value is None:
        return _utcnow()
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9\\s]", " ", value.lower())


def infer_heritage_cluster(*, message: str, session_title: str | None = None) -> str:
    haystack = _normalize_text(f"{session_title or ''} {message or ''}")
    for cluster, patterns in _CLUSTER_PATTERNS.items():
        if any(pattern in haystack for pattern in patterns):
            return cluster
    return "tong_quan"


def build_system_prompt(
    *,
    mode: str,
    session_title: str | None = None,
    learner_message: str | None = None,
) -> str:
    title = (session_title or "").strip()
    cluster = infer_heritage_cluster(message=learner_message or "", session_title=title)
    cluster_label = _CLUSTER_LABELS.get(cluster, _CLUSTER_LABELS["tong_quan"])
    script_line = _CLUSTER_SCRIPT.get(cluster, _CLUSTER_SCRIPT["tong_quan"])
    context_line = (
        f"Phien hien tai: {title}."
        if title
        else "Phien hien tai: phong hoc di san truc tuyen."
    )
    if mode == "direct-answer":
        policy_line = (
            "Che do direct-answer: tra loi ro rang, ngan gon, dung trong tam, "
            "nhung neu du lieu khong chac chan thi phai noi ro muc do khong chac chan."
        )
    else:
        policy_line = (
            "Che do hint-first: uu tien dat cau hoi goi mo, dua 1-3 buoc goi y, "
            "chua dua dap an day du ngay lap tuc, sau do moi bo sung dap an neu nguoi hoc can."
        )

    return (
        "Ban la Gia su AI thuyet minh di san Viet Nam trong lop live. "
        "Muc tieu la giup nguoi hoc hieu y nghia bieu tuong, boi canh lich su, "
        "gia tri my thuat va lien he voi Cuu Dinh khi phu hop. "
        f"{context_line} Dang day theo {cluster_label}. {script_line} "
        f"{policy_line} "
        "Su dung tieng Viet tu nhien, ro rang, than thien; khong viet qua dai dong. "
        "Khong tao lien ket URL khong co that."
    )


def build_history_messages(
    history: Iterable[dict[str, str]] | None, *, max_items: int = 8
) -> list[dict[str, str]]:
    if not history:
        return []

    cleaned: list[dict[str, str]] = []
    for item in history:
        role = str(item.get("role", "")).strip().lower()
        content = str(item.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue
        cleaned.append({"role": role, "content": content[:3000]})
    if not cleaned:
        return []
    return cleaned[-max_items:]


def fallback_response(*, mode: str, question: str) -> str:
    q = question.strip()
    cluster = infer_heritage_cluster(message=q)
    cluster_hint = _CLUSTER_LABELS.get(cluster, _CLUSTER_LABELS["tong_quan"])
    if mode == "direct-answer":
        return (
            "Tra loi truc tiep: dua tren ngu canh di san, ban nen doi chieu voi "
            "tu lieu trong LMS de chot ket luan chinh xac. "
            f"Trong cau hoi nay, uu tien {cluster_hint}. "
            f"Noi dung cau hoi: {q}"
        )
    return (
        "Goi y truoc: hay xac dinh boi canh lich su, nhan dien hoa tiet/linh vat, "
        "va lien he thong diep bieu tuong cua no. "
        f"Cau hoi nay nghiêng ve {cluster_hint}. "
        f"Cau hoi cua ban: {q}. "
        "Thu neu 1-2 nhan dinh, toi se phan bien va bo sung."
    )


def _source_snippet(value: str | None, *, max_len: int = 220) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 3]}..."


def collect_reference_sources(
    db: Session,
    *,
    query: str,
    limit: int = 3,
) -> list[dict[str, str]]:
    docs = (
        db.execute(
            select(RagDocument)
            .where(RagDocument.is_active.is_(True))
            .order_by(RagDocument.updated_at.desc(), RagDocument.created_at.desc())
            .limit(40)
        )
        .scalars()
        .all()
    )

    if not docs:
        return [dict(item) for item in _FALLBACK_REFERENCES[: max(1, limit)]]

    normalized_query = _normalize_text(query)
    keywords = [token for token in normalized_query.split() if len(token) >= 3][:12]
    scored: list[tuple[float, RagDocument]] = []

    for doc in docs:
        title_norm = _normalize_text(doc.title or "")
        content_norm = _normalize_text(doc.content or "")
        keyword_score = 0.0
        for token in keywords:
            if token in title_norm:
                keyword_score += 2.0
            if token in content_norm:
                keyword_score += 0.6
        # Keep slight recency preference even when keyword score ties.
        recency_bonus = 0.2 if keyword_score > 0 else 0.0
        scored.append((keyword_score + recency_bonus, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    selected_docs = [doc for score, doc in scored if score > 0][:limit]
    if not selected_docs:
        selected_docs = [doc for _, doc in scored[:limit]]

    references: list[dict[str, str]] = []
    for doc in selected_docs:
        references.append(
            {
                "source_type": "rag",
                "source_id": str(doc.id),
                "title": str(doc.title or "Nguon noi bo"),
                "snippet": _source_snippet(doc.content),
            }
        )
    return references


def format_reference_context(sources: Iterable[dict[str, Any]]) -> str:
    lines: list[str] = []
    for idx, source in enumerate(sources, start=1):
        title = str(source.get("title") or "Nguon noi bo")
        snippet = _source_snippet(source.get("snippet") or source.get("content"))
        if snippet:
            lines.append(f"[R{idx}] {title}: {snippet}")
        else:
            lines.append(f"[R{idx}] {title}")
    return "\n".join(lines)


def build_suggested_actions(
    *,
    question: str,
    mode: str,
    cluster: str,
) -> list[dict[str, str]]:
    q = question.strip()
    cluster_actions: dict[str, list[dict[str, str]]] = {
        "dinh": [
            {
                "label": "So sanh 2 dinh",
                "prompt": "So sanh nhanh y nghia bieu tuong giua 2 dinh lien quan den cau hoi tren.",
            },
            {
                "label": "Diem nhan bieu tuong",
                "prompt": "Neu 3 diem nhan bieu tuong quan trong nhat tren dinh nay va vi sao.",
            },
        ],
        "hoa_tiet": [
            {
                "label": "Doc hoa tiet theo 3 buoc",
                "prompt": "Huong dan em doc hoa tiet nay theo 3 buoc: mo ta, dien giai, lien he lich su.",
            },
            {
                "label": "Sai lam thuong gap",
                "prompt": "Nhung nham lan thuong gap khi dien giai hoa tiet nay la gi?",
            },
        ],
        "chu_khac": [
            {
                "label": "Tach tu khoa",
                "prompt": "Tach giup em cac tu khoa quan trong trong phan chu khac va giai nghia ngan gon.",
            },
            {
                "label": "Dat vao boi canh",
                "prompt": "Dat phan chu khac nay vao boi canh lich su cua trieu Nguyen de de hieu hon.",
            },
        ],
        "boi_canh_lich_su": [
            {
                "label": "Moc thoi gian",
                "prompt": "Lap giup em 3 moc thoi gian then chot lien quan den chu de dang hoc.",
            },
            {
                "label": "Lien he hien nay",
                "prompt": "Lien he y nghia chu de nay voi hoc di san hien nay trong 2 y ngan gon.",
            },
        ],
        "tong_quan": [
            {
                "label": "Tong hop 1 phut",
                "prompt": "Tong hop trong 1 phut: diem chinh em can nho tu cau tra loi vua roi.",
            },
            {
                "label": "Dao sau tiep",
                "prompt": "Tu cau hoi nay, nen dao sau tiep vao dinh hay hoa tiet nao de hieu hon?",
            },
        ],
    }

    actions = list(cluster_actions.get(cluster, cluster_actions["tong_quan"]))
    actions.append(
        {
            "label": "Hoi tiep theo",
            "prompt": (
                "Goi y 1 cau hoi tiep theo de em hoc sau hon tu noi dung vua trao doi: "
                f"{q[:180]}"
            ),
        }
    )
    if mode == "hint-first":
        actions.append(
            {
                "label": "Nhan goi y tung buoc",
                "prompt": "Cho em ban goi y tung buoc truoc khi dua dap an day du.",
            }
        )
    return actions[:3]


def should_trigger_checkpoint(
    db: Session,
    *,
    live_session_id: Any,
    session_started_at: datetime | None,
    min_minutes: int = 6,
    min_interactions: int = 3,
) -> bool:
    now = _utcnow()
    session_anchor = _ensure_utc(session_started_at)
    if now - session_anchor < timedelta(minutes=max(1, min_minutes)):
        return False

    last_checkpoint_at = (
        db.execute(
            select(LiveEvent.created_at)
            .where(
                and_(
                    LiveEvent.live_session_id == live_session_id,
                    LiveEvent.event_type == CHECKPOINT_EVENT_TYPE,
                )
            )
            .order_by(LiveEvent.created_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    anchor = _ensure_utc(last_checkpoint_at) if last_checkpoint_at else session_anchor
    if now - anchor < timedelta(minutes=max(1, min_minutes)):
        return False

    interactions = (
        db.execute(
            select(func.count(LiveEvent.id)).where(
                and_(
                    LiveEvent.live_session_id == live_session_id,
                    LiveEvent.created_at >= anchor,
                    LiveEvent.event_type.in_(tuple(_INTERACTION_EVENT_TYPES)),
                )
            )
        ).scalar_one()
    )
    return int(interactions or 0) >= max(1, min_interactions)


def build_checkpoint_prompt(*, cluster: str) -> str:
    checkpoints = {
        "dinh": "Trong 1-2 cau, ban thu neu y nghia bieu tuong chinh cua dinh dang hoc.",
        "hoa_tiet": "Ban thu dien giai y nghia cua hoa tiet nay bang 2 y ngan gon.",
        "chu_khac": "Ban thu tom tat thong diep cua phan chu khac nay trong 1 cau.",
        "boi_canh_lich_su": "Ban thu dat chu de vua hoc vao dung boi canh lich su (thoi ky/su kien).",
        "tong_quan": "Checkpoint nhanh: ban vua rut ra 2 y quan trong nao tu noi dung nay?",
    }
    return checkpoints.get(cluster, checkpoints["tong_quan"])
