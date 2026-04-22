# Cải thiện trải nghiệm người học (Learning Experience) cho Luuniensuki LMS

Ngày cập nhật: 2026-04-16

Tài liệu liên quan:
- `docs/EDTECH_RESEARCH_INNOVATIONS_2026.md` (các tính năng mới dựa trực tiếp trên nghiên cứu EdTech 2024-2026)

## 1) Mục tiêu

Tài liệu này tập trung vào cải thiện **trải nghiệm học thực tế** (không chỉ tính năng AI), theo 3 trục:

- Giảm ma sát trong hành trình học (discover -> lesson -> quiz -> review)
- Tăng cảm giác tiến bộ và động lực nội tại
- Tăng tỉ lệ hoàn thành và giữ chân bằng can thiệp đo lường được

## 2) Điểm ma sát chính quan sát từ codebase hiện tại

1. Daily missions hiển thị tiến độ tốt nhưng chưa có CTA đi thẳng tới hành động tiếp theo.
- Bằng chứng: `frontend/src/components/dashboard/DailyMissionsCard.jsx` (chỉ render card/progress, chưa có nút hành động theo từng mission).

2. Quiz có điều hướng câu hỏi và hint modal, nhưng chưa có cơ chế khôi phục phiên làm bài nếu reload/rớt mạng.
- Bằng chứng: `frontend/src/app/motif/[motifId]/quiz/page.jsx` (state answers/timer giữ trong memory component).

3. Onboarding đang là 1 lần duy nhất theo localStorage, chưa cá nhân hóa theo bối cảnh màn hình.
- Bằng chứng: `frontend/src/components/OnboardingModal.jsx` (`hasSeenOnboarding` global key).

4. Hearts UX còn thiếu một số phần trong luồng học chính.
- Bằng chứng: `frontend/src/components/hearts/README.md` mục Future Enhancements (No hearts overlay, integration với quiz).

5. AI Hub tồn tại như một trang riêng; trong lúc học/quiz, trợ giúp theo ngữ cảnh chưa “inline-first”.
- Bằng chứng: `frontend/src/app/ai/page.jsx` và link AI từ quiz hiện theo hướng điều hướng trang.

## 3) Gói cải tiến ưu tiên (12 hạng mục)

## Nhóm A: Quick wins (1-2 sprint)

### A1. Mission CTA trực tiếp

- Thay vì chỉ hiển thị nhiệm vụ, thêm nút “Làm ngay” cho từng loại mission.
- Ví dụ: mission `quiz` -> mở `/motif/{next}/quiz`; mission `discovery` -> mở `/urns/{slug}?focus=next`.
- Tác động kỳ vọng: tăng mission completion rate 10-18%.

File/API liên quan:
- `frontend/src/components/dashboard/DailyMissionsCard.jsx`
- `GET /api/v1/dashboard/summary`, `GET /api/v1/daily-missions`

---

### A2. Quiz auto-save + resume

- Lưu `answers`, `currentQuestionIndex`, `elapsedTime` theo `motifId` vào localStorage mỗi 3-5s.
- Khi vào lại quiz, hỏi người học “Tiếp tục phiên trước?”
- Tác động kỳ vọng: giảm drop-off giữa chừng 15-25%.

File/API liên quan:
- `frontend/src/app/motif/[motifId]/quiz/page.jsx`

---

### A3. Thanh tiến độ quiz rõ ràng hơn

- Thêm mini-map câu hỏi: trạng thái `đã trả lời/chưa trả lời/đang chọn`.
- Nút “đến câu chưa làm đầu tiên”.
- Tác động kỳ vọng: giảm thời gian hoàn thành quiz, giảm bỏ sót câu.

File/API liên quan:
- `frontend/src/app/motif/[motifId]/quiz/page.jsx`

---

### A4. Hint UX minh bạch chi phí

- Trước khi mở modal hint: hiển thị rõ số hearts hiện có + chi phí từng hint ngay tại header câu hỏi.
- Nếu không đủ hearts, cung cấp fallback “xem giải thích miễn phí dạng rút gọn”.
- Tác động kỳ vọng: giảm frustration, tăng perceived fairness.

