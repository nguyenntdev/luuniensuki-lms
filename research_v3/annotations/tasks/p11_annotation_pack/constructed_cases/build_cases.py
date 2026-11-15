"""Deterministic constructed calibration cases for the P11 annotation pack.

These are BUILT structures (not observed student work, not human data). They pin the
scorer to expected levels and give future raters a shared calibration set. Every consumer
must label them "constructed, not human" — they carry no validity evidence.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research_v3.methods.p11.rubric import (
    Claim,
    EvidenceItem,
    EvidenceLink,
    HistoricalReasoningResponse,
    InferenceType,
    LinkRelation,
    Provenance,
    SourceType,
    score_response,
)

CASE_DIR = Path(__file__).parent


def cc01_zero_evidence() -> HistoricalReasoningResponse:
    """Negative case: rich claims, zero evidence -> everything capped low."""
    return HistoricalReasoningResponse(
        response_id="CC01_zero_evidence",
        evidence=(),
        claims=(
            Claim("c1", "Nhà Nguyễn xây dựng hệ thống văn miếu để giáo dục Nho học.", is_causal=True, inference_type=InferenceType.CAUSAL),
            Claim("c2", "Điều này cho thấy triều đình coi trọng giáo dục.", inference_type=InferenceType.EXPLANATORY),
        ),
        links=(),
    )


def cc02_asserted_only() -> HistoricalReasoningResponse:
    """Level-1 floor: evidence asserted, no provenance, no links, descriptive only."""
    return HistoricalReasoningResponse(
        response_id="CC02_asserted_only",
        evidence=(EvidenceItem("e1", text="Có rất nhiều văn bia ở Văn Miếu."),),
        claims=(Claim("c1", "Văn bia cho thấy các kỳ thi diễn ra thường xuyên.", inference_type=InferenceType.DESCRIPTIVE),),
        links=(),
    )


def cc03_described_cited() -> HistoricalReasoningResponse:
    """Mid levels: provenance described, support linked, dated context, explanatory inference."""
    return HistoricalReasoningResponse(
        response_id="CC03_described_cited",
        evidence=(
            EvidenceItem("e1", source_type=SourceType.PRIMARY, provenance=Provenance.DESCRIBED, text="Bia Tiến sĩ năm 1484 ghi danh các trạng nguyên."),
            EvidenceItem("e2", source_type=SourceType.SECONDARY, provenance=Provenance.DESCRIBED, text="Sách sử triều Nguyễn mô tả quy chế thi Hội."),
        ),
        claims=(Claim("c1", "Hệ thống khoa cử được chuẩn hóa dưới triều Nguyễn.", inference_type=InferenceType.EXPLANATORY),),
        links=(
            EvidenceLink("c1", "e1", LinkRelation.SUPPORTS),
            EvidenceLink("c1", "e2", LinkRelation.SUPPORTS),
            EvidenceLink("c1", "e2", LinkRelation.CONTEXTUALIZES),
        ),
    )


def cc04_full_chain() -> HistoricalReasoningResponse:
    """Top levels: cited authentic sources with locators, cross-check incl. refutation, constraining context, explicit chain."""
    return HistoricalReasoningResponse(
        response_id="CC04_full_chain",
        evidence=(
            EvidenceItem("e1", source_type=SourceType.PRIMARY, provenance=Provenance.CITED, is_authentic=True, locator="VNM_stela_1484_faceA_line12", text="Bia Tiến sĩ 1484: 'Khoa thi này chọn được 33 tiến sĩ'."),
            EvidenceItem("e2", source_type=SourceType.PRIMARY, provenance=Provenance.CITED, is_authentic=True, locator="QTNL_q7_folia_31", text="Khâm định Việt sử thông giám cương mục, quyển 7: quy chế thi Hội."),
            EvidenceItem("e3", source_type=SourceType.SECONDARY, provenance=Provenance.CITED, is_authentic=True, locator="phantich_2019_p42", text="Nghiên cứu thống kê số lượng đỗ đạt theo khoa."),
        ),
        claims=(
            Claim("c1", "Khoa cử thời Nguyễn chuẩn hóa cao hơn thời Lê sơ (giới hạn trong phạm vi Bắc Việt thời kỳ 1802-1884).", is_causal=True, inference_type=InferenceType.CAUSAL, scope_limited=True),
            Claim("c2", "Nếu không có quy chế mới, số đỗ đạt sẽ phân tán hơn (phản chứng).", inference_type=InferenceType.COUNTERFACTUAL),
        ),
        links=(
            EvidenceLink("c1", "e1", LinkRelation.SUPPORTS),
            EvidenceLink("c1", "e2", LinkRelation.SUPPORTS),
            EvidenceLink("c1", "e3", LinkRelation.REFUTES),  # statistics limit the claim's strength
            EvidenceLink("c1", "e2", LinkRelation.CONTEXTUALIZES),
        ),
    )


def cc05_fabricated_citation() -> HistoricalReasoningResponse:
    """Stress family 'dẫn nguồn giả': citations exist but none authentic -> S1 capped at 1."""
    return HistoricalReasoningResponse(
        response_id="CC05_fabricated_citation",
        evidence=(
            EvidenceItem("e1", source_type=SourceType.PRIMARY, provenance=Provenance.CITED, is_authentic=False, text="Tư liệu 'Đại Nam thực lục bí sử' (không tồn tại)."),
            EvidenceItem("e2", source_type=SourceType.PRIMARY, provenance=Provenance.CITED, is_authentic=False, text="Tư liệu 'Sắc lệnh triều Nguyễn 1832' (không kiểm chứng được)."),
        ),
        claims=(Claim("c1", "Triều Nguyễn cấm người dân tự đúc chuông (thời Minh Mạng).", inference_type=InferenceType.EXPLANATORY),),
        links=(
            EvidenceLink("c1", "e1", LinkRelation.SUPPORTS),
            EvidenceLink("c1", "e2", LinkRelation.SUPPORTS),
            EvidenceLink("c1", "e2", LinkRelation.CONTEXTUALIZES),
        ),
    )


def cc06_refutation_handled() -> HistoricalReasoningResponse:
    """Refutation engaged: cross-checked corroboration with an explicit refutes link."""
    return HistoricalReasoningResponse(
        response_id="CC06_refutation_handled",
        evidence=(
            EvidenceItem("e1", source_type=SourceType.PRIMARY, provenance=Provenance.CITED, is_authentic=True, locator="HCMC_archive_box3_doc17", text="Bản dịch truyền giáo báo cáo năm 1866."),
            EvidenceItem("e2", source_type=SourceType.PRIMARY, provenance=Provenance.CITED, is_authentic=True, locator="TTTGCM_q44_folia_8", text="Cương mục ghi chép chính sách đối với truyền đạo."),
        ),
        claims=(Claim("c1", "Chính sách cấm đạo những năm 1860 thi hành không đồng đều giữa các tỉnh (giới hạn tỉnh Bắc Kỳ, 1862-1870).", is_causal=True, inference_type=InferenceType.CAUSAL, scope_limited=True),),
        links=(
            EvidenceLink("c1", "e1", LinkRelation.SUPPORTS),
            EvidenceLink("c1", "e2", LinkRelation.REFUTES),  # court records suggest uniform policy; response engages this
            EvidenceLink("c1", "e1", LinkRelation.CONTEXTUALIZES),
        ),
    )


CONSTRUCTORS = {
    "CC01_zero_evidence": cc01_zero_evidence,
    "CC02_asserted_only": cc02_asserted_only,
    "CC03_described_cited": cc03_described_cited,
    "CC04_full_chain": cc04_full_chain,
    "CC05_fabricated_citation": cc05_fabricated_citation,
    "CC06_refutation_handled": cc06_refutation_handled,
}


def serialize_case(resp: HistoricalReasoningResponse) -> dict:
    return {
        "response_id": resp.response_id,
        "label": "CONSTRUCTED_NOT_HUMAN",
        "evidence": [
            {
                "evidence_id": e.evidence_id,
                "source_type": e.source_type.value,
                "provenance": e.provenance.value,
                "is_authentic": e.is_authentic,
                "locator": e.locator,
                "text": e.text,
            }
            for e in resp.evidence
        ],
        "claims": [
            {"claim_id": c.claim_id, "text": c.text, "is_causal": c.is_causal, "inference_type": c.inference_type.value}
            for c in resp.claims
        ],
        "links": [
            {"claim_id": l.claim_id, "evidence_id": l.evidence_id, "relation": l.relation.value}
            for l in resp.links
        ],
    }


def write_all() -> dict[str, str]:
    """Write CC01-CC06 JSON + expected_levels.csv; returns {case_id: sha256}."""
    hashes: dict[str, str] = {}
    expected_rows = ["case_id,expected_S1,expected_S2,expected_S3,expected_S4,note"]
    expected = {
        "CC01_zero_evidence": (0, 0, 0, 1),
        "CC02_asserted_only": (1, 1, 1, 1),
        "CC03_described_cited": (2, 2, 2, 2),
        "CC04_full_chain": (3, 3, 3, 3),
        "CC05_fabricated_citation": (1, 2, 2, 2),
        "CC06_refutation_handled": (3, 3, 3, 3),
    }
    for case_id, ctor in CONSTRUCTORS.items():
        resp = ctor()
        result = score_response(resp)
        payload = serialize_case(resp)
        payload["scorer_output"] = {
            "scores": {k: (v.value if hasattr(v, "value") else v) for k, v in result.scores.items()},
            "overall": result.overall,
            "caps_applied": list(result.caps_applied),
        }
        path = CASE_DIR / f"{case_id}.json"
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        path.write_text(text, encoding="utf-8")
        hashes[case_id] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        exp = expected[case_id]
        got = tuple(
            result.scores[c] if isinstance(result.scores[c], int) else -1
            for c in ("S1_sourcing", "S2_corroboration", "S3_contextualization", "S4_argumentation")
        )
        if got != exp:
            raise AssertionError(f"{case_id}: scorer produced {got}, codebook expects {exp}")
        expected_rows.append(f"{case_id},{exp[0]},{exp[1]},{exp[2]},{exp[3]},constructed_not_human")
    (CASE_DIR / "expected_levels.csv").write_text("\n".join(expected_rows) + "\n", encoding="utf-8")
    return hashes


if __name__ == "__main__":
    import json as _json

    print(_json.dumps(write_all(), indent=2))
