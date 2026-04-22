# Kế Hoạch Triển Khai AI Teacher 3D (Kiểu Google Meet) Cho Lưu Niên Sử Kí

Ngày lập kế hoạch: 2026-04-17  
Trạng thái: Draft để triển khai

## 1) Mục tiêu sản phẩm

- Xây dựng phòng học 3D realtime kiểu Google Meet cho lớp học di sản.
- AI tham gia như một "giáo viên" có thể nghe, nói, trả lời theo ngữ cảnh lớp học.
- Dùng DeepSeek đang có sẵn trong hệ thống làm LLM chính.
- Bổ sung transcript, tóm tắt buổi học, và dữ liệu phân tích học tập.

## 2) Phạm vi MVP

- Có phòng học live với audio/video/chat và điều khiển host cơ bản.
- AI Teacher giao tiếp giọng nói 2 chiều realtime.
- Chế độ sư phạm: `hint-first` mặc định và `direct-answer` có kiểm soát.
- Transcript theo speaker + lưu log phiên học.
- Gắn nguồn tư liệu di sản (RAG) để AI trả lời có căn cứ.

Ngoài MVP (phase sau):
- Breakout rooms nâng cao.
- Avatar/gesture nâng cao.
- Chấm điểm nói tự động theo rubric.

## 3) Hiện trạng codebase liên quan

- API backend chạy từ `backend.main:app` theo `docker-compose.yml`.
- DeepSeek đã có sẵn:
1. Config: `backend/config.py` (`deepseek_api_key`, `deepseek_base_url`, `deepseek_model`).
2. Hàm gọi sync/stream: `backend/main.py` (`_call_deepseek_chat`, `_call_deepseek_chat_stream`).
3. Endpoint tutor stream SSE: `backend/main.py` (`/api/v1/ai/tutor/stream`).
- Frontend đã có stack 3D web: `@react-three/fiber`, `@react-three/drei`, `three` trong `frontend/package.json`.

## 4) Kiến trúc đề xuất

- Realtime layer: LiveKit (room, audio/video, data channel, track events).
- AI layer:
1. STT service (stream audio -> text).
2. Orchestrator service (state hội thoại, turn-taking, policy).
3. DeepSeek inference (dùng hàm/endpoint đang có).
4. TTS service (text -> audio stream).
- LMS layer:
1. Quản lý lớp, quyền host/co-host, lịch sử phiên học.
2. RAG di sản + citation.
3. Lưu transcript, summary, action items.

## 5) Timeline theo phase (10 tuần)

| Phase | Thời lượng | Mục tiêu chính |
|---|---:|---|
| Phase 0 | 3 ngày | Chốt yêu cầu, KPI, kiến trúc, rủi ro |
| Phase 1 | Tuần 1-2 | Nền tảng LiveKit + phiên lớp học |
| Phase 2 | Tuần 2-3 | UI/UX phòng học 3D kiểu Meet |
| Phase 3 | Tuần 3-5 | AI Teacher realtime (voice loop) |
| Phase 4 | Tuần 5-6 | Logic sư phạm + di sản hóa nội dung |
| Phase 5 | Tuần 6-7 | Transcript, summary, analytics |
| Phase 6 | Tuần 8 | Bảo mật, độ ổn định, cost guardrails |
| Phase 7 | Tuần 9-10 | Pilot thực tế, chỉnh sửa, rollout |

## 6) Task chi tiết theo phase

### Phase 0: Discovery, KPI, Architecture

- [ ] P0-T01 Chốt user flow chuẩn: tạo lớp live, vào phòng, AI bật/tắt, kết thúc buổi.
- [ ] P0-T02 Định nghĩa KPI: join success, latency, thời lượng nói của AI, retention lớp.
- [ ] P0-T03 Chốt role matrix: host, teacher, student, AI-teacher.
- [ ] P0-T04 Chốt kiến trúc triển khai LiveKit (Cloud hoặc self-host).
- [ ] P0-T05 Chốt lựa chọn STT/TTS cho tiếng Việt và tiêu chí chất lượng.
- [ ] P0-T06 Chốt chính sách an toàn nội dung và quyền riêng tư transcript.
- [ ] P0-T07 Lập bảng rủi ro và phương án fallback khi AI lỗi.

Deliverable:
- Tài liệu kiến trúc 1 trang.
- Danh sách KPI + target baseline.
- Checklist bảo mật dữ liệu giọng nói.

Definition of Done:
- Team thống nhất tech choices, KPI, và acceptance test cho MVP.

### Phase 1: Nền tảng Live Session + LiveKit