File/API liên quan:
- `frontend/src/app/motif/[motifId]/quiz/page.jsx`
- `frontend/src/components/hearts/*`
- `POST /api/v1/quiz/questions/{questionId}/hint`

---

### A5. Onboarding theo ngữ cảnh màn hình

- Thay onboarding global một lần bằng onboarding theo ngữ cảnh:
  - lần đầu vào 3D viewer
  - lần đầu vào quiz
  - lần đầu vào daily missions
- Tác động kỳ vọng: tăng activation các tính năng cốt lõi.

File/API liên quan:
- `frontend/src/components/OnboardingModal.jsx`
- `frontend/src/components/viewer/*`

---

### A6. One-click “Tiếp tục học” nhất quán toàn hệ

- Chuẩn hóa cùng một CTA “Tiếp tục học” ở Dashboard, Urn, Profile, Result.
- Luôn trỏ tới next best action (lesson/quiz/review) thay vì nhiều link phân tán.
- Tác động kỳ vọng: tăng session depth.

File/API liên quan:
- `frontend/src/app/dashboard/page.jsx`
- `frontend/src/components/UrnExperience.js`
- `GET /api/v1/dashboard/summary`

## Nhóm B: Mid-term (2-4 sprint)

### B1. Inline AI trợ giúp theo ngữ cảnh (không rời trang)

- Ở lesson/quiz: mở AI panel trượt bên phải với context sẵn (`motifId`, `urnSlug`).
- Mẫu prompt nhanh: “Giải thích câu này”, “Cho ví dụ dễ hơn”, “Tạo 1 câu luyện tương tự”.
- Tác động kỳ vọng: tăng chất lượng hỗ trợ ngay thời điểm cần.

File/API liên quan:
- `frontend/src/app/ai/page.jsx` (tách thành reusable panel)
- `frontend/src/app/motif/[motifId]/quiz/page.jsx`
- `POST /api/v1/ai/tutor/stream`, `/api/v1/ai/qa`

---

### B2. Review ngay sau quiz sai (1-click)

- Sau kết quả quiz, gom câu sai thành “gói ôn lại ngay” (flashcard/practice mini-session).
- Có nút “Ôn phần sai (3-5 phút)” thay vì chỉ “Làm lại toàn bộ”.
- Tác động kỳ vọng: cải thiện retention D7.

File/API liên quan:
- `frontend/src/app/motif/[motifId]/quiz/page.jsx`
- `frontend/src/app/practice/results/page.jsx`
- `GET /api/v1/review/due`, `POST /api/v1/review/{cardId}`

---

### B3. Hearts fail-safe UX

- Bổ sung `NoHeartsOverlay` đúng luồng quiz: giải thích rõ lựa chọn (đợi hồi tim / dùng gems / chuyển sang practice không tốn tim).
- Tránh dead-end khi người học bị chặn bất ngờ.
- Tác động kỳ vọng: giảm churn ở người dùng mới.

File/API liên quan:
- `frontend/src/components/hearts/README.md` (đã nêu thiếu)
- `frontend/src/components/hearts/HeartsRefillModal.jsx`
- quiz pages

---

### B4. Daily goal feedback loop tốt hơn

- Khi đạt mốc ngày: hiển thị “what next” ngay (ví dụ: nhiệm vụ ngắn 5 phút để kéo dài streak).
- Tránh trạng thái “xong mục tiêu rồi nhưng không biết làm gì tiếp”.
- Tác động kỳ vọng: tăng streak continuity.

File/API liên quan:
- `frontend/src/components/dashboard/DailyGoalCard.jsx`
- `frontend/src/components/dashboard/DailyMissionsCard.jsx`

---

### B5. Learning Path timeline hóa

- Thay danh sách rời rạc bằng timeline “Hôm nay: 15 phút -> 3 chặng”.
- Có ước tính thời lượng từng chặng + nút tiếp tục.
- Tác động kỳ vọng: tăng perceived manageability.

