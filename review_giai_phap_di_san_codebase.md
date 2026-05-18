# Review nội dung mục 3 theo codebase thực tế (bao gồm web + backend)

## 1) Phạm vi đã đối chiếu

- Web frontend: route và UI trong `frontend/src/app`, các component 3D/học tập/chia sẻ.
- Backend API: endpoint và schema trong `backend/main.py`, `backend/schemas.py`.
- Tài liệu mô tả dự án: `README.md`.

## 2) Các điểm chưa sát codebase hiện tại

### A. Phạm vi sản phẩm đang bị viết quá rộng

- Nội dung hiện tại mô tả một hệ thống “Kho dữ liệu Nghiên cứu và Bảo tồn Di sản Văn hóa” cho nhiều loại di sản.
- Thực tế codebase đang tập trung rất rõ vào **LMS gamified cho Cửu Đỉnh** (9 đỉnh triều Nguyễn), không phải kho di sản tổng quát.
- Bằng chứng:
  - `README.md:3`
  - `frontend/src/app/page.jsx:33-42`
  - `frontend/src/app/cuu-dinh/page.jsx`

### B. “Bảo tàng ảo” nên đổi thành “trình xem 3D tương tác”

- Phần mô tả “bảo tàng ảo” theo nghĩa đầy đủ (trưng bày đa không gian, đa bộ sưu tập) chưa khớp với triển khai thực tế.
- Thực tế hiện có:
  - Trình xem 3D WebGL + click mesh + liên kết bài học/quiz.
  - Không có module “bảo tàng ảo” độc lập với luồng học.
- Bằng chứng:
  - `frontend/src/components/UrnViewer.js:12-20`
  - `frontend/src/components/UrnViewer.js:55-62`
  - `frontend/src/app/urns/[urnSlug]/page.jsx`

### C. “Bản đồ số” và “thực tế ảo (VR)” chưa có trong codebase

- Nội dung hiện tại khẳng định có bản đồ số và VR.
- Đối chiếu code web/backend không thấy module map/VR.
- Có 3D Web viewer (React Three Fiber), nhưng chưa có WebXR/VR tour.

### D. QR code đang dùng cho chia sẻ hồ sơ, chưa phải QR trong booklet/tài liệu học

- Nội dung hiện tại nói QR được tích hợp vào tài liệu học tập/booklet.
- Thực tế QR hiện xuất hiện ở trang hồ sơ công khai để chia sẻ link.
- Bằng chứng:
  - `frontend/src/app/u/[userId]/page.jsx:6`
  - `frontend/src/app/u/[userId]/page.jsx:464-477`

### E. Fanpage/Facebook/TikTok/Livestream/Hashtag chưa có tích hợp

- Nội dung hiện tại mô tả fanpage là giải pháp đã có.
- Đối chiếu route web và API không có module tích hợp fanpage hoặc API social network ngoài.
- Hệ thống hiện có social nội bộ: friends/follow/share activity trong chính nền tảng.
- Bằng chứng:
  - `backend/main.py:17002`
  - `backend/main.py:17055`
  - `backend/main.py:17167`
  - `backend/schemas.py:3091-3112`

### F. “Học sinh đóng góp bài viết/clip/tranh/infographic” chưa có workflow riêng

- Hiện chưa thấy chức năng nộp sản phẩm học tập dạng user-generated content theo đúng mô tả.
- Hệ thống chia sẻ hiện tại chủ yếu là chia sẻ thành tích/huy hiệu/streak/chứng nhận.
- Bằng chứng:
  - `backend/schemas.py:3094-3097`
  - `frontend/src/app/achievements/page.jsx:30-36`
  - `frontend/src/app/share/[shareId]/page.jsx`

### G. Cần chỉnh lại câu chữ “đã triển khai” vs “định hướng”

- Một số đoạn đang viết theo kiểu đã vận hành đầy đủ (fanpage, booklet QR học liệu, VR, bản đồ số), nhưng codebase chưa có.
- Nên tách:
  - **Đã có**: 3D, bài học, quiz, exam, lớp học, AI, bảng xếp hạng, chia sẻ nội bộ.
  - **Định hướng**: fanpage, VR tour, bản đồ số, đóng góp học sinh dạng nội dung số.

## 3) Những điểm ổn và sát codebase (nên giữ)

- 3D xoay/khám phá họa tiết là trục chính.
- Liên kết giữa khám phá 3D -> bài học -> quiz -> đánh giá.
- Tăng hứng thú học tập bằng gamification (XP, badge, leaderboard, streak).
- Có hỗ trợ quản lý lớp học và giao nhiệm vụ cho giáo viên (trong admin).
- Bằng chứng:
  - `frontend/src/app/explore/page.jsx`
  - `frontend/src/app/motif/[motifId]/page.jsx`
  - `frontend/src/app/motif/[motifId]/quiz/page.jsx`
  - `frontend/src/app/urns/[urnSlug]/exam/page.jsx`
  - `frontend/src/app/leaderboard/page.jsx`
  - `frontend/src/app/admin/page.jsx:1485-1693`
  - `backend/main.py:8551`
  - `backend/main.py:8641`
  - `backend/main.py:9293`
  - `backend/main.py:9394`

## 4) Bản viết lại đề xuất (sát thực tế hệ thống hiện tại)

### 3. Giải pháp tích hợp giáo dục di sản và công nghệ số trong dạy học Lịch sử

Nền tảng hiện tại được triển khai theo mô hình LMS gamified, tập trung vào di sản Cửu Đỉnh triều Nguyễn. Trên web, học sinh có thể khám phá 3D các đỉnh đồng, tương tác trực tiếp với từng họa tiết, sau đó chuyển sang bài học chi tiết và phần trắc nghiệm theo từng nội dung.

Hệ thống học liệu số đang vận hành theo chuỗi: khám phá - học - kiểm tra - đánh giá. Mỗi họa tiết có nội dung mô tả lịch sử, ý nghĩa biểu tượng và tư liệu đa phương tiện (hình ảnh, audio, video tùy dữ liệu). Sau khi hoàn thành bài học, học sinh làm quiz; khi đạt điều kiện, có thể làm bài kiểm tra theo từng đỉnh và nhận chứng chỉ xác thực.

Về tổ chức dạy học, hệ thống đã có chức năng lớp học cho giáo viên: tạo lớp, thêm học viên, giao quest và theo dõi tiến độ hoàn thành. Điều này giúp tích hợp dạy học trên lớp với môi trường số theo hướng có kiểm soát tiến trình và kết quả.

Bên cạnh đó, các cơ chế gamification như XP, huy hiệu, streak, bảng xếp hạng và chia sẻ thành tích trong hệ thống tạo động lực học tập liên tục. Tính năng bạn bè và feed hoạt động hỗ trợ tương tác học tập nội bộ giữa người học.

Ngoài phần học tập cốt lõi, hệ thống còn tích hợp AI tutor/AI hỗ trợ học để giải thích kiến thức, gợi ý ôn tập và cá nhân hóa trải nghiệm theo ngữ cảnh bài học.

Lưu ý phạm vi hiện tại: nền tảng **chưa triển khai** fanpage tích hợp mạng xã hội bên ngoài, bản đồ số di sản, tour VR, hoặc quy trình học sinh nộp sản phẩm số (bài viết/clip/infographic) như một module riêng. Các nội dung này nên được trình bày ở mục định hướng phát triển tiếp theo.

