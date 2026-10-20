/**
 * Curated Historical Trails & Inquiries Data for STTTNNĐ (Lưu Niên — Đại Nội Huế).
 * Ref: LUU_NIEN_STTTNND_DAI_NOI_MASTER_SPEC_V2_1_INTEGRATED.md (§20)
 *
 * 4 Curated Walking / Virtual Historical Inquiry Trails:
 * 1. Trục Dũng Đạo & Quyền Lực (Ngọ Môn -> Sân Đại Triều -> Điện Thái Hòa -> Điện Cần Chánh)
 * 2. Không Gian Ký Ức & Tưởng Niệm (Thế Tổ Miếu -> Hiển Lâm Các -> Hưng Miếu -> Triệu Miếu)
 * 3. Tử Cấm Thành — Biến Đổi & Phục Hồi (Điện Cần Chánh -> Duyệt Thị Đường -> Thái Bình Lâu -> Điện Kiến Trung)
 * 4. Đời Sống Cung Đình & Diên Thọ (Cung Diên Thọ -> Cung Trường Sanh -> Điện Phụng Tiên)
 */

import type { ImperialTrail } from "./map-types";

export const IMPERIAL_TRAILS: ImperialTrail[] = [
  {
    slug: "truc-dung-dao-quyen-luc",
    title: "Trục Dũng Đạo & Quyền Lực Hoàng Triều",
    subtitle: "Khảo sát không gian nghi lễ chính thức và trật tự thứ bậc quân quyền triều Nguyễn",
    description:
      "Tuyến khảo sát dọc theo trục Thần đạo (Dũng đạo) trung tâm Bắc - Nam. Học sinh phân tích sự chuyển dịch từ không gian công cộng sang bí mật quân quyền, giải mã cách ngôn ngữ kiến trúc và phân tầng cấp bậc khẳng định trật tự vương triều phong kiến.",
    duration_minutes: 60,
    age_group: "Học sinh THPT & Người yêu di sản",
    target_grade: "Lớp 10 - 12 (Chương trình Lịch sử GDPT 2018)",
    difficulty: "Cơ bản",
    cover_image: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
    theme_color: "amber",
    pedagogical_objectives: [
      "Xác định nguyên tắc trục đối xứng Nam - Bắc và trật tự phân tầng không gian (S1: Năng lực Không gian).",
      "Phân tích vai trò của Ngọ Môn và Điện Thái Hòa trong các đại lễ vương triều (S2: Năng lực Thời gian).",
      "Khai thác và đối chiếu quy chế đại triều từ văn bản Khâm Định Đại Nam Hội Điển Sự Lệ (S3: Năng lực Sử liệu).",
      "Rút ra kết luận về phương thức thể hiện tính chính thống và uy quyền tuyệt đối của quân vương (S4: Năng lực Lập luận).",
    ],
    stops: [
      {
        order: 1,
        monument_slug: "ngo-mon",
        monument_name_vi: "Ngọ Môn",
        monument_name_han_nom: "午門",
        title: "Trạm 1: Ngọ Môn — Cổng Trời Của Vương Triều",
        inquiry_question: "Vì sao cấu trúc 'năm cửa chín lầu' tại Ngọ Môn thể hiện rõ rệt sự phân biệt tôn ti trật tự phong kiến?",
        step_prompt:
          "Quan sát bình diện 5 cửa vào: cửa chính giữa (Ngọ Môn), hai cửa bên (Tả/Hữu Giáp Môn) và hai lối ngoài cùng (Tả/Hữu Dịch Môn). Hãy đối chiếu sử liệu về đối tượng được phép đi qua từng cửa.",
        required_sources: [
          {
            title: "Khâm Định Đại Nam Hội Điển Sự Lệ (Quyển 78 - Công Bộ)",
            citation: "Minh Mạng năm thứ 14 (1833) ban lệnh quy định kích thước 5 lối cửa và quy thức canh gác.",
            type: "chronicle",
          },
          {
            title: "Ảnh Viễn Đông Bác Cổ (EFEO) chụp lầu Ngũ Phụng năm 1920",
            citation: "Kho lưu trữ ảnh EFEO - Fonds Indochine (Hà Nội).",
            type: "archival_photo",
          },
        ],
        observation_points: [
          "Cửa giữa xây bằng đá thanh, lợp ngói hoàng lưu ly (chỉ dành riêng cho Thiên tử).",
          "Hai cửa giáp môn lợp ngói thanh lưu ly (dành cho quan viên văn võ và hoàng thân).",
          "Hai cửa dịch môn hình cánh cung khoét qua thân đài (dành cho binh lính, voi ngựa tùy tùng).",
          "Lầu Ngũ Phụng trên tầng đài với kết cấu gỗ lim 100 cột và hệ mái 'trùng thiềm điệp ốc'.",
        ],
        virtual_fieldwork: {
          overview_text:
            "Đứng trước mặt tiền Ngọ Môn hướng về Kỳ Đài, không gian mở rộng bao quát toàn bộ quảng trường trước Hoàng Thành. Cổng thành không chỉ là công trình phòng ngự mà là sân khấu chính trị nơi diễn ra lễ Ban sóc (phát lịch) và lễ Truyền lô (xướng danh tiến sĩ).",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Tọa độ trực giao Ngọ Môn trên trục trung tâm Nam - Bắc của Hoàng Thành Huế.",
          historical_clues: [
            "Tại lầu Ngũ Phụng ngày 30/8/1945, vua Bảo Đại đã đọc Chiếu thoái vị và trao ấn kiếm cho phái đoàn Chính phủ Cách mạng Lâm thời.",
            "Tên gọi 'Ngọ Môn' chỉ phương Nam theo dịch học, tượng trưng cho hướng ánh sáng và bậc minh quân hướng về phương Nam trị vì thiên hạ.",
          ],
        },
        task_prompt: "Nêu kết luận về ý nghĩa chính trị của trật tự 5 lối cửa tại Ngọ Môn và dẫn một bằng chứng từ văn bản quy định triều Nguyễn.",
        expected_evidence: "Phân biệt lối đi vua (lối giữa ngói vàng) và quan lại/binh lính (cửa bên ngói xanh hoặc vòm đá cuội).",
        u: 0.5002,
        v: 0.8354,
      },
      {
        order: 2,
        monument_slug: "san-dai-trieu-nghi",
        monument_name_vi: "Sân Đại Triều Nghi",
        monument_name_han_nom: "大朝儀丹墀",
        title: "Trạm 2: Sân Đại Triều Nghi — Trật Tự Văn Võ Bái Mạng",
        inquiry_question: "Hai tầng sân và các hàng bia phẩm trật được bố trí như thế nào để khẳng định tôn ti văn võ?",
        step_prompt:
          "Khảo sát sự chênh lệch độ cao giữa tầng sân thượng và tầng sân hạ. Đọc các ký tự khắc trên bia đá phân hạng phẩm trật quan viên (từ Chánh nhất phẩm đến Tòng cửu phẩm).",
        required_sources: [
          {
            title: "Đại Nam Thực Lục Chính Biên (Tập 2, Kỷ Đệ Nhị)",
            citation: "Ghi chép về lễ Đại triều thường kỳ vào ngày mùng 1 và rằm mỗi tháng âm lịch.",
            type: "chronicle",
          },
          {
            title: "Bản vẽ bình đồ nghi thức Đại triều (L. Cadière, BAVH 1916)",
            citation: "Tạp chí Đô thành Hiếu cổ (Bulletin des Amis du Vieux Hué).",
            type: "conservation_report",
          },
        ],
        observation_points: [
          "Bố cục Văn tả - Võ hữu: Quan văn đứng bên trái (hướng đông), Quan võ đứng bên phải (hướng tây).",
          "Tầng trên (thượng đan trì) dành cho quan đại thần tam phẩm trở lên.",
          "Tầng dưới (hạ đan trì) dành cho lục phẩm đến cửu phẩm.",
          "Hồ Thái Dịch và cầu Trung Đạo đóng vai trò ranh giới phong thủy tụ thủy tích tụ sinh khí.",
        ],
        virtual_fieldwork: {
          overview_text:
            "Khoảng sân rộng lớn lát đá Thanh Phước hướng lên thềm rồng Điện Thái Hòa. Vào ngày đại lễ, hàng trăm đại thần mặc triều phục thêu tứ linh cùng quỳ lạy 'tam quỵ cửu khấu' trước ngai vàng.",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Sân Đại Triều Nghi chia đôi bởi Dũng Đạo và cầu Trung Đạo bắc qua hồ Thái Dịch.",
          historical_clues: [
            "Hai bên thành bậc thềm là bốn con rồng đá chạm khắc thời Gia Long biểu trưng cho thiên quyền.",
            "Các bia đá nhỏ (phẩm thạch) đóng vai trò định vị chỗ đứng chính xác tuyệt đối, tránh sai sót trong nghi lễ ngoại giao.",
          ],
        },
        task_prompt: "Chỉ ra nguyên lý 'Văn tả - Võ hữu' và giải thích vì sao trật tự không gian này củng cố tính tôn nghiêm của bộ máy quan liêu phong kiến.",
        expected_evidence: "Vị trí bia phẩm trật hai bên sân và sự phân biệt quan chức cấp cao đứng sân trên sát điện rồng.",
        u: 0.5002,
        v: 0.7085,
      },
      {
        order: 3,
        monument_slug: "dien-thai-hoa",
        monument_name_vi: "Điện Thái Hòa",
        monument_name_han_nom: "太和殿",
        title: "Trạm 3: Điện Thái Hòa — Đỉnh Cao Vương Quyền & Thống Nhất Đất Nước",
        inquiry_question: "Kiến trúc 'trùng thiềm điệp ốc' và trang trí 9 con rồng ngai vàng biểu đạt khát vọng gì của triều đại?",
        step_prompt:
          "Đi sâu vào nội thất chính điện, quan sát vị trí ngai vàng đặt dưới bửu tán gấm và các câu thơ chạm khảm theo lối 'nhất thi nhất họa' trên các liên ba bảng ngạch.",
        required_sources: [
          {
            title: "Thơ văn chạm khắc trên kiến trúc cung đình Huế (Hồ sơ Di sản Tư liệu Ký ức Thế giới UNESCO)",
            citation: "Thơ ngự chế các vua Minh Mạng, Thiệu Trị, Tự Đức ca ngợi sự thái bình thịnh trị và nền độc lập dân tộc.",
            type: "epigraphy",
          },
          {
            title: "Hồ sơ trùng tu tổng thể Điện Thái Hòa (Trung tâm BTDT Cố đô Huế, 2021-2025)",
            citation: "Báo cáo bóc tách hạ giải kết cấu gỗ lim và phục hồi lớp ngói hoàng lưu ly dát vàng.",
            type: "conservation_report",
          },
        ],
        observation_points: [
          "Mô hình 'nhà kép' mái nối tiếp mái bằng máng xối đồng tạo không gian hội họp rộng lớn mà không tối tăm.",
          "Hệ thống 80 cột gỗ lim thếp vàng họa tiết rồng vờn mây (long vân khánh hội).",
          "Ngai vàng biểu tượng quyền uy tối thượng được chế tác từ thời Gia Long (1802).",
          "Con số 9 và số 5 lặp lại trong số bậc thềm, gian nhà và hoa văn rồng (Cửu Ngũ chí tôn).",
        ],
        virtual_fieldwork: {
          overview_text:
            "Điện Thái Hòa là trái tim biểu tượng của cả vương quốc Đại Nam. Đây là nơi diễn ra các nghi lễ trọng đại nhất: Lễ Đăng quang, Lễ Vạn thọ (sinh nhật vua), Lễ Quốc khánh và đón tiếp các đoàn sứ thần ngoại bang.",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Tòa chính điện nguy nga bậc nhất Cố đô, biểu trưng cho sự hòa hợp và phồn vinh của quốc gia.",
          historical_clues: [
            "Chữ 'Thái Hòa' lấy gốc từ Kinh Dịch, mang nghĩa hòa khí tột bậc giữa Trời và Đất tạo nên muôn vật sinh sôi thuận hòa.",
            "Điện hoàn thành đại trùng tu năm 2025 sau đợt hạ giải bảo tồn khoa học kéo dài nhiều năm.",
          ],
        },
        task_prompt: "Phân tích vì sao con số 9 và hình tượng rồng 5 móng chỉ xuất hiện ở Điện Thái Hòa mà không có ở các miếu đền khác.",
        expected_evidence: "Quy chuẩn biểu tượng hoàng đế (Cửu ngũ chí tôn) và tính độc quyền của vương quyền trung ương tập quyền.",
        u: 0.5002,
        v: 0.6385,
      },
      {
        order: 4,
        monument_slug: "dien-can-chanh",
        monument_name_vi: "Điện Cần Chánh",
        monument_name_han_nom: "勤政殿",
        title: "Trạm 4: Điện Cần Chánh — Nơi Quân Vương Trị Nước Thường Triều",
        inquiry_question: "Sự khác biệt căn bản về chức năng và tính chất không gian giữa Điện Thái Hòa và Điện Cần Chánh là gì?",
        step_prompt:
          "Vượt qua Đại Cung Môn để bước vào Tử Cấm Thành. So sánh quy mô, khoảng cách tiếp cận và đối tượng tham gia giữa lễ Đại triều và các buổi Thường triều xét xử chính vụ hàng ngày.",
        required_sources: [
          {
            title: "Đại Nam Hội Điển Sự Lệ (Quyển Nội các - Cơ mật viện)",
            citation: "Quy định giờ vào chầu lúc rạng sáng (canh năm) và sổ sách tấu trình của lục bộ.",
            type: "chronicle",
          },
          {
            title: "Ảnh chụp nội thất Điện Cần Chánh trước năm 1947",
            citation: "Bộ sưu tập ảnh tư liệu Viện Viễn Đông Bác Cổ (EFEO).",
            type: "archival_photo",
          },
        ],
        observation_points: [
          "Vị trí ngay sau Đại Cung Môn, mở đầu chuỗi công trình của Tử Cấm Thành.",
          "Nơi diễn ra các buổi thiết triều hàng ngày vào các ngày 5, 10, 20, 25 mỗi tháng.",
          "Di tích bị phá hủy hoàn toàn trong chiến tranh năm 1947, hiện đang được phục dựng nghiên cứu khảo cổ học.",
          "Tên gọi 'Cần Chánh' nhắc nhở nhà vua phải luôn cần mẫn, siêng năng chăm lo quốc sự.",
        ],
        virtual_fieldwork: {
          overview_text:
            "Không gian nền móng đá xanh của Điện Cần Chánh ngày nay nhắc nhở về những vết thương chiến tranh và nỗ lực phục hồi di sản của thế hệ mai sau. Tại đây vua cùng Cơ Mật Viện và Nội Các phê duyệt các bản Châu bản triều Nguyễn.",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Di tích nền móng Điện Cần Chánh nhìn từ không ảnh trực giao Tử Cấm Thành.",
          historical_clues: [
            "Các cột gỗ lim chạm lộng tinh xảo từng được đánh giá là đỉnh cao mỹ thuật đồ gỗ thế kỷ 19.",
            "Nơi đây cũng là địa điểm đãi tiệc các quan chức cao cấp nhân dịp khánh tiết.",
          ],
        },
        task_prompt: "Sử dụng mô hình M-E-E để kết luận: 'Trục Dũng Đạo đã kiến tạo nên một lộ trình tâm lý quyền lực như thế nào đối với thần dân khi tiến vào bái yết thiên tử?'",
        expected_evidence: "Sự chuyển tiếp từ cửa thành hoành tráng (Ngọ Môn) qua sân khấu lễ nghi tráng lệ (Điện Thái Hòa) đến trung tâm điều hành bí mật (Điện Cần Chánh).",
        u: 0.5002,
        v: 0.5312,
      },
    ],
  },
  {
    slug: "khong-gian-ky-uc-tuong-niem",
    title: "Không Gian Ký Ức & Tưởng Niệm Tổ Tiên",
    subtitle: "Khám phá đạo lý 'Uống nước nhớ nguồn' và trật tự tông miếu triều Nguyễn",
    description:
      "Tuyến khảo sát khu vực phía Tây Nam Hoàng Thành — nơi tọa lạc các công trình tưởng niệm thiêng liêng nhất của vương triều. Học sinh tìm hiểu quy chế thờ tự tổ tiên, vị trí Đỉnh đồng và kiến trúc tháp chuông Hiển Lâm Các.",
    duration_minutes: 50,
    age_group: "Học sinh THPT",
    target_grade: "Lớp 10 - 11",
    difficulty: "Trung cấp",
    cover_image: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
    theme_color: "emerald",
    pedagogical_objectives: [
      "Nhận diện vị trí phong thủy bên tả bên hữu của khu miếu thờ theo nguyên tắc 'Tả Chiêu Hữu Mục' (S1).",
      "Xác định thứ tự các vị vua Nguyễn được phối thờ qua các thời kỳ lịch sử (S2).",
      "Đọc hiểu văn tự chữ Hán khắc trên Cửu Đỉnh và bài vị Thế Tổ Miếu (S3).",
      "Đánh giá giá trị nhân văn và tinh thần tri ân cội nguồn trong văn hóa Việt Nam (S4).",
    ],
    stops: [
      {
        order: 1,
        monument_slug: "the-to-mieu",
        monument_name_vi: "Thế Tổ Miếu",
        monument_name_han_nom: "世祖廟",
        title: "Trạm 1: Thế Tổ Miếu — Nơi Thờ Phụng Các Vị Hoàng Đế",
        inquiry_question: "Vì sao án thờ vua Gia Long luôn ngự tại gian chính giữa và thứ tự các gian thờ phản ánh điều gì?",
        step_prompt:
          "Quan sát bố cục 9 gian 2 chái của tòa miếu chính. Ghi chép vị trí bài vị của các vua qua các thời kỳ, đặc biệt là sự bổ sung bài vị các vua yêu nước Hàm Nghi, Đồng Khánh, Thành Thái, Duy Tân.",
        required_sources: [
          {
            title: "Khâm Định Đại Nam Hội Điển Sự Lệ (Tập Lễ Bộ - Miếu chế)",
            citation: "Quy định nghiêm ngặt về kích thước khám thờ, áo mũ và lễ phẩm cúng tế tứ thời.",
            type: "chronicle",
          },
          {
            title: "Văn bản Hội đồng Hoàng Tộc năm 1959",
            citation: "Biên bản rước bài vị ba vị vua yêu nước Hàm Nghi, Thành Thái, Duy Tân vào phối thờ.",
            type: "chronicle",
          },
        ],
        observation_points: [
          "Gian chính giữa luôn dành cho Thế Tổ Cao Hoàng Đế (vua Gia Long) — người sáng lập vương triều.",
          "Nguyên tắc Tả Chiêu Hữu Mục: Đời chẵn bên tả, đời lẻ bên hữu.",
          "Hệ thống bao lam, hoành phi câu đối sơn son thếp vàng cổ kính.",
        ],
        virtual_fieldwork: {
          overview_text:
            "Thế Tổ Miếu là miếu thờ lớn nhất trong Hoàng Thành, được xây dựng năm 1821 dưới thời Minh Mạng. Đây là không gian linh thiêng chỉ dành cho hoàng tộc và các quan đại thần tham gia tế lễ.",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Khuôn viên Thế Miếu tĩnh mịch với cây tùng bách ngàn năm tuổi.",
          historical_clues: [
            "Vua Dục Đức, Hiệp Hòa và Bảo Đại không có án thờ chính thức tại đây do các biến cố lịch sử.",
            "Lễ Tế Miếu được tổ chức đều đặn mỗi năm 5 lần theo lịch xuân, hạ, thu, đông và chạp.",
          ],
        },
        task_prompt: "Giải thích nguyên tắc sắp đặt bài vị tại Thế Tổ Miếu và phân tích ý nghĩa của việc đưa các vị vua kháng Pháp vào phối thờ năm 1959.",
        expected_evidence: "Vị trí gian giữa của vua Gia Long và sự điều chỉnh lịch sử thể hiện sự kính trọng tinh thần yêu nước.",
        u: 0.3845,
        v: 0.7420,
      },
      {
        order: 2,
        monument_slug: "hien-lam-cac",
        monument_name_vi: "Hiển Lâm Các",
        monument_name_han_nom: "顯臨閣",
        title: "Trạm 2: Hiển Lâm Các — Đài Tưởng Niệm Công Thần Hoàng Gia",
        inquiry_question: "Vì sao triều đình quy định không có bất kỳ công trình nào trong Đại Nội được xây cao hơn Hiển Lâm Các?",
        step_prompt:
          "Chiêm ngưỡng kết cấu 3 tầng bằng gỗ lim cao hơn 17 mét đứng sừng sững trước sân Thế Miếu. Quan sát 9 chiếc đỉnh đồng sừng sững xếp hàng ngang dưới chân gác.",
        required_sources: [
          {
            title: "Đại Nam Thực Lục Chính Biên (Đệ Nhị Kỷ, Quyển 12)",
            citation: "Chỉ dụ của vua Minh Mạng về việc tôn vinh những danh thần tận tụy phò tá khai quốc.",
            type: "chronicle",
          },
          {
            title: "Hồ sơ di sản ký ức Cửu Đỉnh Huế (UNESCO Memory of the World)",
            citation: "Hồ sơ bản dập 153 mảng phù điêu cảnh sắc giang sơn đất nước Việt Nam trên thân Cửu Đỉnh.",
            type: "epigraphy",
          },
        ],
        observation_points: [
          "Tầng 1 là nơi đặt biển ngạch kỷ công, tầng 2 và 3 là nơi ngắm cảnh và treo chuông khánh tế lễ.",
          "Hai dãy nhà Tả Vu - Hữu Vu hai bên thờ các khai quốc công thần văn võ (như Nguyễn Văn Trương, Võ Tánh, Lê Văn Duyệt...).",
          "Cửu Đỉnh đúc năm 1835-1837 đặt thẳng hàng trước thềm gác.",
        ],
        virtual_fieldwork: {
          overview_text:
            "Hiển Lâm Các là đài tưởng niệm các bậc tiền nhân có công khai sáng và bảo vệ bờ cõi. Công trình vươn cao lên bầu trời như một cầu nối giữa trần thế và thế giới tiền nhân thiêng liêng.",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Hiển Lâm Các cùng Cửu Đỉnh tạo thành quần thể di sản ký ức vô giá.",
          historical_clues: [
            "Mỗi đỉnh trên Cửu Đỉnh tương ứng với thụy hiệu của một vị hoàng đế, đỉnh giữa (Cao Đỉnh) ứng với vua Gia Long.",
            "Trên Cửu Đỉnh có hình tượng Biển Đông, Biển Nam thể hiện chủ quyền biển đảo toàn vẹn từ thế kỷ 19.",
          ],
        },
        task_prompt: "Chỉ ra mối liên hệ không gian giữa Hiển Lâm Các, Cửu Đỉnh và Thế Miếu. Chúng cùng tạo nên thông điệp biểu tượng gì?",
        expected_evidence: "Sự kết hợp giữa tưởng niệm tổ tiên (Thế Miếu), ghi công khai quốc (Hiển Lâm Các) và khẳng định chủ quyền lãnh thổ (Cửu Đỉnh).",
        u: 0.3845,
        v: 0.8042,
      },
      {
        order: 3,
        monument_slug: "hung-to-mieu",
        monument_name_vi: "Hưng Miếu",
        monument_name_han_nom: "興廟",
        title: "Trạm 3: Hưng Miếu — Nơi Tôn Kính Thân Phụ Vua Gia Long",
        inquiry_question: "Hưng Miếu thờ ai và vì sao ngôi miếu này được xây dựng độc lập bên cạnh Thế Miếu?",
        step_prompt:
          "Đi bộ về phía Bắc Thế Miếu, bước vào khuôn viên tường hoa bao bọc Hưng Miếu. Khảo sát kiến trúc tinh xảo của ngôi miếu thờ Thế tử Nguyễn Phúc Luân (thân phụ vua Gia Long).",
        required_sources: [
          {
            title: "Đại Nam Liệt Truyện Tiền Biên",
            citation: "Truyện kể về đức tính nhân từ và cái chết bi tráng của Định Thiền Vương Nguyễn Phúc Luân thời Chúa Nguyễn.",
            type: "chronicle",
          },
        ],
        observation_points: [
          "Kiến trúc nhà kép bằng gỗ thếp bạc tinh xảo.",
          "Hoa văn gốm sứ trang trí trên bờ nóc và hệ thống hàng rào gạch hoa trang nhã.",
          "Miếu từng bị cháy năm 1947 và được bà Đoan Huy Hoàng Thái Hậu (Đức Từ Cung) công đức xây dựng lại năm 1951.",
        ],
        virtual_fieldwork: {
          overview_text:
            "Hưng Miếu là minh chứng xúc động về lòng hiếu kính của vua Gia Long dành cho đấng sinh thành đã chịu nhiều oan khuất trong thời biến loạn Tây Sơn và Trịnh - Nguyễn phân tranh.",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Khuôn viên Hưng Miếu thanh tịnh với bóng mát của các hàng sứ cổ.",
          historical_clues: [
            "Từng là nơi đặt thần vị của Định Vương và bà thân mẫu thân sinh vua Gia Long.",
          ],
        },
        task_prompt: "Nêu nhận xét về nghệ thuật chạm khắc và ý nghĩa đạo hiếu của công trình Hưng Miếu trong tổng thể tín ngưỡng triều Nguyễn.",
        expected_evidence: "Gia Long tri ân thân phụ Nguyễn Phúc Luân, tạo tiền đề tính chính thống lập vương triều.",
        u: 0.3845,
        v: 0.6720,
      },
      {
        order: 4,
        monument_slug: "trieu-to-mieu",
        monument_name_vi: "Triệu Miếu",
        monument_name_han_nom: "肇廟",
        title: "Trạm 4: Triệu Miếu — Khởi Nguồn Họ Nguyễn Nơi Phương Đông",
        inquiry_question: "Sự đối xứng giữa Triệu Miếu (phía Đông) và Thái Miếu/Thế Miếu (phía Tây) thể hiện triết lý quy hoạch phương Đông ra sao?",
        step_prompt:
          "Di chuyển sang góc Đông Nam Hoàng Thành đối xứng qua trục chính. Khảo sát nơi thờ phụng đức Triệu Tổ Tĩnh Hoàng Đế Nguyễn Kim — vị thủy tổ mở đầu dòng dõi chúa Nguyễn và vua Nguyễn.",
        required_sources: [
          {
            title: "Gia Định Thành Thông Chí (Trịnh Hoài Đức)",
            citation: "Ghi chép về quá trình Nam tiến mở đất và di sản các đời chúa Nguyễn.",
            type: "chronicle",
          },
        ],
        observation_points: [
          "Vị trí đối xứng qua trục Dũng Đạo theo thuyết Tả Chiêu Hữu Mục và Tiền Án Hậu Chẩm.",
          "Gian thờ đơn sơ mà uy nghiêm thể hiện sự mộc mạc thuở khai nguyên vương triều.",
        ],
        virtual_fieldwork: {
          overview_text:
            "Triệu Miếu nhắc nhở con cháu về công lao của Triệu Tổ Nguyễn Kim dấy cờ phù Lê diệt Mạc, tạo dựng tiền đề cho Thái Tổ Gia Dụ Hoàng Đế Nguyễn Hoàng vượt dãy Hoành Sơn vào trấn thủ Thuận Hóa năm 1558.",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Bình đồ vị trí Triệu Miếu ở khu vực phía Đông Hoàng Thành.",
          historical_clues: [
            "Đây là một trong những ngôi miếu đầu tiên được vua Gia Long xây dựng ngay sau khi định đô năm 1804.",
          ],
        },
        task_prompt: "So sánh chức năng của Triệu Miếu (thờ thủy tổ các chúa) với Thế Tổ Miếu (thờ các vua triều Nguyễn) theo quy chuẩn tông miếu phương Đông.",
        expected_evidence: "Phân biệt nguồn cội thuở chúa Tiên vào xứ Đàng Trong và đỉnh cao quân quyền thống nhất thời các vua Nguyễn.",
        u: 0.6158,
        v: 0.6720,
      },
    ],
  },
  {
    slug: "tu-cam-thanh-bien-doi-phuc-hoi",
    title: "Tử Cấm Thành — Biến Đổi Lịch Sử & Phục Hồi Di Sản",
    subtitle: "Dấu ấn thăng trầm qua chiến tranh, giao lưu văn hóa Đông Tây và nỗ lực bảo tồn",
    description:
      "Tuyến khảo sát chuyên sâu về diện mạo biến đổi của trung tâm nội cung triều Nguyễn từ thế kỷ 19 sang thế kỷ 20. Học sinh tìm hiểu sự pha trộn kiến trúc Pháp - Việt và những thách thức khảo cổ phục dựng di sản sau chiến tranh tàn phá.",
    duration_minutes: 55,
    age_group: "Học sinh THPT",
    target_grade: "Lớp 11 - 12",
    difficulty: "Nâng cao",
    cover_image: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
    theme_color: "purple",
    pedagogical_objectives: [
      "Đối chiếu hình ảnh tư liệu đầu thế kỷ 20 với hiện trạng phế tích để nhận diện tác động của chiến tranh (S1 & S2).",
      "Phân tích sự tiếp biến văn hóa Đông - Tây trong kiến trúc thời Khải Định tại Điện Kiến Trung (S2 & S3).",
      "Khai thác hồ sơ khảo cổ học và ảnh viễn thám trong phục hồi di tích (S3).",
      "Đưa ra lập luận bảo tồn: 'Nên phục dựng hoàn toàn hay giữ gìn dấu tích phế tích lịch sử?' (S4).",
    ],
    stops: [
      {
        order: 1,
        monument_slug: "dien-can-chanh",
        monument_name_vi: "Nền Móng Điện Cần Chánh",
        monument_name_han_nom: "勤政殿遺址",
        title: "Trạm 1: Nền Điện Cần Chánh — Vết Thương Khói Lửa & Khảo Cổ Học",
        inquiry_question: "Dấu tích nền móng còn lại cung cấp những bằng chứng vật chất nào giúp các nhà khoa học phục hồi lại công trình?",
        step_prompt:
          "Quan sát các chân đá táng cột bằng đá Thanh chạm hoa sen và hệ thống gạch Bát Tràng lát nền còn nguyên vẹn sau trận hỏa hoạn năm 1947.",
        required_sources: [
          {
            title: "Báo cáo khai quật khảo cổ nền điện Cần Chánh (Viện Khảo cổ học & ĐH Waseda Nhật Bản)",
            citation: "Khảo sát địa tầng móng bè và kết cấu gỗ lim dưới lòng đất thực hiện năm 1999-2003.",
            type: "conservation_report",
          },
        ],
        observation_points: [
          "Mạng lưới hàng chân đá táng tương ứng chính xác với bản đồ họa đồ thời vua Khải Định.",
          "Dấu vết tro xỉ than của trận cháy dữ dội đầu năm 1947.",
          "Dự án hợp tác quốc tế phục chế mô hình kỹ thuật số 3D độ phân giải cao.",
        ],
        virtual_fieldwork: {
          overview_text:
            "Đứng giữa không gian rộng mở lộng gió nơi từng là nơi làm việc uy nghi nhất của hoàng đế, học sinh cảm nhận rõ nét sự mong manh của di sản trước thảm họa chiến tranh.",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Khu vực khảo cổ nền Điện Cần Chánh qua ảnh chụp vệ tinh trực giao.",
          historical_clues: [
            "Các cột nhà cháy đã được thu thập mẫu thử niên đại đồng vị phóng xạ carbon C14.",
          ],
        },
        task_prompt: "Dựa vào hệ thống chân đá táng, hãy giải thích cách các nhà khảo cổ xác định lại quy mô số gian và chiều cao của Điện Cần Chánh.",
        expected_evidence: "Khoảng cách giữa các bước gian, đường kính lòng chân táng tương ứng với tiết diện thân cột gỗ lim.",
        u: 0.5002,
        v: 0.5312,
      },
      {
        order: 2,
        monument_slug: "duyet-thi-duong",
        monument_name_vi: "Duyệt Thị Đường",
        monument_name_han_nom: "閱是堂",
        title: "Trạm 2: Duyệt Thị Đường — Nhà Hát Cung Đình Cổ Nhất Việt Nam",
        inquiry_question: "Cấu trúc âm học và không gian sân khấu nhà hát cung đình được thiết kế thông minh ra sao mà không cần hệ thống tăng âm?",
        step_prompt:
          "Bước vào không gian nhà hát hai tầng gỗ lim. Quan sát sân khấu vuông ở giữa, vị trí ngai vua ở tầng trên đối diện và hệ thống lu chum chôn dưới sàn nhằm khuếch đại âm vang.",
        required_sources: [
          {
            title: "Hồ sơ Nhã Nhạc Cung Đình Huế (UNESCO Masterpiece of Oral and Intangible Heritage)",
            citation: "Văn bản định nghĩa không gian trình diễn ca múa nhạc và tuồng cung đình bác học.",
            type: "conservation_report",
          },
        ],
        observation_points: [
          "Mái nhà vòm cao vẽ hình mặt trời, mặt trăng và tinh tú đại diện cho vũ trụ quan bao la.",
          "Chỗ ngồi phân tầng nghiêm ngặt cho vương hầu, hậu phi và sứ thần ngoại quốc.",
          "Công trình được phục hồi thành công và hiện vẫn là nơi biểu diễn Nhã nhạc phục vụ công chúng.",
        ],
        virtual_fieldwork: {
          overview_text:
            "Xây dựng năm 1826 dưới triều Minh Mạng, Duyệt Thị Đường là trung tâm biểu diễn các vở tuồng lịch sử giáo dục lòng trung nghĩa và đạo làm người cho hoàng gia.",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Duyệt Thị Đường nằm ở góc Đông Bắc của Tử Cấm Thành.",
          historical_clues: [
            "Từng bị chuyển đổi làm trường Quốc Gia Âm Nhạc Huế trong giai đoạn 1962 trước khi được trả lại nguyên trạng bảo tồn.",
          ],
        },
        task_prompt: "Phân tích vì sao Duyệt Thị Đường được xem là bằng chứng vật chất bảo lưu trọn vẹn di sản phi vật thể Nhã nhạc Cung đình Huế.",
        expected_evidence: "Sự gắn kết hữu cơ giữa không gian biểu diễn cổ truyền và nghệ thuật diễn xướng tuồng cung đình.",
        u: 0.5720,
        v: 0.4950,
      },
      {
        order: 3,
        monument_slug: "thai-binh-lau",
        monument_name_vi: "Thái Bình Lâu",
        monument_name_han_nom: "太平樓",
        title: "Trạm 3: Thái Bình Lâu — Thư Viện Hoàng Gia & Nghệ Thuật Khảm Sành Sứ",
        inquiry_question: "Nghệ thuật ghép mảnh gốm sành sứ trên bờ nóc Thái Bình Lâu phản ánh sự sáng tạo độc đáo của nghệ nhân xứ Huế ra sao?",
        step_prompt:
          "Chiêm ngưỡng hoa văn tứ linh (Long, Lân, Quy, Phụng) và các bức cuốn thư trang trí bằng kỹ thuật cắt ghép mảnh sành chén bát cổ trên các đầu đao và bao lơn.",
        required_sources: [
          {
            title: "Tạp chí Đô Thành Hiếu Cổ (BAVH 1925)",
            citation: "Khảo cứu của tác giả Pháp về thú chơi sách và nghệ thuật trang trí cung đình thời Khải Định.",
            type: "chronicle",
          },
        ],
        observation_points: [
          "Tòa nhà hai tầng xây dựng thời Khải Định làm nơi đọc sách, ngâm thơ và nghỉ ngơi của hoàng đế.",
          "Hồ nước hình chữ nhật phía trước với hòn non bộ tạo cảnh quan sơn thủy hữu tình.",
          "Nội thất gỗ chạm khắc đề tài hoa lá và đồ cổ ngoạn tinh xảo bậc nhất.",
        ],
        virtual_fieldwork: {
          overview_text:
            "Thái Bình Lâu là một ốc đảo văn hóa thanh bình giữa lòng Tử Cấm Thành, nơi vua trút bỏ bớt gánh nặng triều chính để đắm mình vào kho tàng thi ca và tri thức bác học.",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Thái Bình Lâu phản chiếu bóng nước hồ hoa sen biếc.",
          historical_clues: [
            "Là một trong số rất ít công trình nội cung thoát khỏi sự tàn phá của ngọn lửa năm 1947.",
          ],
        },
        task_prompt: "Mô tả chất liệu và kỹ thuật khảm sành sứ tại Thái Bình Lâu. Kỹ thuật này có ưu điểm gì trong điều kiện khí hậu mưa bão khắc nghiệt của Huế?",
        expected_evidence: "Chất liệu men sành chịu được mưa nắng không phai màu, tận dụng phế liệu gốm sứ tạo thành nghệ thuật thị giác tráng lệ.",
        u: 0.5720,
        v: 0.4120,
      },
      {
        order: 4,
        monument_slug: "dien-kien-trung",
        monument_name_vi: "Điện Kiến Trung",
        monument_name_han_nom: "建中殿",
        title: "Trạm 4: Điện Kiến Trung — Giao Thoa Văn Hóa Tân Cổ Đông Tây & Kỳ Tích Phục Hồi",
        inquiry_question: "Vì sao Điện Kiến Trung được coi là biểu tượng đỉnh cao của phong cách nghệ thuật kiến trúc thời Khải Định?",
        step_prompt:
          "Đứng trước mặt tiền đồ sộ của tòa cung điện phục chế khánh thành năm 2024. Phân tích các chi tiết pha trộn giữa thức cột Phục Hưng Pháp, tường bê tông cốt thép với hoa văn rồng mây gốm sứ truyền thống.",
        required_sources: [
          {
            title: "Bản vẽ thiết kế của Nha Công Chính Đông Dương (1921-1923)",
            citation: "Lưu trữ tại Trung tâm Lưu trữ Quốc gia I (Hà Nội).",
            type: "archival_photo",
          },
          {
            title: "Hồ sơ dự án Tu bổ, tôn tạo Điện Kiến Trung (Trung tâm BTDT Cố đô Huế, hoàn thành 2024)",
            citation: "Tái hiện chính xác hàng triệu mảnh ghép gốm tráng men màu và các mảng đắp nổi sơn thếp.",
            type: "conservation_report",
          },
        ],
        observation_points: [
          "Mặt tiền mang dáng dấp lâu đài châu Âu kết hợp mái ngói lưu ly và đầu rồng uốn lượn.",
          "Hệ thống đèn chùm pha lê, sàn gạch hoa văn nhập khẩu cùng nội thất tiện nghi hiện đại đầu thế kỷ 20.",
          "Nơi sinh sống của gia đình vua Bảo Đại và Hoàng hậu Nam Phương trong những năm tháng cuối cùng của triều Nguyễn.",
        ],
        virtual_fieldwork: {
          overview_text:
            "Điện Kiến Trung từng bị bom đạn đánh sập hoàn toàn năm 1947 chỉ còn trơ trọi nền móng cỏ mọc hoang tàn suốt hơn 70 năm. Kỳ tích phục hồi nguyên vẹn công trình vào đầu năm 2024 là mốc son chói lọi của ngành bảo tồn di sản Việt Nam.",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Điện Kiến Trung rực rỡ sắc màu phục sinh nơi cực Bắc Tử Cấm Thành.",
          historical_clues: [
            "Tại đây Hoàng hậu Nam Phương đã chăm sóc các hoàng tử, công chúa với nếp sống kết hợp văn minh phương Tây và lễ giáo hoàng gia.",
            "Hoàng đế Bảo Đại đã hội ý cùng các cố vấn tại đây trước khi quyết định thoái vị.",
          ],
        },
        task_prompt: "Đưa ra đánh giá cá nhân theo Rubric S4: 'Theo em, việc phục dựng Điện Kiến Trung từ tro tàn phế tích có ý nghĩa như thế nào đối với việc gìn giữ ký ức lịch sử?'",
        expected_evidence: "Sự kết hợp giữa tư liệu lưu trữ chính xác (ảnh, bản vẽ) và bàn tay nghệ nhân giúp hiện thực hóa di sản mà không rơi vào giả cổ sai lệch.",
        u: 0.5002,
        v: 0.3340,
      },
    ],
  },
  {
    slug: "doi-song-cung-dinh-dien-tho",
    title: "Đời Sống Hoàng Gia & Cung Diên Thọ",
    subtitle: "Khám phá đời sống hậu cung, đạo hiếu phụng dưỡng và nghệ thuật vườn cảnh hoàng triều",
    description:
      "Tuyến khảo sát không gian sinh hoạt của các bậc Hoàng Thái Hậu và Hậu phi triều Nguyễn. Tìm hiểu nghệ thuật quy hoạch vườn cảnh, hồ nước thư thái và những quy chuẩn cung cấm trang nhã phía Tây Bắc Hoàng Thành.",
    duration_minutes: 45,
    age_group: "Học sinh THPT",
    target_grade: "Lớp 10 - 12",
    difficulty: "Cơ bản",
    cover_image: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
    theme_color: "rose",
    pedagogical_objectives: [
      "Nhận diện không gian cư trú của phụ nữ hoàng gia và mối liên hệ với đạo hiếu của các vua Nguyễn (S1).",
      "Khám phá các giai đoạn trùng tu, xây đắp cảnh quan qua các triều đại Tự Đức, Đồng Khánh, Khải Định (S2).",
      "Khai thác các câu chuyện dã sử và tài liệu hồi ức của các cung nữ, quan thị (S3).",
      "Thấu hiểu tâm tư và thân phận con người phía sau những bức tường thành thâm nghiêm (S4).",
    ],
    stops: [
      {
        order: 1,
        monument_slug: "cung-dien-tho",
        monument_name_vi: "Cung Diên Thọ",
        monument_name_han_nom: "延壽宮",
        title: "Trạm 1: Cung Diên Thọ — Nơi Hoàng Thái Hậu Hưởng Lộc Trường Niên",
        inquiry_question: "Quy mô và vị thế độc lập của Cung Diên Thọ phản ánh đạo hiếu của các vua triều Nguyễn đối với mẹ mình như thế nào?",
        step_prompt:
          "Đi qua cửa Thọ Chỉ để bước vào khuôn viên Cung Diên Thọ. Quan sát ngôi nhà chính điện nối thông với nhà Tịnh Minh qua hành lang có mái che bảo vệ người già khi mưa gió.",
        required_sources: [
          {
            title: "Đại Nam Thực Lục (Kỷ Đệ Tứ - Vua Tự Đức)",
            citation: "Ghi chép về việc vua Tự Đức đều đặn cứ hai ngày một lần sang vấn an sức khỏe Từ Dũ Bác Huệ Hoàng Thái Hậu.",
            type: "chronicle",
          },
        ],
        observation_points: [
          "Bình phong đá hoa cương chạm chữ 'Thọ' và họa tiết hoa sen thanh cao.",
          "Nhà Tạ Trường Du xây bên hồ sen nuôi cá chép giải trí cho Hoàng Thái Hậu.",
          "Hệ thống trường lang nối liền các ngôi nhà giúp di chuyển thuận tiện.",
        ],
        virtual_fieldwork: {
          overview_text:
            "Cung Diên Thọ là tổ hợp kiến trúc cung điện quy mô nhất còn tồn tại nguyên vẹn trong Hoàng Thành Huế, biểu trưng cho lời chúc sống lâu, an lạc gửi đến người mẹ của muôn dân.",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Khuôn viên Cung Diên Thọ rợp bóng cây xanh mát lành bên hồ sen.",
          historical_clues: [
            "Bà Từ Dũ nổi tiếng là người phụ nữ đức độ, hiểu biết sâu rộng chính trị và thường đưa ra những lời khuyên sáng suốt cho vua con.",
          ],
        },
        task_prompt: "Dẫn một câu chuyện lịch sử về mối quan hệ giữa vua Tự Đức và mẹ (Hoàng Thái hậu Từ Dũ) để làm rõ vai trò của Cung Diên Thọ.",
        expected_evidence: "Sách 'Từ Dũ Di Huấn' hoặc sự tích vua Tự Đức quỳ xin roi phạt khi ham đi săn quên ngày vấn an mẫu hậu.",
        u: 0.3780,
        v: 0.4720,
      },
      {
        order: 2,
        monument_slug: "cung-truong-sanh",
        monument_name_vi: "Cung Trường Sanh",
        monument_name_han_nom: "長生宮",
        title: "Trạm 2: Cung Trường Sanh — Hoa Viên Dưỡng Lão Hoàng Triều",
        inquiry_question: "Nghệ thuật xếp đá non bộ và tạo hình sông Đào mang dấu ấn phong thủy nào trong khuôn viên Cung Trường Sanh?",
        step_prompt:
          "Đi lên phía Bắc tiếp cận Cung Trường Sanh (trước gọi là Cung Cung Khánh). Khảo sát hòn non bộ nhân tạo mô phỏng tam sơn ngũ nhạc và con hào uốn lượn như dải lụa.",
        required_sources: [
          {
            title: "Khâm Định Đại Nam Hội Điển Sự Lệ (Tập 185 - Cung thất)",
            citation: "Ghi chép về việc sửa đổi tên gọi và quy hoạch khuôn viên hoa viên hoa cúc mùa thu.",
            type: "chronicle",
          },
        ],
        observation_points: [
          "Cổng tam quan đắp nổi rồng phượng và hoa cúc tinh mỹ bằng vôi vữa và sành sứ.",
          "Cầu gạch bắc qua sông đào nhân tạo bao quanh cung điện.",
          "Không gian yên tĩnh cách biệt hoàn toàn với không khí chính sự khẩn trương ngoài tiền triều.",
        ],
        virtual_fieldwork: {
          overview_text:
            "Cung Trường Sanh như một bức tranh thủy mặc sống động, là nơi các bà Thái Hoàng Thái Hậu (bà nội của vua) dạo cảnh ngắm hoa, uống trà dưỡng lão trong những năm tháng vãn niên.",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Cung Trường Sanh với hồ nước và cảnh quan non bộ thơ mộng.",
          historical_clues: [
            "Vua Khải Định từng tiến hành đợt trùng tu lớn mang hơi hướng kiến trúc phương Tây vào năm 1923 để mừng sinh nhật mẹ.",
          ],
        },
        task_prompt: "Nhận xét về sự phối hợp giữa kiến trúc nhà ở và cảnh quan thiên nhiên (cây cối, mặt nước, đá non bộ) tại Cung Trường Sanh.",
        expected_evidence: "Quy luật âm dương tương hợp, mặt nước làm mát không gian và đá non bộ tích tụ vượng khí dưỡng sinh.",
        u: 0.3780,
        v: 0.3540,
      },
      {
        order: 3,
        monument_slug: "dien-phung-tien",
        monument_name_vi: "Điện Phụng Tiên",
        monument_name_han_nom: "奉先殿",
        title: "Trạm 3: Điện Phụng Tiên — Miếu Thờ Dành Riêng Cho Nữ Giới Hoàng Tộc",
        inquiry_question: "Vì sao triều đình lại xây thêm Điện Phụng Tiên khi đã có Thế Tổ Miếu ở gần đó?",
        step_prompt:
          "Quan sát vị trí của Điện Phụng Tiên nằm giáp ranh giữa khu ở của Hậu cung và Thế Miếu. Tìm hiểu lý do các bà Hoàng hậu, cung phi không được phép bước chân vào Thế Miếu.",
        required_sources: [
          {
            title: "Luật Hậu Cung triều Nguyễn",
            citation: "Quy tắc cấm ngặt nữ giới không được tham gia lễ tế tổ tiên tại tiền triều.",
            type: "chronicle",
          },
        ],
        observation_points: [
          "Bình phong gạch tráng men và tam quan cổ kính còn đứng vững sau chiến tranh.",
          "Khuôn viên tĩnh mịch nơi tổ chức các lễ giỗ nội bộ do chính tay các phi tần nấu nướng tế tự.",
        ],
        virtual_fieldwork: {
          overview_text:
            "Điện Phụng Tiên ra đời xuất phát từ tấm lòng hiếu kính nhưng phải thích nghi với lễ giáo khắt khe: để các bà mẹ, người vợ có nơi bái lạy hương khói tiên đế mà không vi phạm quy chế tế tự nam giới.",
          media_url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          media_caption: "Khu vực cổng và tường bao cổ kính của Điện Phụng Tiên.",
          historical_clues: [
            "Công trình cũng bị bom đạn phá hủy trong kháng chiến chống Pháp năm 1947, hiện được các chuyên gia Đức và Việt Nam bảo tồn di tích phế tích.",
          ],
        },
        task_prompt: "Kết luận về quan niệm giới (nam - nữ) và sự linh hoạt trong việc tổ chức không gian tâm linh của hoàng tộc triều Nguyễn qua việc tạo dựng Điện Phụng Tiên.",
        expected_evidence: "Sự phân chia nghiêm ngặt giữa nghi lễ quốc gia công cộng (Thế Miếu) và tình cảm gia quyến tế tự riêng tư (Điện Phụng Tiên).",
        u: 0.3845,
        v: 0.5820,
      },
    ],
  },
];

export function getTrailBySlug(slug: string): ImperialTrail | undefined {
  if (slug === "truc-dung-dao-va-quyen-luc") {
    return IMPERIAL_TRAILS.find((t) => t.slug === "truc-dung-dao-quyen-luc");
  }
  return IMPERIAL_TRAILS.find((t) => t.slug === slug);
}
