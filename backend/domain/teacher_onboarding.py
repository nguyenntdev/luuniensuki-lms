# -*- coding: utf-8 -*-
"""Domain logic for Teacher Onboarding, Support Center, and Student PII Safety (Ticket V5-T099 / W09-A09).

Core mandates:
1. Interactive Teacher Onboarding Tour:
   - Tracks onboarding steps, completion timestamp, and tour dismissal.
   - Differentiates Demo/Preview Mode vs Real School-Verified Mode.
2. Sample Lesson Templates:
   - Curated reference lesson plans structured under CV 5512/BGDĐT.
   - Prominently labeled with is_sample_template=True, template_badge="SAMPLE TEMPLATE",
     and explicit disclaimer ("SAMPLE TEMPLATE - Mẫu giáo án tham khảo phục vụ tập huấn giáo viên").
3. Support Center:
   - Teacher support ticket submission, categorization, priority, and threaded replies.
4. Teacher Training Resources:
   - Curated professional development guides (CV 5512, 2D/3D historical inquiry, Decree 13/2023/ND-CP privacy).
5. Negative Abuse Defense (V5-T099 invariant):
   - Unverified school users and guest teachers CANNOT access real student PII
     (emails, guardian contacts, guardian consent status) or live class records/gradebook.
   - Violations are blocked with HTTP 403 UNVERIFIED_TEACHER_ACCESS_DENIED.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional
import uuid


class OnboardingStep(str, Enum):
    welcome = "welcome"
    curriculum_standards = "curriculum_standards"
    sample_templates = "sample_templates"
    student_privacy = "student_privacy"
    rubric_scoring = "rubric_scoring"
    fieldwork_kit = "fieldwork_kit"
    support_center = "support_center"
    completed = "completed"


class SupportTicketCategory(str, Enum):
    pedagogical_guidance = "pedagogical_guidance"
    curriculum_alignment = "curriculum_alignment"
    technical_issue = "technical_issue"
    account_verification = "account_verification"
    rubric_scoring = "rubric_scoring"
    student_privacy = "student_privacy"
    other = "other"


class SupportTicketPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class SupportTicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class UnverifiedTeacherAccessDeniedError(PermissionError):
    """Raised when an unverified school user or guest teacher attempts to access real student PII or live class records."""
    pass


# --------------------------------------------------------------------------- #
# Verified Sample Lesson Templates
# --------------------------------------------------------------------------- #

SAMPLE_LESSON_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "sample-cao-dinh-dragon-45min",
        "title": "Mẫu Giáo án 45 phút: Khảo sát hình tượng Rồng trên Cao Đỉnh (CV 5512/BGDĐT)",
        "topic": "Ý nghĩa biểu tượng vương quyền thời Nguyễn & Khắc họa trên Cửu Đỉnh",
        "target_grade": "Lớp 10 THPT",
        "duration_minutes": 45,
        "curriculum_framework": "CV 5512/BGDĐT",
        "is_sample_template": True,
        "template_badge": "SAMPLE TEMPLATE",
        "disclaimer": "SAMPLE TEMPLATE - Mẫu giáo án tham khảo phục vụ tập huấn giáo viên, không thay thế hồ sơ thực địa chính thức.",
        "media_variant": "2d_rubbing",
        "objectives": {
            "competencies": [
                "S1: Nhận diện biểu tượng Rồng 5 móng trên Cao Đỉnh",
                "S2: Đối chiếu bản dập nổi với ghi chép trong Đại Nam Thực Lục",
                "S3: Phân tích tính biểu trưng quyền uy vương triều",
                "S4: Rút ra kết luận về nghệ thuật đúc đồng thời Nguyễn",
            ],
            "qualities": ["Lòng tự hào di sản", "Tính trung thực trong trích dẫn tư liệu"],
        },
        "inquiry_activities": [
            {
                "sequence": 1,
                "name": "Khởi động: Kích hoạt tri thức nền & quan sát bản dập",
                "duration_minutes": 5,
                "pedagogy_role": "Quan sát sơ bộ chi tiết chạm khắc rồng trên thân đỉnh",
            },
            {
                "sequence": 2,
                "name": "Khảo sát: Đối chiếu hiện vật với chép sử Đại Nam Thực Lục",
                "duration_minutes": 15,
                "pedagogy_role": "Đối chiếu bản dịch mộc bản với vị trí quai và thân Cao Đỉnh",
            },
            {
                "sequence": 3,
                "name": "Thảo luận: Phân tích tư tưởng độc lập tự chủ và quyền uy",
                "duration_minutes": 15,
                "pedagogy_role": "Làm việc nhóm trên bảng chứng cứ tư liệu",
            },
            {
                "sequence": 4,
                "name": "Đánh giá: Vé ra cửa (Exit Ticket) & Tự lượng giá Rubric",
                "duration_minutes": 10,
                "pedagogy_role": "Tổng hợp kết quả và tự đối chiếu tiêu chí Rubric S1-S4",
            },
        ],
        "assessment_rubric": {
            "framework": "S1-S4 Historical Inquiry Rubric",
            "scale": "0-3 (Chưa đạt, Đạt cơ sở, Khá, Xuất sắc)",
            "criteria": [
                {"code": "S1", "name": "Định vị không gian - hình ảnh", "max_points": 3},
                {"code": "S2", "name": "Xác định niên đại - bối cảnh", "max_points": 3},
                {"code": "S3", "name": "Phân tích sử liệu - hiện vật", "max_points": 3},
                {"code": "S4", "name": "Lập luận & Đánh giá lịch sử", "max_points": 3},
            ],
        },
    },
    {
        "id": "sample-minh-dinh-maritime-45min",
        "title": "Mẫu Chuyên đề: Biển đảo & Hàng hải qua hình tượng Đông Hải trên Minh Đỉnh",
        "topic": "Chủ quyền lãnh thổ biển đảo và kinh tế hàng hải thời Nguyễn qua Cửu Đỉnh",
        "target_grade": "Lớp 11 THPT",
        "duration_minutes": 45,
        "curriculum_framework": "CV 5512/BGDĐT",
        "is_sample_template": True,
        "template_badge": "SAMPLE TEMPLATE",
        "disclaimer": "SAMPLE TEMPLATE - Mẫu giáo án tham khảo phục vụ tập huấn giáo viên, không thay thế hồ sơ thực địa chính thức.",
        "media_variant": "3d_model",
        "objectives": {
            "competencies": [
                "S1: Xác định tọa độ hình khắc Đông Hải trên Minh Đỉnh",
                "S2: Khai thác bản đồ và sử liệu khẳng định chủ quyền Hoàng Sa, Trường Sa",
                "S3: Đánh giá tầm nhìn đại dương của triều Nguyễn",
                "S4: Trình bày bài học bảo vệ chủ quyền biển đảo ngày nay",
            ],
            "qualities": ["Ý thức trách nhiệm công dân đối với chủ quyền biển đảo quốc gia"],
        },
        "inquiry_activities": [
            {
                "sequence": 1,
                "name": "Khởi động: Định vị Đông Hải trên Minh Đỉnh qua mô hình 3D xoay 360",
                "duration_minutes": 7,
                "pedagogy_role": "Học sinh xoay 3D tìm kiếm hình tượng sóng nước và tên chữ Hán Đông Hải",
            },
            {
                "sequence": 2,
                "name": "Phân tích nguồn tư liệu: Khâm Định Đại Nam Hội Điển Sự Lệ",
                "duration_minutes": 13,
                "pedagogy_role": "Đối chiếu quy chế đúc đỉnh với các đảo và hải phận ghi chép trong sử liệu",
            },
            {
                "sequence": 3,
                "name": "Thảo luận nhóm: Tầm nhìn kinh tế biển & Phòng thủ duyên hải",
                "duration_minutes": 15,
                "pedagogy_role": "Hoàn thiện phiếu học tập thực địa và lập luận nhóm",
            },
            {
                "sequence": 4,
                "name": "Tổng kết & Đánh giá năng lực sử học",
                "duration_minutes": 10,
                "pedagogy_role": "Đánh giá qua Rubric tư duy lịch sử",
            },
        ],
        "assessment_rubric": {
            "framework": "S1-S4 Historical Inquiry Rubric",
            "scale": "0-3 (Chưa đạt, Đạt cơ sở, Khá, Xuất sắc)",
            "criteria": [
                {"code": "S1", "name": "Định vị không gian - hình ảnh", "max_points": 3},
                {"code": "S2", "name": "Xác định niên đại - bối cảnh", "max_points": 3},
                {"code": "S3", "name": "Phân tích sử liệu - hiện vật", "max_points": 3},
                {"code": "S4", "name": "Lập luận & Đánh giá lịch sử", "max_points": 3},
            ],
        },
    },
    {
        "id": "sample-flora-fauna-nhan-thuan-dinh-45min",
        "title": "Mẫu Tiết thực địa: So sánh hệ động thực vật trên Nhân Đỉnh và Thuần Đỉnh",
        "topic": "Sản vật địa phương và bức tranh sinh thái Đại Nam thế kỷ XIX",
        "target_grade": "Lớp 8 THCS",
        "duration_minutes": 45,
        "curriculum_framework": "CV 5512/BGDĐT",
        "is_sample_template": True,
        "template_badge": "SAMPLE TEMPLATE",
        "disclaimer": "SAMPLE TEMPLATE - Mẫu giáo án tham khảo phục vụ tập huấn giáo viên, không thay thế hồ sơ thực địa chính thức.",
        "media_variant": "2d_rubbing",
        "objectives": {
            "competencies": [
                "S1: Nhận diện các loài động thực vật bản địa khắc trên Nhân Đỉnh",
                "S2: Phân biệt giá trị kinh tế và giá trị biểu tượng của từng sản vật",
                "S3: Liên hệ với công tác bảo tồn đa dạng sinh học hiện nay",
            ],
            "qualities": ["Yêu thiên nhiên", "Tôn trọng tri thức bản địa"],
        },
        "inquiry_activities": [
            {
                "sequence": 1,
                "name": "Trò chơi mảnh ghép: Tìm sản vật trên Cửu Đỉnh",
                "duration_minutes": 8,
                "pedagogy_role": "Quan sát bản dập 2D cây lúa, cây quế, con voi, cá voi",
            },
            {
                "sequence": 2,
                "name": "Điều tra tư liệu: Tại sao triều đình đưa sản vật lên Đỉnh thần?",
                "duration_minutes": 15,
                "pedagogy_role": "Phân tích trích đoạn Đại Nam Nhất Thống Chí",
            },
            {
                "sequence": 3,
                "name": "Báo cáo thực địa thu nhỏ",
                "duration_minutes": 12,
                "pedagogy_role": "Học sinh trình bày tranh luận theo tiêu chí Rubric",
            },
            {
                "sequence": 4,
                "name": "Lượng giá cuối bài",
                "duration_minutes": 10,
                "pedagogy_role": "Thu phiếu học tập và chấm điểm nhanh",
            },
        ],
        "assessment_rubric": {
            "framework": "S1-S4 Historical Inquiry Rubric",
            "scale": "0-3 (Chưa đạt, Đạt cơ sở, Khá, Xuất sắc)",
            "criteria": [
                {"code": "S1", "name": "Định vị không gian - hình ảnh", "max_points": 3},
                {"code": "S2", "name": "Xác định niên đại - bối cảnh", "max_points": 3},
                {"code": "S3", "name": "Phân tích sử liệu - hiện vật", "max_points": 3},
                {"code": "S4", "name": "Lập luận & Đánh giá lịch sử", "max_points": 3},
            ],
        },
    },
]


# --------------------------------------------------------------------------- #
# Teacher Training Resources
# --------------------------------------------------------------------------- #

TEACHER_TRAINING_RESOURCES: list[dict[str, Any]] = [
    {
        "id": "tr-mod-01-cv5512",
        "title": "Tập huấn Khung bài dạy Lịch sử 45 phút theo Công văn 5512/BGDĐT",
        "duration_minutes": 30,
        "format": "video_and_guidebook",
        "category": "curriculum_standards",
        "is_mandatory_for_verification": True,
        "summary": "Hướng dẫn chi tiết xây dựng kế hoạch bài dạy môn Lịch sử đáp ứng chương trình GDPT 2018, tích hợp 4 hoạt động nối tiếp (Khởi động, Khảo sát, Thảo luận, Đánh giá).",
        "resource_url": "/docs/training/cv5512-guideline.pdf",
    },
    {
        "id": "tr-mod-02-rubric-s1-s4",
        "title": "Phương pháp chấm Rubric tư duy lịch sử S1-S4 & Hiệu chuẩn đồng thuận",
        "duration_minutes": 25,
        "format": "interactive_module",
        "category": "rubric_scoring",
        "is_mandatory_for_verification": True,
        "summary": "Tiêu chuẩn hóa thang điểm 0-3 cho 4 tiêu chí năng lực (Không gian, Thời gian, Sử liệu, Lập luận); phương pháp giải quyết độ lệch đánh giá giữa hai giám khảo.",
        "resource_url": "/docs/training/rubric-calibration-guide.pdf",
    },
    {
        "id": "tr-mod-03-privacy-ethics",
        "title": "Bảo vệ dữ liệu cá nhân học sinh & Đạo đức nghiên cứu thực địa (Nghị định 13/2023/NĐ-CP)",
        "duration_minutes": 20,
        "format": "video_and_checklist",
        "category": "student_privacy",
        "is_mandatory_for_verification": True,
        "summary": "Quy định bắt buộc về chấp thuận của phụ huynh (Guardian Consent), khử định danh PII học sinh và lưu trữ hồ sơ lớp học an toàn.",
        "resource_url": "/docs/training/privacy-ethics-handbook.pdf",
    },
    {
        "id": "tr-mod-04-media-variants",
        "title": "Tối ưu hóa thiết bị: Dập nổi 2D băng thông thấp vs Mô hình 3D thực địa",
        "duration_minutes": 20,
        "format": "technical_guide",
        "category": "technical_guidance",
        "is_mandatory_for_verification": False,
        "summary": "Khai thác hiệu quả bộ tư liệu dập nổi 2D khi trường học mất kết nối Internet hoặc thiết bị học sinh không hỗ trợ WebGL 3D.",
        "resource_url": "/docs/training/2d-3d-classroom-toolkit.pdf",
    },
]


# --------------------------------------------------------------------------- #
# Security & Negative Abuse Enforcement Functions
# --------------------------------------------------------------------------- #

def verify_teacher_school_access(
    user: Any,
    classroom: Any = None,
    allow_admin: bool = True,
) -> bool:
    """Verify that a user is a school-verified teacher authorized to access real student PII.

    Negative abuse invariant (V5-T099):
    - Unverified school users / guest teachers CANNOT access real student PII or live class records.
    - If user is guest or user.is_school_verified is False, raises UnverifiedTeacherAccessDeniedError.
    """
    if not user:
        raise UnverifiedTeacherAccessDeniedError(
            "UNVERIFIED_TEACHER_ACCESS_DENIED: Authentication required."
        )

    role_str = getattr(user.role, "value", str(user.role))
    if role_str == "guest":
        raise UnverifiedTeacherAccessDeniedError(
            "UNVERIFIED_TEACHER_ACCESS_DENIED: Guest teachers cannot access real student PII or live class records."
        )

    if allow_admin and role_str in ("admin", "super_admin"):
        return True

    if role_str != "teacher":
        raise UnverifiedTeacherAccessDeniedError(
            "UNVERIFIED_TEACHER_ACCESS_DENIED: Only verified teachers and school administrators can access real student PII."
        )

    # Check school verification status on user
    is_school_verified = getattr(user, "is_school_verified", True)
    if not is_school_verified:
        raise UnverifiedTeacherAccessDeniedError(
            "UNVERIFIED_TEACHER_ACCESS_DENIED: Unverified school users cannot access real student PII or live class records. Please submit an account verification request."
        )

    return True


def sanitize_roster_for_unverified_viewer(roster_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sanitize student roster for unverified teachers or demo mode viewers.

    Strictly redacts email, guardian_email, and guardian_consent, and replaces real names with anonymous tokens.
    """
    sanitized: list[dict[str, Any]] = []
    for idx, student in enumerate(roster_data, start=1):
        sanitized.append({
            "id": student.get("id"),
            "user_id": student.get("user_id"),
            "display_name": f"Học Sinh Mẫu #{idx} (Demo Anonymous)",
            "email": None,
            "role": student.get("role", "learner"),
            "joined_at": student.get("joined_at"),
            "guardian_email": None,
            "guardian_consent": None,
            "is_demo_sanitized": True,
        })
    return sanitized
