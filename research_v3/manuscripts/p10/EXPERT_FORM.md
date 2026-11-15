# P10 expert validation form (human-only; P10-T19 prerequisite)

> TRẠNG THÁI: BLOCKED — biểu mẫu chuẩn bị trước, KHÔNG có chữ ký thật nào tồn tại.
> Không ai được điền "đồng ý" thay chuyên gia. Mọi ô trống phải giữ nguyên trống.

## A. Thông tin chuyên gia (người thật, không ẩn danh trong hồ sơ gốc)
- Họ tên: ____________________
- Đơn vị / chức danh (VD: giáo viên Lịch sử THPT, Sở GD&ĐT): ____________________
- Số năm giảng dạy Lịch sử THPT: ______
- Đã đọc Thông tư 32/2018/TT-BGDĐT phần Lịch sử trong 12 tháng gần nhất: ☐ Có ☐ Không

## B. Vật liệu chấm (bộ đánh giá, tách khỏi bộ thiết kế)
- Chuỗi A (proposed_spiral_dag) và Chuỗi B (baseline giáo viên) được render thành bảng
  đối tượng theo thứ tự, KHÔNG kèm tên phương pháp (mù tên — packet §2).
- Tệp render: `research_artifacts_v3/runs/p10/p10_run_*.json` → trích
  `ordered_object_ids` + `motif_name_vi`.

## C. Rubric chấm (3 lớp — packet §6 secondary metrics)
| Tiêu chí | Thang | Mô tả |
|---|---|---|
| C1 Tính liên tục (continuity) | 1–4 | mỗi bước nối được với bước trước bằng nội dung rõ |
| C2 Leo thang độ sâu Bloom | 1–4 | lớp sau đòi hỏi thao tác tư duy cao hơn lớp trước |
| C3 Phù hợp CTGDPT 2018 | 1–4 | đối tượng nằm đúng nội dung/dải lớp của CTGDPT |
| C4 Tính khả thi lớp học | 1–4 | dựng được thành tiết dạy 45 phút theo 5512 |

- CVI tính theo Lynn (1986) I-CVI; S-CVI/Ave với n>=6 chuyên gia.
- Mọi chấm lại (revision) phải lưu phiên bản; KHÔNG ghi đè.

## D. Xác nhận từng neo cần chuyên gia (27 dòng needs_expert_review)
Với MỖI dòng `P10-LOCAL-<category>-G<grade>` trong run manifest:
- [ ] Đối chiếu Thông tư 32/2018 (Lịch sử) — neo này có thuộc nội dung lớp đó không?
- [ ] Nếu KHÔNG: ghi mã CTGDPT đúng (nếu có) hoặc đánh dấu LOẠI.
- Chuyên gia ký tên từng trang: ____________

## E. Cam kết của người thực hiện nghiên cứu
- Không chỉnh kết quả chấm; không thêm chuyên gia ảo; không chạy lại đến khi đạt.
- Chuyển đổi trạng thái: chỉ khi (i) >= 6 chuyên gia thật, (ii) duyệt đạo đức có thật,
  (iii) dữ liệu chấm gốc lưu trữ được, mới chuyển P10-T19 → HUMAN_SIGNOFF.

Chữ ký điều phối nghiên cứu: ____________________ Ngày: ______
(Ô này RỖNG cho đến khi có hồ sơ thật — đây là rào cản chống làm giả.)
