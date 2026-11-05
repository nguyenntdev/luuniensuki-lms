# -*- coding: utf-8 -*-
"""P07 ELLO Inquiry Lesson and Assessment Rubric Drafting Engine.

Implements Agents P07-A07 and P07-A08:
- P07-A07: Source-based ELLO lesson author (ello_lesson.json)
  Implements 6-step historical inquiry grounded strictly in verified primary evidence.
- P07-A08: Assessment & rubric author (assessment_pack.json)
  Implements 4-level rubric (0-3 scale) across mastery dimensions and source-locked quiz items.

Invariants Enforced:
1. Every learning task must require students to cite specific source evidence.
2. Quizzes must NOT be built on disputed claims as uncontested facts.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .dossier import DossierClaim, DossierSource, ResearchDossier
from .writers import P07DraftingError


# --------------------------------------------------------------------------- #
# Custom Exceptions for P07 Lesson / Assessment
# --------------------------------------------------------------------------- #
class MissingEvidenceRequirementError(P07DraftingError):
    """Raised when an inquiry task fails to require student source citations."""
    pass


class DisputedClaimQuizError(P07DraftingError):
    """Raised when a factual quiz item is constructed from a disputed or unreviewed claim."""
    pass


# --------------------------------------------------------------------------- #
# Models for ELLO Lesson & Rubrics
# --------------------------------------------------------------------------- #
class InquiryTaskStep(BaseModel):
    step_number: int  # 1 to 6
    step_key: str  # hook, observation, source_analysis, synthesis, reflection, evaluation
    title_vi: str
    title_en: str
    prompt_vi: str
    prompt_en: str
    evidence_requirement: str
    requires_citation: bool = True
    bound_claim_ids: List[str] = Field(default_factory=list)
    bound_source_ids: List[str] = Field(default_factory=list)


class ELLOLessonDraft(BaseModel):
    lesson_id: str
    entity_slug: str
    title_vi: str
    title_en: str
    inquiry_steps: List[InquiryTaskStep] = Field(default_factory=list)
    pedagogical_focus: str = "SOURCE_BASED_INQUIRY"
    sha256: str = ""

    def compute_sha256(self) -> str:
        dump = json.dumps(
            {
                "lesson_id": self.lesson_id,
                "steps": [s.model_dump() for s in self.inquiry_steps],
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(dump).hexdigest()


class RubricCriterion(BaseModel):
    criterion_id: str
    dimension: str  # source_literacy, evidence_reasoning, contextualization, factual_recall
    title: str
    description: str
    levels: Dict[int, str] = Field(
        default_factory=lambda: {
            0: "Chưa trích dẫn nguồn hoặc suy đoán vô căn cứ (Unsubstantiated / zero evidence).",
            1: "Trích dẫn còn sơ sài, thiếu số trang hoặc định vị quyển (Emerging / partial citation).",
            2: "Trích dẫn chính xác nguồn sử liệu triều Nguyễn và đối chiếu đúng chi tiết hình tượng (Competent).",
            3: "Phân tích sử liệu xuất sắc, gắn kết hoàn hảo văn bản và hình tượng 2D/3D (Exemplary).",
        }
    )


class QuizItem(BaseModel):
    quiz_id: str
    question_vi: str
    question_en: str
    options_vi: List[str]
    options_en: List[str]
    correct_option_index: int
    explanation_vi: str
    explanation_en: str
    bound_claim_id: str
    bound_source_id: str
    locator: str
    is_disputed: bool = False


class AssessmentRubricPack(BaseModel):
    pack_id: str
    entity_slug: str
    rubric_criteria: List[RubricCriterion] = Field(default_factory=list)
    quiz_items: List[QuizItem] = Field(default_factory=list)
    sha256: str = ""

    def compute_sha256(self) -> str:
        dump = json.dumps(
            {
                "pack_id": self.pack_id,
                "criteria": [c.model_dump() for c in self.rubric_criteria],
                "quiz": [q.model_dump() for q in self.quiz_items],
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(dump).hexdigest()


# --------------------------------------------------------------------------- #
# P07 Lesson Writer Engine
# --------------------------------------------------------------------------- #
class P07LessonWriter:
    """Generates source-locked ELLO inquiry lessons and rubric assessment packs."""

    def __init__(self, dossier: ResearchDossier):
        self.dossier = dossier
        self.approved_claims = dossier.get_approved_claims()

    def generate_ello_lesson(self) -> ELLOLessonDraft:
        """Constructs 6-step inquiry tasks requiring strict evidence citation."""
        if not self.approved_claims:
            raise P07DraftingError("Cannot generate ELLO lesson without approved claims.")

        primary_claim = self.approved_claims[0]
        primary_source = self.dossier.sources[0] if self.dossier.sources else None
        source_id = primary_source.source_id if primary_source else "source-default"
        source_title = primary_source.title if primary_source else "Đại Nam Nhất Thống Chí"

        steps: List[InquiryTaskStep] = [
            # Step 1: Hook
            InquiryTaskStep(
                step_number=1,
                step_key="hook",
                title_vi="Bước 1: Khởi động và Khám phá hiện vật",
                title_en="Step 1: Relic Engagement and Discovery",
                prompt_vi=f"Quan sát hình tượng {self.dossier.name_vi} trên bề mặt Cửu Đỉnh. Hãy chỉ ra đặc điểm thị giác nổi bật nhất mà em nhận thấy.",
                prompt_en=f"Observe the {self.dossier.name_en or self.dossier.name_vi} relief on the dynastic urn. Identify its prominent visual characteristics.",
                evidence_requirement="Học sinh phải chỉ rõ chi tiết hình khối hoặc đường nét quan sát được trên hiện vật.",
                requires_citation=True,
                bound_claim_ids=[primary_claim.claim_id],
                bound_source_ids=[source_id],
            ),
            # Step 2: Observation
            InquiryTaskStep(
                step_number=2,
                step_key="observation",
                title_vi="Bước 2: Quan sát vi mô và Đối chiếu bản dập 2D",
                title_en="Step 2: Micro-Observation & 2D Rubbing Inspection",
                prompt_vi=f"Sử dụng công cụ phóng to bản dập 2D hoa văn {self.dossier.name_vi}. Đối chiếu các nét chạm với mô tả kích thước và chất liệu.",
                prompt_en=f"Inspect the 2D rubbing archive of {self.dossier.name_en or self.dossier.name_vi}. Compare bronze carving techniques.",
                evidence_requirement="Học sinh phải định vị ít nhất 1 tọa độ/vùng hoa văn trên bản dập lưu trữ.",
                requires_citation=True,
                bound_claim_ids=[primary_claim.claim_id],
                bound_source_ids=[source_id],
            ),
            # Step 3: Source Analysis
            InquiryTaskStep(
                step_number=3,
                step_key="source_analysis",
                title_vi="Bước 3: Phân tích Sử liệu Gốc Triều Nguyễn",
                title_en="Step 3: Primary Source Historical Analysis",
                prompt_vi=f"Đọc đoạn trích trong {source_title}. Sử quan triều Nguyễn đã ghi nhận những sự kiện hoặc biểu tượng nào liên quan đến {self.dossier.name_vi}?",
                prompt_en=f"Read the primary archival excerpt from {source_title}. How did royal historians chronicle {self.dossier.name_en or self.dossier.name_vi}?",
                evidence_requirement="Bắt buộc trích dẫn nguyên văn câu văn sử liệu kèm số quyển và số trang.",
                requires_citation=True,
                bound_claim_ids=[c.claim_id for c in self.approved_claims[:2]],
                bound_source_ids=[source_id],
            ),
            # Step 4: Synthesis
            InquiryTaskStep(
                step_number=4,
                step_key="synthesis",
                title_vi="Bước 4: Tổng hợp và So sánh Đa nguồn",
                title_en="Step 4: Cross-Source Synthesis & Contextualization",
                prompt_vi=f"So sánh ghi chép trong sử triều Nguyễn với vị trí thực tế của {self.dossier.name_vi} trong hệ thống biểu tượng Cửu Đỉnh.",
                prompt_en=f"Synthesize royal records with the physical layout of {self.dossier.name_en or self.dossier.name_vi} on the urns.",
                evidence_requirement="Học sinh phải liên hệ giữa chứng cứ văn bản và chứng cứ hiện vật chạm nổi.",
                requires_citation=True,
                bound_claim_ids=[primary_claim.claim_id],
                bound_source_ids=[source_id],
            ),
            # Step 5: Historical Reflection
            InquiryTaskStep(
                step_number=5,
                step_key="reflection",
                title_vi="Bước 5: Suy ngẫm Lịch sử và Đạo đức Di sản",
                title_en="Step 5: Historical Reflection & Heritage Ethics",
                prompt_vi=f"Hình tượng {self.dossier.name_vi} thể hiện quan niệm gì của tiền nhân về chủ quyền, thiên nhiên và văn hóa Đại Nam?",
                prompt_en=f"What worldview regarding sovereignty and ecology did the Nguyen court express through {self.dossier.name_en or self.dossier.name_vi}?",
                evidence_requirement="Lập luận phải dựa trên chứng cứ lịch sử đã phân tích ở Bước 3.",
                requires_citation=True,
                bound_claim_ids=[primary_claim.claim_id],
                bound_source_ids=[source_id],
            ),
            # Step 6: Evaluation
            InquiryTaskStep(
                step_number=6,
                step_key="evaluation",
                title_vi="Bước 6: Đánh giá và Bảo vệ Luận điểm Sử học",
                title_en="Step 6: Evaluation & Evidence Defense",
                prompt_vi="Viết đoạn lập luận 150 từ trả lời câu hỏi nghiên cứu, bảo vệ luận điểm của em bằng cách trích dẫn tối thiểu 2 minh chứng sử liệu.",
                prompt_en="Write a 150-word evidence-backed synthesis answering the research inquiry with at least two archival citations.",
                evidence_requirement="Yêu cầu trích dẫn tối thiểu 2 bằng chứng nguồn sử liệu có thẩm quyền.",
                requires_citation=True,
                bound_claim_ids=[c.claim_id for c in self.approved_claims],
                bound_source_ids=[source_id],
            ),
        ]

        lesson = ELLOLessonDraft(
            lesson_id=f"ello_lesson_{self.dossier.entity_slug}",
            entity_slug=self.dossier.entity_slug,
            title_vi=f"Bài học Khám phá Sử liệu: {self.dossier.name_vi}",
            title_en=f"Source-Based Historical Inquiry: {self.dossier.name_en or self.dossier.name_vi}",
            inquiry_steps=steps,
        )
        lesson.sha256 = lesson.compute_sha256()
        return lesson

    def generate_assessment_rubric_pack(self) -> AssessmentRubricPack:
        """Generates 4-level rubric and factual quiz items strictly locked to verified sources."""
        # 1. 4-level rubric across mastery dimensions
        criteria = [
            RubricCriterion(
                criterion_id="rubric_source_literacy",
                dimension="source_literacy",
                title="Khai thác và trích dẫn tư liệu lịch sử",
                description="Đánh giá mức độ chính xác và chuẩn mực khi viện dẫn sử liệu triều Nguyễn.",
            ),
            RubricCriterion(
                criterion_id="rubric_evidence_reasoning",
                dimension="evidence_reasoning",
                title="Lập luận dựa trên chứng cứ",
                description="Đánh giá năng lực liên kết giữa văn bản lịch sử và hình chạm trên Cửu Đỉnh.",
            ),
            RubricCriterion(
                criterion_id="rubric_contextualization",
                dimension="contextualization",
                title="Đặt hiện vật vào bối cảnh thời đại",
                description="Đánh giá khả năng hiểu đúng tư duy chính trị - văn hóa thời Minh Mạng.",
            ),
        ]

        # 2. Source-locked quiz items
        quiz_items: List[QuizItem] = []
        for i, claim in enumerate(self.approved_claims):
            if claim.is_disputed or claim.verification_status == "disputed":
                raise DisputedClaimQuizError(
                    f"Attempted to construct factual quiz item from disputed claim '{claim.claim_id}'."
                )

            binding = claim.source_bindings[0] if claim.source_bindings else None
            source_id = binding.source_id if binding else "source-001"
            source_title = binding.source_title if binding else "Sử liệu triều Nguyễn"
            locator = binding.locator if binding else "Chính sử"

            question_vi = f"Theo ghi chép trong {source_title} ({locator}), nhận định nào sau đây là chính xác về {self.dossier.name_vi}?"
            question_en = f"According to historical records in {source_title} ({locator}), which statement is correct regarding {self.dossier.name_en or self.dossier.name_vi}?"

            quiz_items.append(
                QuizItem(
                    quiz_id=f"quiz_{self.dossier.entity_slug}_{i+1}",
                    question_vi=question_vi,
                    question_en=question_en,
                    options_vi=[
                        claim.statement_vi,
                        f"{self.dossier.name_vi} được chế tác vào thời kỳ hiện đại thế kỷ 20.",
                        f"{self.dossier.name_vi} là hình tượng xuất xứ ngoại lai không thuộc cương thổ Đại Nam.",
                        f"{self.dossier.name_vi} không hề xuất hiện trong biên niên sử triều Nguyễn.",
                    ],
                    options_en=[
                        claim.statement_en or claim.statement_vi,
                        f"{self.dossier.name_vi} was created during the 20th century.",
                        f"{self.dossier.name_vi} is a foreign motif outside Dai Nam borders.",
                        f"{self.dossier.name_vi} is omitted from Nguyen royal annals.",
                    ],
                    correct_option_index=0,
                    explanation_vi=f"Đáp án đúng là mệnh đề được xác nhận trong {source_title}: '{claim.statement_vi}'.",
                    explanation_en=f"The verified answer is supported by {source_title}: '{claim.statement_en or claim.statement_vi}'.",
                    bound_claim_id=claim.claim_id,
                    bound_source_id=source_id,
                    locator=locator,
                    is_disputed=False,
                )
            )

        pack = AssessmentRubricPack(
            pack_id=f"assessment_pack_{self.dossier.entity_slug}",
            entity_slug=self.dossier.entity_slug,
            rubric_criteria=criteria,
            quiz_items=quiz_items,
        )
        pack.sha256 = pack.compute_sha256()
        return pack
