/**
 * LƯU NIÊN – ĐẠI NỘI HUẾ
 * Heritage Image Corpus (Spec Patch V2.2)
 *
 * Comprehensive typed registry of verified heritage photographs and visual media.
 * Supports map thumbnails, monument dossier galleries, architectural detail studies,
 * and pedagogical inquiry tasks with explicit rights and edit disclosures.
 */

export type HeritageImageType =
  | "current_original"
  | "current_edited"
  | "reconstruction"
  | "archival"
  | "architectural_detail"
  | "aerial_reference";

export type HeritageViewpoint =
  | "front"
  | "rear"
  | "left"
  | "right"
  | "oblique"
  | "aerial"
  | "detail"
  | "unknown";

export type HeritageCategory =
  | "monument"
  | "architecture"
  | "citadel"
  | "panorama"
  | "art"
  | "culture";

export interface HeritageImage {
  id: string;
  siteId?: string | null;
  siteSlug?: string | null;
  src: string;
  thumbnailSrc?: string;
  alt: string;
  title: string;
  caption: string;
  imageType: HeritageImageType;
  viewpoint: HeritageViewpoint;
  category: HeritageCategory;
  captureDate?: string;
  historicalPeriod?: string;
  sourceName?: string;
  rightsStatus: "verified" | "permission_required" | "unknown" | "restricted";
  creditLine: string;
  editDisclosure?: string;
  verificationStatus: "unreviewed" | "needs_review" | "verified" | "rejected";
  featured: boolean;
  sortOrder: number;
}

export const HERITAGE_IMAGE_TYPES: Record<
  HeritageImageType,
  { label: string; badgeClass: string; description: string }
> = {
  current_original: {
    label: "Hiện trạng gốc",
    badgeClass: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30",
    description: "Quan sát tình trạng công trình ở thời điểm chụp thực tế",
  },
  current_edited: {
    label: "Hiện trạng xử lý",
    badgeClass: "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30",
    description: "Ảnh có xử lý ánh sáng hoặc góc chụp phục vụ nghiên cứu",
  },
  reconstruction: {
    label: "Phục chế / Tái hiện",
    badgeClass: "bg-purple-500/15 text-purple-700 dark:text-purple-400 border-purple-500/30",
    description: "Minh họa giả thuyết phục hồi hoặc hiện trạng sau trùng tu",
  },
  archival: {
    label: "Tư liệu lịch sử",
    badgeClass: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30",
    description: "Ảnh chụp tư liệu lưu trữ đầu thế kỷ 20 để đối chiếu qua thời gian",
  },
  architectural_detail: {
    label: "Chi tiết kiến trúc",
    badgeClass: "bg-amber-500/15 text-amber-800 dark:text-amber-300 border-amber-500/30",
    description: "Khảo sát cấu kiện vì kèo, bờ nóc, mái ngói hoặc nghệ thuật khảm sứ",
  },
  aerial_reference: {
    label: "Không ảnh tham chiếu",
    badgeClass: "bg-indigo-500/15 text-indigo-700 dark:text-indigo-400 border-indigo-500/30",
    description: "Ảnh chụp bao quát từ trên cao định vị không gian địa bàn",
  },
};

export const HERITAGE_CATEGORIES: Record<
  HeritageCategory,
  { label: string; iconName: string; description: string }
> = {
  monument: {
    label: "Công trình Hoàng Thành",
    iconName: "Landmark",
    description: "Các di tích trọng yếu: Ngọ Môn, Điện Thái Hòa, Điện Kiến Trung, Cung Diên Thọ",
  },
  architecture: {
    label: "Kiến trúc & Cấu kiện",
    iconName: "Hammer",
    description: "Hệ thống mái ngói lưu ly, hàng cột rường gỗ lim, vì kèo và bờ nóc",
  },
  citadel: {
    label: "Kinh thành & Cảnh quan",
    iconName: "Shield",
    description: "Cửa Thể Nhơn, Cửa Thượng Tứ, Phu Văn Lâu, Nghinh Lương Đình và hào thành",
  },
  panorama: {
    label: "Toàn cảnh & Trên cao",
    iconName: "Compass",
    description: "Góc nhìn bao quát không gian Đại Nội và quy hoạch phong thủy từ trên cao",
  },
  art: {
    label: "Mỹ thuật & Biểu tượng",
    iconName: "Sparkles",
    description: "Hình tượng rồng 5 móng, chạm trổ mộc và tranh tư liệu nghi lễ triều Nguyễn",
  },
  culture: {
    label: "Lễ hội & Văn hóa đêm",
    iconName: "Calendar",
    description: "Festival Huế và không gian chiếu sáng nghệ thuật Hoàng Cung",
  },
};