- [x] P1-T01 Tạo service phát hành token LiveKit theo user hiện có của LMS.
- [x] P1-T02 Thiết kế schema DB cho `live_sessions`, `live_participants`, `live_events`.
- [x] P1-T03 Tạo API: tạo phiên, join phiên, end phiên, lấy lịch sử phiên.
- [x] P1-T04 Tạo API phân quyền host/co-host/mute-all/remove-participant.
- [x] P1-T05 Đồng bộ trạng thái lớp học với module classroom hiện có.
- [x] P1-T06 Tạo webhook receiver cho sự kiện room (join/leave/disconnect).
- [x] P1-T07 Tạo retry/idempotency cho các thao tác tạo room và close room.
- [x] P1-T08 Bổ sung env/config cho LiveKit vào backend config và deploy files.

Deliverable:
- Backend API đầy đủ cho vòng đời phiên live.
- DB migration + audit event cơ bản.

Definition of Done:
- Có thể mở phòng và mời 20-50 user test vào/ra ổn định.

### Phase 2: Frontend phòng học 3D kiểu Meet

- [x] P2-T01 Tạo route mới `frontend/src/app/live/[sessionId]/page.jsx`.
- [x] P2-T02 Tích hợp SDK LiveKit client vào web app.
- [x] P2-T03 Xây layout kiểu Meet: grid video, khung chat, participant list, control bar.
- [x] P2-T04 Bổ sung lớp 3D scene song song (không chặn call controls).
- [x] P2-T05 Thêm tính năng raise hand, pin speaker, mute/unmute, cam on/off.
- [x] P2-T06 Thêm host panel: mute all, remove, lock room, bật/tắt AI.
- [x] P2-T07 Thêm trạng thái mạng/chất lượng cuộc gọi và auto-reconnect.
- [x] P2-T08 Tối ưu mobile web cho hành vi join nhanh và reconnect nhanh.

Deliverable:
- Màn hình phòng live 3D dùng được end-to-end.

Definition of Done:
- 2 trình duyệt khác nhau gọi ổn định >=30 phút, không crash UI.

### Phase 3: AI Teacher realtime (voice in/out)

- [x] P3-T01 Tạo `services/ai_teacher_agent/` (worker realtime độc lập).
- [x] P3-T02 Agent join room như participant "AI Teacher".
- [x] P3-T03 Kết nối audio inbound room -> STT streaming.
- [x] P3-T04 Nối text hội thoại -> DeepSeek (tận dụng hàm gọi hiện có).
- [x] P3-T05 Nối DeepSeek output -> TTS streaming -> publish audio track.
- [x] P3-T06 Xây cơ chế turn-taking: AI không nói đè khi học viên đang nói.
- [x] P3-T07 Xây cơ chế wake phrase và push-to-ask cho AI.
- [x] P3-T08 Thêm timeout, cancel speech, barge-in handling.
- [x] P3-T09 Đẩy transcript chunk realtime qua data channel đến UI.
- [x] P3-T10 Fallback mode: nếu voice fail thì trả lời text trong chat.

Deliverable:
- Agent service chạy độc lập, join room, nói chuyện 2 chiều realtime.

Definition of Done:
- Vòng `user speech -> AI speech` hoạt động ổn định với p95 round-trip <= 2.5s.

### Phase 4: Logic sư phạm và di sản

- [x] P4-T01 Áp dụng policy `hint-first` mặc định cho mọi câu trả lời AI.
- [x] P4-T02 Áp dụng `direct-answer` có kiểm soát theo rule và role host.
- [x] P4-T03 Tạo lesson script theo cụm tri thức di sản (đỉnh, họa tiết, chủ đề).
- [x] P4-T04 Tạo checkpoint tự động mỗi 5-8 phút để kiểm tra hiểu bài.
- [x] P4-T05 Kết nối RAG di sản hiện có để AI bám nguồn.
- [ ] P4-T06 Thêm citation tagging trong lời đáp và summary cuối buổi.
- [ ] P4-T07 Tạo rubric phản hồi cho học viên (mức hiểu, lỗ hổng kiến thức).
- [ ] P4-T08 Cấu hình "AI persona giáo viên di sản" cho từng cấp học.

Deliverable:
- AI Teacher trả lời đúng vai trò giáo viên, có dẫn nguồn di sản.

Definition of Done:
- 20 kịch bản học thử đạt quality gate do team nội dung đánh giá.

### Phase 5: Transcript, summary, analytics

- [ ] P5-T01 Tạo schema `session_transcripts`, `session_summaries`, `session_actions`.
- [ ] P5-T02 Lưu transcript theo speaker + timestamp + confidence.
- [ ] P5-T03 Sinh summary cuối buổi: chủ điểm, câu hỏi nổi bật, bài tập gợi ý.
- [ ] P5-T04 Sinh attendance + engagement metrics từ sự kiện room.
- [ ] P5-T05 Tạo teacher dashboard xem lại transcript và insight.
- [ ] P5-T06 Tạo API export transcript (JSON/CSV) cho vận hành nội bộ.
- [ ] P5-T07 Thêm cảnh báo "đứt mạch học" cho học viên ít tương tác.