File/API liên quan:
- dashboard/learning path UI
- `GET /api/v1/learning-path/today`, `POST /api/v1/learning-path/complete-item`

---

### B6. Khen thưởng chất lượng học, không chỉ số lượng

- Bonus XP/Badge cho hành vi học sâu: tự giải không hint, cải thiện ở lần làm lại, hoàn thành ôn tập sau sai.
- Tác động kỳ vọng: chuyển động lực từ “farm điểm” sang “mastery”.

File/API liên quan:
- gamification services + event tracking
- badge/hearts/gems stores

## Nhóm C: Advanced (4+ sprint)

### C1. Trợ lý học tập chủ động theo thời điểm

- Notification thông minh theo nhịp học cá nhân (không spam): nhắc ôn thẻ sắp quên, nhắc hoàn tất path còn dang dở.
- Tác động kỳ vọng: tăng DAU và D7 return rate.

File/API liên quan:
- push notification services
- daily mission/review stats

---

### C2. Accessibility nâng cao cho người học phổ rộng

- Quiz/Lesson chuẩn hóa keyboard-only, tăng tương phản, hỗ trợ screen reader tốt hơn ở các widget tùy biến.
- Tác động kỳ vọng: tăng completion ở nhóm thiết bị yếu/người dùng có nhu cầu hỗ trợ.

File/API liên quan:
- quiz, viewer, sidebar components

---

### C3. Offline-first cho các luồng ngắn

- Cache lesson text, lưu draft quiz, retry submit khi online lại.
- Tác động kỳ vọng: giảm mất dữ liệu và bỏ cuộc do mạng không ổn định.

File/API liên quan:
- frontend API layer (`frontend/src/lib/api.js`)
- local persistence strategy

## 4) KPI bắt buộc để đo hiệu quả UX

1. `activation_rate_day0`: hoàn thành bài học đầu tiên trong ngày đăng ký.
2. `quiz_completion_rate`: tỉ lệ hoàn thành quiz đã bắt đầu.
3. `quiz_resume_rate`: tỉ lệ phiên quiz được resume thành công.
4. `mission_completion_rate`: tỉ lệ hoàn thành nhiệm vụ ngày.
5. `hint_overuse_rate`: tỉ lệ câu hỏi dùng hint > ngưỡng.
6. `d7_retention`: quay lại sau 7 ngày.
7. `time_to_next_action`: thời gian từ lúc vào app đến hành động học đầu tiên.

## 5) Thiết kế thí nghiệm đề xuất (A/B)

- EXP-UX-01: Mission CTA vs không CTA.
- EXP-UX-02: Quiz autosave/resume vs baseline.
- EXP-UX-03: Inline AI panel vs chuyển sang AI page.
- EXP-UX-04: NoHeartsOverlay fail-safe vs modal hiện tại.

Mỗi thí nghiệm theo dõi tối thiểu:
- conversion chính
- thời gian hoàn thành
- tỷ lệ lỗi/thoát giữa chừng

## 6) Backlog triển khai ngay (4 tuần)

Tuần 1:
- A1 Mission CTA
- A2 Quiz autosave/resume (phase 1)

Tuần 2:
- A3 Quiz mini-map unanswered
- A4 Hint cost transparency

Tuần 3:
- A5 Contextual onboarding
- A6 Unified continue learning CTA

Tuần 4:
- B1 Inline AI panel (MVP)
- B2 Review from wrong answers (MVP)

## 7) Kết luận

Nếu cần cải thiện mạnh trải nghiệm người học, ưu tiên nên là:

1. Giảm mất phiên và dead-end (autosave, hearts fail-safe, one-click continue)
2. Tăng tính hướng dẫn theo ngữ cảnh (mission CTA, inline AI, onboarding theo màn)
3. Tăng cảm giác tiến bộ có ý nghĩa (review sau sai, thưởng theo mastery)

Ba nhóm này tạo tác động trực tiếp nhất lên completion, retention và mức hài lòng của người học.
