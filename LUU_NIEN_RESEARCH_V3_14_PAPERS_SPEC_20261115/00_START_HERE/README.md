# LƯU NIÊN — Research V3 / Full execution spec (14-paper portfolio)
**Ngày khóa:** 2026-11-15 (Asia/Ho_Chi_Minh). **Baseline:** `6debec211f240375f5b967fe2eac7f6450c3e53c` (`main`).
**Đây là tài liệu giao việc, KHÔNG phải kết quả đã chạy.**

## Đọc theo thứ tự
1. `01_AUDIT/GITHUB_BASELINE_AND_GAPS.md` + `01_AUDIT/HIGH_PRIORITY_AUDIT_FINDINGS.md`: evidence và source defects cần sửa trước.
2. `01_AUDIT/LN_TO_P_MAPPING.md`: ánh xạ LN-01..10 → 14 bài P01..P14, ngăn salami slicing.
3. `02_ARCHITECTURE/RESEARCH_V3_ARCHITECTURE.md`: kiến trúc, modules, hợp đồng code.
4. `03_DATA/DATA_ACQUISITION_AND_LICENSES.md`: external datasets + license gate.
5. `04_METHODOLOGY/SCIENTIFIC_EVALUATION.md` + `04_METHODOLOGY/NOVELTY_AND_LITERATURE.md`.
6. `05_PAPERS/Pxx_*.md`: paper execution packets (14 files).
7. `06_TASK_TRACKER/V3_TASK_REGISTER.csv` + `06_TASK_TRACKER/V3_TASK_REGISTER.json`: tracker máy đọc được.
8. `07_AGENTS/10_AGENT_EXECUTION_PLAN.md`: xếp waves, tránh concurrent writes.
9. `07_AGENTS/GOAL_FOR_CODEAGENT.md`: copy nguyên văn vào /goal.
10. `08_RELEASE/RELEASE_GATES.md`: checklist trước khi viết và submit.

## Phạm vi so với spec trước
- ĐỘC LẬP với `LUU_NIEN_V6_MASTER_AND_MODULAR_SPECS_WITH_MOBILE/...`, `research/` v1 và `research_v2/`.
- Không ghi đè research V2, artifacts legacy, hoặc sửa production để đạt metric khoa học.
- LƯU NIÊN là nền tảng/case study; 14 bài là *portfolio dự kiến*, chưa có 14 bằng chứng độc lập.
- Tập trung thực nghiệm external datasets, baseline mạnh, ML/FL nơi có RQ phù hợp, ấn phẩm khoa học và ethics; không biến V3 thành 14 phiên bản của cùng feature.
- Chỉ chốt bài khi xác minh novelty độc lập; P04/P08 được phép gộp/hủy.

## Chỉ thị trạng thái
`EXISTING_VERIFIED_ON_GITHUB` = file/CI đọc trực tiếp; `REPO_CLAIM` = báo cáo đã ghi trong repo; `UNVERIFIED` = chưa chạy độc lập/thiếu chứng cứ; `BLOCKED` = phụ thuộc dữ liệu/giấy phép/đạo đức; `TODO` = việc mới chưa triển khai.

## Mục tiêu nghiệm thu
Mỗi bài có tối thiểu một dataset ngoài thực sự phù hợp với outcome (hoặc corpus gốc + annotation thực đối với bài định tính/di sản), comparators comparable; no train/test leakage; full negative results; đủ độ tin cậy; tính độc lập và reproducibility. Không có guarantee vượt baseline, conference hay HĐGSNN.

Xem snapshot: https://github.com/nguyenntdev/luuniensuki-lms/tree/6debec211f240375f5b967fe2eac7f6450c3e53c