Deliverable:
- Báo cáo sau buổi học dùng được cho giáo viên và quản trị.

Definition of Done:
- 100% session pilot có transcript và summary sinh tự động.

### Phase 6: Reliability, security, compliance, cost

- [ ] P6-T01 Thêm rate limit cho endpoint live và AI endpoints.
- [ ] P6-T02 Thêm guardrails prompt + content safety cho voice path.
- [ ] P6-T03 Mã hóa dữ liệu nhạy cảm trong storage và logs.
- [ ] P6-T04 Thiết kế retention policy cho audio/transcript theo quyền riêng tư.
- [ ] P6-T05 Bật observability: latency, error budget, drop rate, token usage.
- [ ] P6-T06 Thiết lập circuit breaker khi STT/TTS/LLM provider lỗi.
- [ ] P6-T07 Áp cost ceiling theo lớp/phiên để tránh bùng chi phí.

Deliverable:
- SLO/SLA nội bộ cho live class + AI assistant.

Definition of Done:
- Pass security checklist và test tải cơ bản trước pilot mở rộng.

### Phase 7: Pilot, rollout, vận hành

- [ ] P7-T01 Chọn 2-3 lớp pilot (quy mô nhỏ) và lịch chạy thật.
- [ ] P7-T02 Thu feedback giáo viên/học viên theo form chuẩn.
- [ ] P7-T03 Tinh chỉnh prompt/policy theo feedback thực tế.
- [ ] P7-T04 A/B test mức can thiệp AI (ít/chuẩn/nhiều).
- [ ] P7-T05 Viết runbook vận hành + incident playbook.
- [ ] P7-T06 Đào tạo team nội dung sử dụng AI Teacher mode.
- [ ] P7-T07 Chốt tiêu chí go-live production.

Deliverable:
- Báo cáo pilot + quyết định rollout.

Definition of Done:
- KPI pilot đạt ngưỡng đã chốt từ Phase 0.

## 7) Kế hoạch kiểm thử

- Unit test: Token issuance, quyền room, policy mode `hint-first/direct-answer`.
- Integration test: Tạo room -> join -> AI join -> hội thoại -> transcript -> end session.
- E2E test: 1 host + 3 learners + AI trong 30 phút.
- Non-functional test: Soak test 2 giờ, kiểm tra memory leak, reconnect, packet loss.

## 8) KPI và ngưỡng nghiệm thu MVP

- Join success rate: >= 98%.
- Median time to join: <= 5 giây.
- p95 AI response round-trip (voice): <= 2.5 giây.
- Transcript completeness: >= 95% lượt phát biểu có bản ghi.
- Session crash rate: <= 1%.
- Teacher satisfaction (pilot): >= 4.2/5.

## 9) Phân công vai trò gợi ý

- Backend engineer: API live session, permissions, transcript storage, analytics APIs.
- Frontend engineer: Room UI kiểu Meet, 3D scene integration, host controls.
- AI engineer: Agent orchestration, STT/TTS routing, DeepSeek policy prompts.
- DevOps engineer: LiveKit deploy, secrets, monitoring, autoscaling, cost guard.
- QA: E2E call matrix, network resilience, regression checklist.

## 10) Danh sách việc triển khai ngay tuần đầu

- [x] W1-01 Tạo skeleton module `backend/services/live_sessions.py`.
- [x] W1-02 Tạo migration cho `live_sessions` và `live_participants`.
- [x] W1-03 Tạo endpoint cấp token LiveKit.
- [x] W1-04 Tạo trang `frontend/src/app/live/[sessionId]/page.jsx` bản tối giản.
- [x] W1-05 Join được room, thấy participant list, bật/tắt mic/cam.
- [x] W1-06 Tạo service `services/ai_teacher_agent/` với loop text giả lập.
- [x] W1-07 Bổ sung API `leave` để cập nhật participant lifecycle (`left_at`) chuẩn.
- [x] W1-08 Tích hợp AI Teacher trực tiếp trong live room (hint-first/direct-answer, fallback mock).
- [x] W1-09 Tích hợp luồng tạo buổi live + vào phòng từ trang Admin.

---

Ghi chú kỹ thuật quan trọng:
- Ưu tiên reuse DeepSeek path đã có trong `backend/main.py`, không tạo luồng LLM tách rời ngay từ đầu.
- AI phải luôn có fallback text mode để không làm gián đoạn buổi học khi voice pipeline lỗi.
- Dùng feature flag cho AI Teacher để rollout an toàn theo lớp.