export const HERITAGE_IMAGES: HeritageImage[] = [
  {
    id: "img-ngo-mon-direct-hero",
    siteId: "site-ngo-mon",
    siteSlug: "ngo-mon",
    src: "/assets/imperial/heritage/ngomon.jpg",
    title: "Cổng Ngọ Môn — Tòa nghi môn biểu tượng Cố đô Huế",
    alt: "Toàn cảnh chính diện cổng Ngọ Môn sừng sững uy nghi nhìn từ quảng trường Kỳ Đài",
    caption:
      "Xây dựng năm Minh Mạng thứ 14 (1833), Ngọ Môn là cổng chính lớn nhất trong bốn cổng của Hoàng Thành Huế, nơi diễn ra các sự kiện triều chính trọng đại nhất của vương triều Nguyễn.",
    imageType: "current_original",
    viewpoint: "front",
    category: "monument",
    rightsStatus: "verified",
    creditLine: "Trung tâm Bảo tồn Di tích Cố đô Huế & Ảnh điền dã giáo dục",
    verificationStatus: "verified",
    featured: true,
    sortOrder: 1,
  },
  {
    id: "img-ngo-mon-lau-ngu-phung",
    siteId: "site-ngo-mon",
    siteSlug: "ngo-mon",
    src: "/assets/imperial/heritage/launguphung.jpg",
    title: "Lầu Ngũ Phụng trên đài đá Ngọ Môn",
    alt: "Lầu Ngũ Phụng hai tầng mái chồng diềm với 100 cây cột gỗ thanh thoát",
    caption:
      "Lầu Ngũ Phụng đặt trên đài đá Ngọ Môn, kết cấu 100 cây cột biểu trưng trăm họ thái bình, chia làm chín bộ mái với mái chính lợp ngói hoàng lưu ly và tám mái phụ lợp ngói thanh lưu ly.",
    imageType: "current_original",
    viewpoint: "front",
    category: "monument",
    rightsStatus: "verified",
    creditLine: "Tư liệu ảnh khảo sát kiến trúc Cố đô Huế",
    verificationStatus: "verified",
    featured: true,
    sortOrder: 2,
  },
  {
    id: "img-ngo-mon-gates",
    siteId: "site-ngo-mon",
    siteSlug: "ngo-mon",
    src: "/assets/imperial/heritage/congngomon.jpg",
    title: "Hệ thống 5 cửa vòm đài đá Ngọ Môn",
    alt: "Năm vòm cửa đá dưới chân cổng Ngọ Môn với cửa chính giữa dành cho thiên tử",
    caption:
      "Đài đá Ngọ Môn trổ 5 cửa ngõ: cửa chính giữa là Ngọ Môn dành riêng cho hoàng đế, hai cửa bên là Tả/Hữu Giáp Môn cho quan văn võ, hai cửa ngoài cùng là Tả/Hữu Dịch Môn cho binh mã cấm vệ.",
    imageType: "current_original",
    viewpoint: "front",
    category: "monument",
    rightsStatus: "verified",
    creditLine: "Tư liệu kiến trúc cổng thành hoàng gia",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 3,
  },
  {
    id: "img-ngo-mon-festival",
    siteId: "site-ngo-mon",
    siteSlug: "ngo-mon",
    src: "/assets/imperial/heritage/festival.jpg",
    title: "Lễ hội cung đình trước quảng trường Ngọ Môn",
    alt: "Không gian lễ hội văn hóa Festival Huế với dàn cờ hoa trang trọng trước cổng Ngọ Môn",
    caption:
      "Quảng trường Ngọ Môn — nơi diễn ra các sự kiện văn hóa nghệ thuật tôn vinh di sản Cố đô Huế trong các kỳ Festival quốc tế.",
    imageType: "current_original",
    viewpoint: "front",
    category: "culture",
    rightsStatus: "verified",
    creditLine: "Tư liệu Festival Huế & Di sản đương đại",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 4,
  },
  {
    id: "img-ngo-mon-night-illumination",
    siteId: "site-ngo-mon",
    siteSlug: "ngo-mon",
    src: "/assets/imperial/heritage/demhue.jpg",
    title: "Ngọ Môn và Kỳ Đài lung linh ánh đèn đêm",
    alt: "Cổng Ngọ Môn rực rỡ trong hệ thống đèn chiếu sáng nghệ thuật ban đêm",
    caption:
      "Cổng chính Hoàng Thành lung linh trong ánh sáng nghệ thuật phục vụ các hoạt động du lịch văn hóa đêm và tuần lễ Festival Huế.",
    imageType: "current_edited",
    viewpoint: "front",
    category: "culture",
    editDisclosure: "Chiếu sáng nghệ thuật kiến trúc ban đêm",
    rightsStatus: "verified",
    creditLine: "Tư liệu hình ảnh du lịch di sản Huế",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 5,
  },
  {
    id: "img-dien-thai-hoa-facade",
    siteId: "site-dien-thai-hoa",
    siteSlug: "dien-thai-hoa",
    src: "/assets/imperial/heritage/dienthaihoa.jpg",
    title: "Điện Thái Hòa — Biểu tượng quyền lực tối cao vương triều Nguyễn",
    alt: "Mặt tiền Điện Thái Hòa vừa hoàn tất đại trùng tu bảo tồn tổng thể toàn diện",
    caption:
      "Tòa điện thiết đại triều quan trọng bậc nhất của vương triều Nguyễn, xây dựng theo quy thức 'trùng thiềm điệp ốc' với 80 cột gỗ lim và hệ thống thơ văn thếp vàng 'nhất thi nhất họa'.",
    imageType: "current_original",
    viewpoint: "front",
    category: "monument",
    rightsStatus: "verified",
    creditLine: "Tư liệu trùng tu tổng thể di tích Điện Thái Hòa (2021-2025)",
    verificationStatus: "verified",
    featured: true,
    sortOrder: 6,
  },
  {
    id: "img-dien-thai-hoa-roof-side",
    siteId: "site-dien-thai-hoa",
    siteSlug: "dien-thai-hoa",
    src: "/assets/imperial/heritage/dienthaihoa2.jpg",
    title: "Góc nghiêng mái trùng thiềm điệp ốc Điện Thái Hòa",
    alt: "Chi tiết kết cấu mái kép hai tầng lợp ngói hoàng lưu ly vàng rực của Điện Thái Hòa",
    caption:
      "Kiến trúc nhà kép (trùng thiềm điệp ốc) với trần vỏ cua nối liền hai mái, trang trí rồng mây hồi long bằng pháp lam và sành sứ tinh xảo.",
    imageType: "current_original",
    viewpoint: "oblique",
    category: "monument",
    rightsStatus: "verified",
    creditLine: "Tư liệu kiến trúc cung điện Huế",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 7,
  },
  {
    id: "img-cau-trung-dao-thai-hoa",
    siteId: "site-cau-trung-dao",
    siteSlug: "cau-trung-dao",
    src: "/assets/imperial/heritage/dainoihue.jpg",
    title: "Cầu Trung Đạo và hồ Thái Dịch hướng về Điện Thái Hòa",
    alt: "Cầu Trung Đạo bằng đá bắc qua hồ Thái Dịch nở hoa sen dẫn vào sân Đại Triều Nghi",
    caption:
      "Cầu Trung Đạo xây dựng năm Minh Mạng thứ 14 (1833) bắc qua hồ Thái Dịch trên trục chính đạo, tạo khoảng chuyển tiếp cảnh quan nước phong thủy trước khi bước vào không gian đại triều.",
    imageType: "current_original",
    viewpoint: "front",
    category: "monument",
    rightsStatus: "verified",
    creditLine: "Tư liệu trục chính đạo Hoàng Thành",
    verificationStatus: "verified",
    featured: true,
    sortOrder: 8,
  },
  {
    id: "img-dien-kien-trung-facade",
    siteId: "site-dien-kien-trung",
    siteSlug: "dien-kien-trung",
    src: "/assets/imperial/heritage/dienkientrung.jpg",
    title: "Mặt tiền lộng lẫy Điện Kiến Trung sau phục hồi (2023)",
    alt: "Điện Kiến Trung với kiến trúc hỗn hợp Á - Âu rực rỡ hoa văn khảm sành sứ nhiều màu",
    caption:
      "Tòa điện hai tầng xây thời Khải Định (1921-1923), kết hợp kiến trúc cổ điển Pháp, Phục hưng Ý và nghệ thuật khảm sành sứ cung đình Huế, hoàn tất đại trùng tu phục chế năm 2023.",
    imageType: "current_original",
    viewpoint: "front",
    category: "monument",
    rightsStatus: "verified",
    creditLine: "Hồ sơ phục dựng khoa học Điện Kiến Trung (2019-2023)",
    verificationStatus: "verified",
    featured: true,
    sortOrder: 9,
  },
  {
    id: "img-cung-dien-tho-truong-du-ta",
    siteId: "site-cung-dien-tho",
    siteSlug: "cung-dien-tho",
    src: "/assets/imperial/heritage/truongduta.jpg",
    title: "Nhà Tạ Trường Du bên hồ sen Cung Diên Thọ",
    alt: "Nhà tạ bằng gỗ lim thanh bình dựng trên mặt nước hồ bán nguyệt Cung Diên Thọ",
    caption:
      "Tạ Trường Du dựng năm 1849 dưới thời vua Tự Đức, nằm ở phía đông chính điện Cung Diên Thọ. Đây là nhà thủy tạ tao nhã nơi Hoàng Thái Hậu ngắm hoa, thưởng sen và tĩnh dưỡng tuổi già.",
    imageType: "current_original",
    viewpoint: "front",
    category: "monument",
    rightsStatus: "verified",
    creditLine: "Tư liệu cảnh quan sân vườn Cung Diên Thọ",
    verificationStatus: "verified",
    featured: true,
    sortOrder: 10,
  },
  {
    id: "img-dai-noi-panorama",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/dainoi.jpg",
    title: "Quần thể kiến trúc cung điện Đại Nội Huế",
    alt: "Góc nhìn bao quát sân lát đá và dãy mái cung điện Đại Nội Huế",
    caption:
      "Không gian uy nghiêm của quần thể cung điện Hoàng Thành Huế với sự kết hợp hài hòa giữa sân chầu lát đá thanh, tường thành và hệ thống mái lợp ngói lưu ly truyền thống.",
    imageType: "current_original",
    viewpoint: "oblique",
    category: "panorama",
    rightsStatus: "verified",
    creditLine: "Tư liệu không gian tổng thể Hoàng Cung Huế",
    verificationStatus: "verified",
    featured: true,
    sortOrder: 11,
  },
  {
    id: "img-dai-noi-aerial-reference",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/dainoitrencao.jpg",
    title: "Đại Nội Huế nhìn từ trên cao (Ảnh không ảnh trực giao)",
    alt: "Toàn cảnh Hoàng Thành và Tử Cấm Thành Huế nhìn từ trên cao thể hiện trật tự quy hoạch phong thủy",
    caption:
      "Góc nhìn toàn cảnh trên không bao quát cấu trúc hình vuông của Hoàng Thành, trục thần đạo trung tâm từ Kỳ Đài - Ngọ Môn đến Điện Thái Hòa và Tử Cấm Thành.",
    imageType: "aerial_reference",
    viewpoint: "aerial",
    category: "panorama",
    rightsStatus: "verified",
    creditLine: "Ảnh không ảnh khảo sát Cố đô Huế",
    verificationStatus: "verified",
    featured: true,
    sortOrder: 12,
  },
  {
    id: "img-phu-van-lau-facade",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/phuvanlau.jpg",
    title: "Phu Văn Lâu — Tòa lầu niêm yết chiếu thư hoàng gia",
    alt: "Tòa lầu gỗ hai tầng thanh thoát nằm trên trục thần đạo phía trước Kỳ Đài",
    caption:
      "Xây dựng năm Gia Long thứ 18 (1819), Phu Văn Lâu là nơi niêm yết các chiếu thư, chỉ dụ quan trọng của hoàng đế và bảng vàng vinh danh các vị tân khoa tiến sĩ trong các khoa thi đình.",
    imageType: "current_original",
    viewpoint: "front",
    category: "citadel",
    rightsStatus: "verified",
    creditLine: "Tư liệu kiến trúc trục Tiền tiêu Kinh thành",
    verificationStatus: "verified",
    featured: true,
    sortOrder: 13,
  },
  {
    id: "img-phu-van-lau-landscape",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/phuvanlauview.jpg",
    title: "Toàn cảnh cảnh quan Phu Văn Lâu và công viên bờ sông Hương",
    alt: "Góc nhìn rộng không gian xanh bao quanh Phu Văn Lâu và Nghinh Lương Đình",
    caption:
      "Không gian cảnh quan xanh thoáng đãng phía trước kinh thành Huế, kết nối hài hòa giữa trục kiến trúc quyền lực phong kiến và cảnh quan thiên nhiên sông Hương thơ mộng.",
    imageType: "current_original",
    viewpoint: "oblique",
    category: "citadel",
    rightsStatus: "verified",
    creditLine: "Ảnh khảo cứu cảnh quan Cố đô Huế",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 14,
  },
  {
    id: "img-nghinh-luong-dinh",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/nghinhluongdinh.jpg",
    title: "Nghinh Lương Đình — Nhà thủy đình bên bờ sông Hương",
    alt: "Tòa thủy đình duyên dáng bên bến sông Hương nhìn ra Kỳ Đài và Kinh thành Huế",
    caption:
      "Tòa nhà tạ thủy đình xây dựng năm Tự Đức thứ 5 (1852) bên bờ bắc sông Hương, là nơi vua nghỉ ngơi, hóng mát ngắm cảnh sông trước khi bước lên thuyền ngự tuần du.",
    imageType: "current_original",
    viewpoint: "front",
    category: "citadel",
    rightsStatus: "verified",
    creditLine: "Tư liệu di tích Nghinh Lương Đình",
    verificationStatus: "verified",
    featured: true,
    sortOrder: 15,
  },
  {
    id: "img-kinh-thanh-tuong-thanh",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/kinhthanhhue.jpg",
    title: "Tường thành đá và hào nước Kim Thủy — Kinh thành Huế",
    alt: "Tường thành xây gạch vồ kiểu Vauban phòng thủ bao bọc bên bờ hào nước phẳng lặng",
    caption:
      "Hệ thống phòng thủ Kinh thành Huế được khởi công xây dựng từ năm 1805 dưới thời vua Gia Long, kết hợp tinh hoa kiến trúc quân sự phương Tây (thành lũy Vauban) với dịch học phương Đông.",
    imageType: "current_original",
    viewpoint: "oblique",
    category: "citadel",
    rightsStatus: "verified",
    creditLine: "Tư liệu kiến trúc thành lũy quân sự triều Nguyễn",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 16,
  },
  {
    id: "img-kinh-thanh-cong-thanh",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/kinhthanhhue2.jpg",
    title: "Cửa ô và cầu vòm gạch qua hào thành Kinh đô",
    alt: "Cổng thành cổ kính với cây cầu vòm đá bắc qua hào hộ thành",
    caption:
      "Cầu đá vòm cuốn bắc qua hào Kim Thủy dẫn vào các cửa ô thành Huế, tạo nên cảnh quan cổ kính rợp bóng cây xanh ven bờ hào.",
    imageType: "current_original",
    viewpoint: "front",
    category: "citadel",
    rightsStatus: "verified",
    creditLine: "Tư liệu khảo sát cửa ô Kinh thành Huế",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 17,
  },
  {
    id: "img-kinh-thanh-cua-the-nhon",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/cuathenhon.jpg",
    title: "Cửa Thể Nhơn (Cửa Ngăn) — Kinh thành Huế",
    alt: "Cửa Thể Nhơn hay Cửa Ngăn phía đông nam của Kinh thành Huế dẫn vào Hoàng Thành",
    caption:
      "Cửa Thể Nhơn nằm ở mặt nam Kinh thành, thường gọi là Cửa Ngăn do trước đây mỗi khi vua xuất cung tuần du, đường đi qua cửa này được ngăn lại để bảo đảm an ninh.",
    imageType: "current_original",
    viewpoint: "front",
    category: "citadel",
    rightsStatus: "verified",
    creditLine: "Tư liệu hệ thống 10 cửa Kinh thành",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 18,
  },
  {
    id: "img-kinh-thanh-cua-thuong-tu",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/cuathuongtu.jpg",
    title: "Cửa Thượng Tứ (Đông Nam Môn) — Kinh thành Huế",
    alt: "Cửa Thượng Tứ với vọng lâu cong vút và cổng vòm xây bằng gạch vồ thời Gia Long",
    caption:
      "Cửa Đông Nam của Kinh thành Huế xây dựng năm 1809 dưới triều vua Gia Long, bên ngoài cửa trước đây có Viện Thượng Tứ chuyên coi việc nuôi dưỡng và huấn luyện ngựa hoàng gia.",
    imageType: "current_original",
    viewpoint: "oblique",
    category: "citadel",
    rightsStatus: "verified",
    creditLine: "Tư liệu hệ thống 10 cửa Kinh thành",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 19,
  },
  {
    id: "img-mai-nha-luu-ly",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/mainha.jpg",
    title: "Nghệ thuật đắp nổi bờ nóc và ngói lưu ly cung đình",
    alt: "Chi tiết bờ nóc đắp hình tượng lưỡng long chầu nguyệt bằng kỹ thuật ghép mảnh sành sứ",
    caption:
      "Bờ nóc mái điện với hình tượng Lưỡng long triều nhật (hai rồng chầu mặt trời) được đắp nổi bằng vôi vữa trộn mật mía và ghép hàng ngàn mảnh sành sứ, sỏi đá màu rực rỡ.",
    imageType: "architectural_detail",
    viewpoint: "detail",
    category: "architecture",
    rightsStatus: "verified",
    creditLine: "Tư liệu chi tiết mỹ thuật bờ nóc di tích Huế",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 20,
  },
  {
    id: "img-kien-truc-cot-ruong",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/kientruc.jpg",
    title: "Hệ cột gỗ lim và trường lang cung đình",
    alt: "Hàng cột gỗ lim sơn son thếp vàng trong dãy trường lang che mưa nắng",
    caption:
      "Hệ thống hành lang có mái che (trường lang) đặc trưng của Đại Nội Huế, sử dụng kết cấu rường gỗ lim truyền thống vừa bền chắc vừa thích ứng với khí hậu mưa nắng miền Trung.",
    imageType: "architectural_detail",
    viewpoint: "detail",
    category: "architecture",
    rightsStatus: "verified",
    creditLine: "Tư liệu kết cấu mộc truyền thống Huế",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 21,
  },
  {
    id: "img-kien-truc-hien-cung-dinh",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/kientruc.png",
    title: "Cấu trúc hiên và vì kèo gỗ rường cung đình",
    alt: "Không gian tiền tế và hiên nhà rường cung đình với vì kèo trạm trổ hoa lá tinh tế",
    caption:
      "Nghệ thuật chạm khắc gỗ cung đình Huế theo lối tả thực kết hợp cách điệu mô típ hoa sen, lá hóa rồng, phản ánh tay nghề đỉnh cao của nghệ nhân mộc truyền thống.",
    imageType: "architectural_detail",
    viewpoint: "detail",
    category: "architecture",
    rightsStatus: "verified",
    creditLine: "Tư liệu điêu khắc mộc cung đình triều Nguyễn",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 22,
  },
  {
    id: "img-kien-truc-dao-mai-bo-noc",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/kientruc3.png",
    title: "Chi tiết bờ nóc và góc đao rồng chầu mái ngói",
    alt: "Đầu đao uốn cong thanh thoát và tượng rồng đắp nổi sành sứ trên bờ nóc cung điện",
    caption:
      "Góc mái cung đình Huế với độ dốc vừa phải giúp thoát nước nhanh trong mùa mưa bão, điểm xuyết tượng rồng ngậm bờ nóc và con giống sứ tinh tế.",
    imageType: "architectural_detail",
    viewpoint: "detail",
    category: "architecture",
    rightsStatus: "verified",
    creditLine: "Tư liệu hoa văn bờ mái cung điện",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 23,
  },
  {
    id: "img-kien-truc-hue-tong-the",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/kientruchue2.png",
    title: "Quy thức mái ngói âm dương và đường bờ nóc uy nghiêm",
    alt: "Tầng tầng lớp lớp mái ngói cung đình Huế dưới ánh nắng vàng Cố đô",
    caption:
      "Trật tự mái ngói hoàng lưu ly (vàng) và thanh lưu ly (xanh) phân tầng theo phẩm trật công trình trong sơ đồ quy hoạch tổng thể Hoàng Thành.",
    imageType: "architectural_detail",
    viewpoint: "oblique",
    category: "architecture",
    rightsStatus: "verified",
    creditLine: "Tư liệu nghệ thuật ngói tráng men lưu ly Cố đô",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 24,
  },
  {
    id: "img-my-thuat-cung-dinh",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/mythuatjpg.jpg",
    title: "Nghệ thuật chạm khắc và hoa văn cổ triều Nguyễn",
    alt: "Họa tiết hoa văn chạm trổ mây lửa, bát bửu và linh thú cung đình",
    caption:
      "Mô típ trang trí cung đình Huế chứa đựng hàm nghĩa cát tường, trường thọ và vương đạo, thể hiện triết lý mỹ học Nho giáo kết hợp với mỹ cảm dân gian Việt Nam.",
    imageType: "architectural_detail",
    viewpoint: "detail",
    category: "art",
    rightsStatus: "verified",
    creditLine: "Tư liệu mỹ thuật tạo hình cung đình Huế",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 25,
  },
  {
    id: "img-my-thuat-rong-hoang-trieu",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/rongthoily.png",
    title: "Hình tượng Rồng năm móng biểu trưng vương quyền tối thượng",
    alt: "Đồ họa mỹ thuật mô tả chi tiết rồng năm móng vần vũ trong mây lửa cung đình",
    caption:
      "Hình tượng rồng 5 móng chỉ dành riêng cho hoàng đế, xuất hiện dày đặc trên ngai vàng, bửu tán, áo long bào và bờ nóc các tòa chính điện như Thái Hòa và Cần Chánh.",
    imageType: "architectural_detail",
    viewpoint: "detail",
    category: "art",
    rightsStatus: "verified",
    creditLine: "Tư liệu nghiên cứu mỹ thuật rồng thời Nguyễn",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 26,
  },
  {
    id: "img-tranh-tu-lieu-cung-dinh",
    siteId: null,
    siteSlug: null,
    src: "/assets/imperial/heritage/tranh.png",
    title: "Tranh khắc tư liệu mỹ thuật nghi lễ cung đình triều Nguyễn",
    alt: "Bức họa cổ mô tả đoàn ngự đạo rước kiệu hoàng gia và các nghi thức triều hội",
    caption:
      "Tranh tư liệu mô tả các nghi lễ hoàng cung, thể hiện chi tiết cờ quạt, loan giá, tàn lọng và trang phục quan viên trong các buổi tuần du hoặc tế giao.",
    imageType: "archival",
    viewpoint: "unknown",
    category: "art",
    rightsStatus: "verified",
    creditLine: "Kho tranh tư liệu lịch sử hoàng gia triều Nguyễn",
    verificationStatus: "verified",
    featured: false,
    sortOrder: 27,
  },
];

/**
 * Returns all verified heritage images sorted by sortOrder.
 */
export function getAllHeritageImages(): HeritageImage[] {
  return [...HERITAGE_IMAGES].sort((a, b) => a.sortOrder - b.sortOrder);
}

/**
 * Returns images specifically associated with a monument site.
 */
export function getHeritageImagesBySite(siteSlug: string): HeritageImage[] {
  return HERITAGE_IMAGES.filter((img) => img.siteSlug === siteSlug).sort(
    (a, b) => a.sortOrder - b.sortOrder,
  );
}

/**
 * Returns the primary (featured) image for a monument, or the first available one.
 */
export function getPrimaryHeritageImage(siteSlug: string): HeritageImage | null {
  const images = getHeritageImagesBySite(siteSlug);
  if (images.length === 0) return null;
  return images.find((img) => img.featured) || images[0];
}

/**
 * Returns images filtered by broad thematic category.
 */
export function getHeritageImagesByCategory(category: HeritageCategory): HeritageImage[] {
  return HERITAGE_IMAGES.filter((img) => img.category === category).sort(
    (a, b) => a.sortOrder - b.sortOrder,
  );
}
