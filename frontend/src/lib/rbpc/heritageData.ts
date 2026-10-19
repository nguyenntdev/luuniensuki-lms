/**
 * LƯU NIÊN — RBPC 2026: Official Huế Heritage Dataset & Query Helpers
 * Sourced from data/heritage-hue/inventory.unesco-14.yaml and Master Spec V2.
 */

import type { HeritagePlace } from '@/types/heritage';
import type { HeritageFilterValues } from '@/components/explore/HeritageFilters';

/**
 * Remove diacritics / tone marks from Vietnamese and Latin strings for accent-insensitive search.
 * Converts 'Ngọ Môn' -> 'ngo mon', 'Tự Đức' -> 'tu duc', 'Phường Đúc' -> 'phuong duc'.
 */
export function removeDiacritics(str: unknown): string {
  return String(str || '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .toLowerCase()
    .trim();
}

/**
 * Verify whether a heritage place is part of the UNESCO World Heritage inscription (Complex of Huế Monuments - 678).
 */
export function isUnescoComponent(place: HeritagePlace): boolean {
  if (!place) return false;
  const ref = place.official_reference_id || '';
  const des = place.official_designation || '';
  return ref.startsWith('678') || ref.startsWith('UNESCO') || /unesco/i.test(des);
}

/**
 * Filter heritage places by category, search keywords, UNESCO status, and 3D availability.
 * Implements diacritic-tolerant accent-insensitive search across name_vi, name_en, ref id, and summaries.
 */
export function filterHeritagePlaces(
  places: HeritagePlace[],
  filters: HeritageFilterValues
): HeritagePlace[] {
  if (!Array.isArray(places)) return [];

  const queryNorm = removeDiacritics(filters.q || '');
  const targetCategory = filters.category;
  const unescoOnly = Boolean(filters.unescoOnly);
  const has3dOnly = Boolean(filters.has3dOnly);
  const accessStatus = filters.accessStatus;

  return places.filter((place) => {
    // 1. Category Filter
    if (targetCategory && targetCategory !== 'all') {
      if (place.heritage_category !== targetCategory) {
        // Special case: Duyệt Thị Đường can also be viewed as music_performance (Royal Theater)
        if (targetCategory === 'music_performance' && place.slug === 'duyet-thi-duong') {
          // allow match
        } else {
          return false;
        }
      }
    }

    // 2. UNESCO 14 Component Filter
    if (unescoOnly && !isUnescoComponent(place)) {
      return false;
    }

    // 3. 3D Model Availability Filter
    if (has3dOnly && !place.has_3d) {
      return false;
    }

    // 4. Access Status Filter
    if (accessStatus && accessStatus !== 'all') {
      if (place.current_access_status !== accessStatus) {
        return false;
      }
    }

    // 5. Diacritic-tolerant Keyword Search
    if (queryNorm) {
      const nameVi = removeDiacritics(place.name_vi);
      const nameEn = removeDiacritics(place.name_en);
      const refId = removeDiacritics(place.official_reference_id);
      const slug = removeDiacritics(place.slug);
      const period = removeDiacritics(place.period_label);
      const summaryVi = removeDiacritics(place.visitor_summary_vi);
      const summaryEn = removeDiacritics(place.visitor_summary_en);

      const matches =
        nameVi.includes(queryNorm) ||
        nameEn.includes(queryNorm) ||
        refId.includes(queryNorm) ||
        slug.includes(queryNorm) ||
        period.includes(queryNorm) ||
        summaryVi.includes(queryNorm) ||
        summaryEn.includes(queryNorm);

      if (!matches) {
        return false;
      }
    }

    return true;
  });
}

/**
 * Authentic 24-place Huế Heritage Catalogue fallback dataset.
 */
export const DEFAULT_HERITAGE_PLACES: HeritagePlace[] = [
  {
    "id": "678-001",
    "slug": "kinh-thanh-hue",
    "name_vi": "Kinh thành Huế (bao gồm Hoàng thành và Tử Cấm thành)",
    "name_en": "Huế Citadel (including Imperial City and Purple Forbidden City)",
    "entity_type": "site",
    "heritage_category": "imperial_architecture",
    "parent_id": null,
    "official_reference_id": "678-001",
    "official_designation": "UNESCO World Heritage Property Component (678-001) / Di tích Quốc gia Đặc biệt",
    "period_label": "Thời Nguyễn (1805–1945; khởi lập thời Gia Long 1805, hoàn thiện thời Minh Mạng 1832)",
    "historical_state": "standing",
    "location_lat": 16.4697,
    "location_lon": 107.5779,
    "geo_precision": "polygon_centroid",
    "current_access_status": "open",
    "visitor_summary_vi": "Kinh thành Huế là trung tâm chính trị, quân sự và văn hóa của triều Nguyễn từ năm 1802 đến năm 1945. Được xây dựng kết hợp giữa nguyên lý quy hoạch cung thành phương Đông và kỹ thuật công sự phòng thủ Vauban phương Tây, khu vực này bao bọc Hoàng thành và Tử Cấm thành với hàng chục cung điện, miếu thờ hoàng gia.",
    "visitor_summary_en": "The Huế Citadel served as the administrative, ceremonial, and dynastic center of the Nguyễn Dynasty from 1802 to 1945. Engineered through a synthesis of East Asian royal geomancy and French Vauban fortification principles, it encloses the Imperial City and Purple Forbidden City with dozens of royal palaces, shrines, and pavilions.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": true,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "678-002",
    "slug": "chua-thien-mu",
    "name_vi": "Chùa Thiên Mụ (Linh Mụ Tự)",
    "name_en": "Thiên Mụ Pagoda (Pagoda of the Celestial Lady)",
    "entity_type": "site",
    "heritage_category": "religious_spiritual",
    "parent_id": null,
    "official_reference_id": "678-002",
    "official_designation": "UNESCO World Heritage Property Component (678-002) / Di tích Lịch sử - Văn hóa Quốc gia",
    "period_label": "Thời Chúa Nguyễn đến Triều Nguyễn (Khởi lập năm 1601 thời Chúa Tiên Nguyễn Hoàng; mở rộng năm 1844 thời Thiệu Trị)",
    "historical_state": "standing",
    "location_lat": 16.4533,
    "location_lon": 107.545,
    "geo_precision": "exact_gps",
    "current_access_status": "open",
    "visitor_summary_vi": "Ngôi cổ tự danh tiếng tọa lạc trên đồi Hà Khê bên bờ bắc sông Hương, gắn liền với huyền tích bà tiên áo đỏ dự báo điềm lành dựng nước của Chúa Tiên Nguyễn Hoàng năm 1601. Chùa nổi bật với tháp Phước Duyên hình bát giác 7 tầng cao 21m xây năm 1844 và Đại Hồng Chung đúc năm 1710.",
    "visitor_summary_en": "An iconic ancient pagoda situated atop Hà Khê hill along the northern bank of the Perfume River, founded in 1601 by Lord Nguyễn Hoàng following a local legend of a red-robed celestial lady. The complex features the 21-meter, seven-story octagonal Phước Duyên Tower erected in 1844 and the Great Bell cast in 1710.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": true,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "678-003",
    "slug": "van-mieu-vo-mieu",
    "name_vi": "Văn Miếu và Võ Miếu Huế",
    "name_en": "Temple of Letters (Văn Miếu) and Temple of Literature / Martial Temple (Võ Miếu)",
    "entity_type": "site",
    "heritage_category": "imperial_architecture",
    "parent_id": null,
    "official_reference_id": "678-003",
    "official_designation": "UNESCO World Heritage Property Component (678-003) / Di tích Lịch sử Quốc gia",
    "period_label": "Triều Gia Long & Minh Mạng (Văn Miếu lập năm 1808 thời Gia Long; Võ Miếu lập năm 1835 thời Minh Mạng)",
    "historical_state": "partially_lost",
    "location_lat": 16.4517,
    "location_lon": 107.5358,
    "geo_precision": "approximate_site",
    "current_access_status": "open",
    "visitor_summary_vi": "Cụm di tích tôn vinh Nho học và võ nghiệp quốc gia dưới triều Nguyễn. Văn Miếu còn lưu giữ hệ thống 32 tấm bia đá đề danh 293 vị Tiến sĩ Nho học từ khoa thi 1822 đến 1919; các kiến trúc đại điện chính đã bị hư hại hoặc tiêu biến qua chiến tranh, hiện duy trì không gian văn bia và các cổng miếu cổ kính.",
    "visitor_summary_en": "Dual royal ceremonial monuments dedicated to Confucian scholarship and military achievement under the Nguyễn Dynasty. Văn Miếu preserves an intact collection of 32 stone doctor stelae recording 293 imperial doctoral graduates (1822–1919); primary temple halls were damaged during 20th-century warfare, while stele pavilions remain preserved.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "678-004",
    "slug": "ho-quyen-voi-re",
    "name_vi": "Hổ Quyền và Điện Voi Ré",
    "name_en": "Royal Arena (Hổ Quyền) and Voi Ré Temple (Long Châu Miếu)",
    "entity_type": "site",
    "heritage_category": "imperial_architecture",
    "parent_id": null,
    "official_reference_id": "678-004",
    "official_designation": "UNESCO World Heritage Property Component (678-004) / Di tích Lịch sử Quốc gia",
    "period_label": "Triều Gia Long & Minh Mạng (Điện Voi Ré lập năm 1817 thời Gia Long; Hổ Quyền xây dựng năm 1830 thời Minh Mạng)",
    "historical_state": "restored",
    "location_lat": 16.4475,
    "location_lon": 107.5619,
    "geo_precision": "exact_gps",
    "current_access_status": "open",
    "visitor_summary_vi": "Hổ Quyền là đấu trường lộ thiên hình vành khăn bằng gạch vồ độc nhất vô nhị ở Việt Nam, nơi triều Nguyễn tổ chức các trận tử chiến giữa voi và hổ để rèn luyện lòng dũng cảm cho tượng binh. Cách Hổ Quyền vài trăm mét là Điện Voi Ré (Long Châu Miếu), miếu thờ thần hộ vệ loài voi và nơi an táng những chiến tượng trung nghĩa.",
    "visitor_summary_en": "Hổ Quyền is a unique circular open-air colosseum built with ancient terracotta bricks in 1830, where imperial authorities staged controlled duels between royal elephants and tigers to train cavalry elephants. Nearby stands Voi Ré Temple (Long Châu Miếu), an imperial shrine consecrated in 1817 to honor loyal war elephants.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": true,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "678-005",
    "slug": "lang-duc-duc",
    "name_vi": "Lăng Dục Đức (An Lăng)",
    "name_en": "Tomb of Dục Đức (An Lăng)",
    "entity_type": "site",
    "heritage_category": "royal_tomb",
    "parent_id": null,
    "official_reference_id": "678-005",
    "official_designation": "UNESCO World Heritage Property Component (678-005) / Di tích Lịch sử Quốc gia",
    "period_label": "Triều Thành Thái & Duy Tân (Khởi dựng năm 1890 thời Thành Thái; nơi an táng 3 vị vua: Dục Đức, Thành Thái, Duy Tân)",
    "historical_state": "restored",
    "location_lat": 16.4447,
    "location_lon": 107.5911,
    "geo_precision": "approximate_site",
    "current_access_status": "open",
    "visitor_summary_vi": "An Lăng là quần thể lăng tẩm đặc biệt nằm ngay trong nội thị thành phố Huế, là nơi an nghỉ của ba thế hệ quân vương triều Nguyễn có số phận lịch sử thăng trầm: vua Dục Đức cùng hai vị vua yêu nước chống thực dân Pháp là Thành Thái và Duy Tân. Kiến trúc khiêm nhường với điện Long Ân làm trung tâm tẩm điện.",
    "visitor_summary_en": "An Lăng is a distinctive imperial burial complex situated within urban Huế, serving as the resting place of three generations of Nguyễn monarchs: Emperor Dục Đức, and his patriotic anti-colonial successors Emperor Thành Thái and Emperor Duy Tân. Features a modest layout centered on Long Ân Temple.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "678-006",
    "slug": "dan-nam-giao",
    "name_vi": "Đàn Nam Giao",
    "name_en": "Nam Giao Esplanade (Altar of Heaven and Earth)",
    "entity_type": "monument",
    "heritage_category": "imperial_architecture",
    "parent_id": null,
    "official_reference_id": "678-006",
    "official_designation": "UNESCO World Heritage Property Component (678-006) / Di tích Quốc gia Đặc biệt",
    "period_label": "Triều Gia Long đến Bảo Đại (Khởi công năm 1806; đại lễ tế Giao cử hành định kỳ 3 năm một lần)",
    "historical_state": "restored",
    "location_lat": 16.4386,
    "location_lon": 107.5858,
    "geo_precision": "exact_gps",
    "current_access_status": "open",
    "visitor_summary_vi": "Đàn tế Trời Đất linh thiêng và quy mô bậc nhất triều Nguyễn, tọa lạc trên đồi cao phía nam kinh thành giữa rừng thông xanh ngát. Cấu trúc đàn tế gồm ba tầng: Viên Đàn (hình tròn trên cùng tượng trưng cho Trời), Phương Đàn (hình vuông ở giữa tượng trưng cho Đất), và tầng hạ ngoài cùng, phản ánh triết lý vũ trụ Nho giáo.",
    "visitor_summary_en": "The paramount open-air imperial altar of the Nguyễn Dynasty, located in a pine forest south of the Citadel. The three-tiered stone terrace embodies traditional Confucian cosmology: the circular upper terrace (Viên Đàn) representing Heaven, the square middle terrace (Phương Đàn) representing Earth, and the enclosing perimeter terrace.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "678-007",
    "slug": "lang-tu-duc",
    "name_vi": "Lăng Tự Đức (Khiêm Lăng / Vạn Niên Cơ)",
    "name_en": "Tomb of Tự Đức (Khiêm Tomb / Vạn Niên Cơ)",
    "entity_type": "site",
    "heritage_category": "royal_tomb",
    "parent_id": null,
    "official_reference_id": "678-007",
    "official_designation": "UNESCO World Heritage Property Component (678-007) / Di tích Quốc gia Đặc biệt",
    "period_label": "Triều Tự Đức (Xây dựng 1864–1867; sử dụng làm hành cung sinh thời và lăng viện vĩnh cửu)",
    "historical_state": "standing",
    "location_lat": 16.4331,
    "location_lon": 107.5647,
    "geo_precision": "exact_gps",
    "current_access_status": "open",
    "visitor_summary_vi": "Tuyệt tác kiến trúc cảnh quan vườn lăng (viên lâm) triều Nguyễn. Được chia thành hai khu vực: Tẩm điện (Khiêm Cung) và Lăng mộ (Khiêm Lăng), bố trí mềm mại quanh hồ Lưu Khiêm, đảo Tịnh Khiêm và hai nhà thủy tạ tao nhã (Xung Khiêm Tạ, Dũ Khiêm Tạ). Nơi lưu giữ văn bia Khiêm Cung Ký đồ sộ nặng 20 tấn do chính vua Tự Đức soạn thảo.",
    "visitor_summary_en": "A lyrical masterpiece of imperial garden-tomb (viên lâm) landscape architecture. Divided into a residential temple palace (Khiêm Cung) and tomb sanctuary (Khiêm Lăng), arranged around Lưu Khiêm Lake, islet gardens, and lakeside pavilions (Xung Khiêm Tạ, Dũ Khiêm Tạ). Houses the 20-ton stone stele bearing the self-critical Khiêm Cung Ký inscription.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": true,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "678-008",
    "slug": "lang-dong-khanh",
    "name_vi": "Lăng Đồng Khánh (Tư Lăng)",
    "name_en": "Tomb of Đồng Khánh (Tư Tomb)",
    "entity_type": "site",
    "heritage_category": "royal_tomb",
    "parent_id": null,
    "official_reference_id": "678-008",
    "official_designation": "UNESCO World Heritage Property Component (678-008) / Di tích Quốc gia Đặc biệt",
    "period_label": "Triều Đồng Khánh đến Khải Định (Điện Ngưng Hy dựng 1888–1889; khu lăng mộ hoàn thành 1917–1923)",
    "historical_state": "restored",
    "location_lat": 16.4339,
    "location_lon": 107.5694,
    "geo_precision": "approximate_site",
    "current_access_status": "open",
    "visitor_summary_vi": "Quần thể lăng tẩm đánh dấu bước chuyển mình mỹ thuật từ phong cách kiến trúc cung đình truyền thống sang giao thoa Tây - Đông. Điện Ngưng Hy lưu giữ nghệ thuật sơn son thếp vàng đỉnh cao và các bức tranh khảm sành sứ, ngói lưu ly tinh mỹ; khu lăng mộ xây dựng dưới thời Khải Định mang rõ nét ảnh hưởng của nghệ thuật kiến trúc Âu - Á.",
    "visitor_summary_en": "An imperial tomb marking the aesthetic transition from pure classical court architecture to Euro-Asian eclecticism. Ngưng Hy Temple features brilliant gilded lacquerwork and porcelain mosaic friezes, while the tomb precinct completed under Emperor Khải Định (1917–1923) reflects early modern architectural influences.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "678-009",
    "slug": "dien-hon-chen",
    "name_vi": "Điện Hòn Chén (Huệ Nam Điện)",
    "name_en": "Hòn Chén Temple (Huệ Nam Palace)",
    "entity_type": "site",
    "heritage_category": "religious_spiritual",
    "parent_id": null,
    "official_reference_id": "678-009",
    "official_designation": "UNESCO World Heritage Property Component (678-009) / Di tích Lịch sử - Tín ngưỡng Quốc gia",
    "period_label": "Thời Chúa Nguyễn đến Triều Đồng Khánh (Thờ Mẫu Thiên Y A Na; mở rộng quy mô lớn năm 1886 thời Đồng Khánh)",
    "historical_state": "standing",
    "location_lat": 16.4172,
    "location_lon": 107.5636,
    "geo_precision": "exact_gps",
    "current_access_status": "open",
    "visitor_summary_vi": "Trung tâm tín ngưỡng Thờ Mẫu và giao thoa văn hóa Việt - Chăm đặc sắc bậc nhất xứ Huế, tọa lạc trên vách đá núi Ngọc Trản soi bóng xuống dòng sông Hương. Điện thờ chính là Huệ Nam Điện, nơi diễn ra lễ hội rước thánh bằng thuyền rồng náo nhiệt trên sông Hương vào tháng Ba và tháng Bảy âm lịch hàng năm.",
    "visitor_summary_en": "A dramatic cliffside spiritual sanctuary on Ngọc Trản mountain along the Perfume River, illustrating the syncretic fusion of indigenous Vietnamese Mother Goddess (Đạo Mẫu) worship and Cham religious reverence for Goddess Po Nagar (Thiên Y A Na). Rebuilt under Emperor Đồng Khánh in 1886; hosts annual riverboat pilgrimages.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "678-010",
    "slug": "lang-thieu-tri",
    "name_vi": "Lăng Thiệu Trị (Xương Lăng)",
    "name_en": "Tomb of Thiệu Trị (Xương Tomb)",
    "entity_type": "site",
    "heritage_category": "royal_tomb",
    "parent_id": null,
    "official_reference_id": "678-010",
    "official_designation": "UNESCO World Heritage Property Component (678-010) / Di tích Quốc gia Đặc biệt",
    "period_label": "Triều Tự Đức (Khởi công tháng 2 năm 1848, hoàn thành sau 10 tháng thi công thần tốc)",
    "historical_state": "restored",
    "location_lat": 16.4161,
    "location_lon": 107.5758,
    "geo_precision": "approximate_site",
    "current_access_status": "open",
    "visitor_summary_vi": "Lăng tẩm hoàng gia thanh bình nằm tựa lưng vào núi Thuận Đạo, được xây dựng theo di huấn giản dị, tiết kiệm ngân khố của vua Thiệu Trị. Kiến trúc kết hợp nét đăng đối của Lăng Gia Long và sự uy nghiêm của Lăng Minh Mạng, không có La thành bao quanh mà dùng các dãy đồi núi tự nhiên làm bình phong che chắn.",
    "visitor_summary_en": "An unadorned and serene royal tomb situated against the Thuận Đạo hills, built in just ten months in 1848 adhering to Emperor Thiệu Trị's testamentary wish for fiscal moderation and simplicity. Combines spatial axes from Gia Long Tomb and Minh Mạng Tomb without an artificial enclosing wall, utilizing natural hills as screens.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "678-011",
    "slug": "lang-khai-dinh",
    "name_vi": "Lăng Khải Định (Ứng Lăng)",
    "name_en": "Tomb of Khải Định (Ứng Tomb)",
    "entity_type": "site",
    "heritage_category": "royal_tomb",
    "parent_id": null,
    "official_reference_id": "678-011",
    "official_designation": "UNESCO World Heritage Property Component (678-011) / Di tích Quốc gia Đặc biệt",
    "period_label": "Triều Khải Định & Bảo Đại (Xây dựng kéo dài 11 năm, 1920–1931)",
    "historical_state": "standing",
    "location_lat": 16.3989,
    "location_lon": 107.5903,
    "geo_precision": "exact_gps",
    "current_access_status": "open",
    "visitor_summary_vi": "Công trình đỉnh cao của nghệ thuật ghép sành sứ và bê tông cốt thép đầu thế kỷ 20, vươn cao trên sườn núi Châu Chữ với 127 bậc tam cấp. Bên trong Điện Khải Thành là bức bích họa 'Cửu Long Ẩn Vân' trên trần điện do nghệ nhân Phan Văn Tánh thể hiện, cùng nghệ thuật khảm sành sứ rực rỡ và pho tượng đồng vua Khải Định đúc tại Pháp năm 1920.",
    "visitor_summary_en": "The zenith of early 20th-century porcelain mosaic art and reinforced concrete eclecticism, ascending the steep slopes of Châu Chữ mountain across 127 steps. Inside Khải Thành Palace, ceilings showcase master artisan Phan Văn Tánh's 'Nine Dragons Amidst Clouds' fresco, complemented by intricate porcelain mosaics and a gilded bronze statue cast in Paris.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": true,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "678-012",
    "slug": "lang-minh-mang",
    "name_vi": "Lăng Minh Mạng (Hiếu Lăng)",
    "name_en": "Tomb of Minh Mạng (Hiếu Tomb)",
    "entity_type": "site",
    "heritage_category": "royal_tomb",
    "parent_id": null,
    "official_reference_id": "678-012",
    "official_designation": "UNESCO World Heritage Property Component (678-012) / Di tích Quốc gia Đặc biệt",
    "period_label": "Triều Minh Mạng & Thiệu Trị (Quy hoạch 1840, xây dựng 1840–1843 thời Thiệu Trị)",
    "historical_state": "restored",
    "location_lat": 16.3889,
    "location_lon": 107.5714,
    "geo_precision": "exact_gps",
    "current_access_status": "open",
    "visitor_summary_vi": "Quần thể kiến trúc lăng tẩm đăng đối, uy nghiêm và chuẩn mực nhất triều Nguyễn, tọa lạc tại ngã ba Bằng Lãng nơi hai nhánh sông Tả Trạch và Hữu Trạch hợp thành dòng sông Hương. Toàn bộ gần 40 công trình lớn nhỏ được bố trí tuyệt đối đối xứng trên một trục Thần đạo dài 700m, xuyên qua hồ Trừng Minh, hồ Tân Nguyệt và Bửu Thành.",
    "visitor_summary_en": "The most rigorously symmetrical, monumental, and philosophically coherent royal tomb of the Nguyễn Dynasty, located at the confluence of the Tả Trạch and Hữu Trạch tributaries of the Perfume River. Nearly 40 architectural structures align strictly along a 700-meter central sacred axis (Thần đạo) crossing through lakes and the burial mound (Bửu Thành).",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": true,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "678-013",
    "slug": "lang-gia-long",
    "name_vi": "Lăng Gia Long (Thiên Thọ Lăng)",
    "name_en": "Tomb of Gia Long (Thiên Thọ Tomb)",
    "entity_type": "site",
    "heritage_category": "royal_tomb",
    "parent_id": null,
    "official_reference_id": "678-013",
    "official_designation": "UNESCO World Heritage Property Component (678-013) / Di tích Quốc gia Đặc biệt",
    "period_label": "Triều Gia Long (Khởi dựng 1814, hoàn thành 1820; lăng tẩm đầu tiên của các vua triều Nguyễn)",
    "historical_state": "restored",
    "location_lat": 16.3475,
    "location_lon": 107.5833,
    "geo_precision": "approximate_site",
    "current_access_status": "open",
    "visitor_summary_vi": "Quần thể lăng tẩm đầu tiên của các hoàng đế triều Nguyễn, trải rộng trên vùng cảnh quan thiên nhiên hùng vĩ của 42 đồi núi thuộc dãy Thiên Thọ. Điểm đặc sắc là ngôi mộ kép bằng đá song táng cạnh nhau của vua Gia Long và Thừa Thiên Cao Hoàng hậu, phản ánh tình nghĩa vợ chồng đồng cam cộng khổ qua bao năm chiến tranh dựng nghiệp.",
    "visitor_summary_en": "The foundational and most geographically expansive imperial tomb of the Nguyễn Dynasty, dispersed across 42 mountains in the Thiên Thọ range. Features twin stone crypts resting side by side beneath a natural pine canopy for Emperor Gia Long and Empress Thừa Thiên Cao, symbolizing their shared trials during dynastic civil wars.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "678-014",
    "slug": "tran-hai-thanh",
    "name_vi": "Trấn Hải Thành (Trấn Hải Đài / Đồn Thuận An)",
    "name_en": "Trấn Hải Fort (Thuận An Coastal Bastion / Trấn Hải Đài)",
    "entity_type": "monument",
    "heritage_category": "imperial_architecture",
    "parent_id": null,
    "official_reference_id": "678-014",
    "official_designation": "UNESCO World Heritage Property Component (678-014) / Di tích Lịch sử Quốc gia",
    "period_label": "Triều Gia Long & Minh Mạng (Khởi lập 1813 thời Gia Long; kiên cố hóa 1834 thời Minh Mạng)",
    "historical_state": "standing",
    "location_lat": 16.5742,
    "location_lon": 107.6539,
    "geo_precision": "exact_gps",
    "current_access_status": "restricted",
    "visitor_summary_vi": "Pháo đài quân sự ven biển trọng yếu kiểm soát toàn bộ cửa biển Thuận An và tuyến đường thủy huyết mạch vào Kinh đô Huế. Được đắp bằng gạch đá theo hình tròn chu vi 285 trượng (khoảng hơn 1.000m), xung quanh có hào nước bảo vệ sâu 1 trượng, là mắt xích tiền tiêu bảo vệ kinh kỳ dưới thời phong kiến.",
    "visitor_summary_en": "A vital circular coastal bastion guarding the strategic Thuận An sea estuary and the maritime entry channel into imperial Huế. Reconstructed in stone in 1834 with a perimeter exceeding 1,000 meters and a protective moat, serving as the frontline naval sentinel for the royal capital during the 19th century.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "CHILD-001",
    "slug": "ngo-mon",
    "name_vi": "Ngọ Môn",
    "name_en": "Meridian Gate (Ngọ Môn)",
    "entity_type": "monument",
    "heritage_category": "imperial_architecture",
    "parent_id": "kinh-thanh-hue",
    "official_reference_id": "678-001-NM",
    "official_designation": "Component Monument within UNESCO 678-001 / Di tích Quốc gia Đặc biệt",
    "period_label": "Triều Minh Mạng (Khởi công xây dựng năm Minh Mạng thứ 14, 1833)",
    "historical_state": "restored",
    "location_lat": 16.4678,
    "location_lon": 107.5781,
    "geo_precision": "exact_gps",
    "current_access_status": "open",
    "visitor_summary_vi": "Cổng chính phía nam của Hoàng thành Huế, công trình biểu tượng rực rỡ của kiến trúc cung đình triều Nguyễn. Phần dưới là nền đài chữ U bằng đá Thanh và gạch vồ trổ 5 lối đi (lối giữa dành riêng cho Hoàng đế); phần trên là Lầu Ngũ Phụng 2 tầng mái với 100 cây cột lim tượng trưng cho bách tính.",
    "visitor_summary_en": "The paramount southern portal to the Imperial City of Huế, completed in 1833. The massive U-shaped stone substructure features five vaulted gateways (the central passage reserved exclusively for the Emperor), topped by the two-story Belvidere of the Five Phoenixes (Lầu Ngũ Phụng) framed by 100 ironwood pillars.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": true,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "CHILD-002",
    "slug": "dien-thai-hoa",
    "name_vi": "Điện Thái Hòa",
    "name_en": "Hall of Supreme Harmony (Điện Thái Hòa)",
    "entity_type": "building",
    "heritage_category": "imperial_architecture",
    "parent_id": "kinh-thanh-hue",
    "official_reference_id": "678-001-DTH",
    "official_designation": "Component Monument within UNESCO 678-001 / Di tích Quốc gia Đặc biệt",
    "period_label": "Triều Gia Long & Minh Mạng (Dựng năm 1805, dời và tái lập năm 1833)",
    "historical_state": "restored",
    "location_lat": 16.4694,
    "location_lon": 107.5781,
    "geo_precision": "exact_gps",
    "current_access_status": "open",
    "visitor_summary_vi": "Cung điện quan trọng bậc nhất trong Hoàng thành Huế, nơi cử hành các đại lễ quốc gia như đăng quang, sinh nhật hoàng đế và đón tiếp sứ thần. Điện được xây dựng theo thức trùng thiềm điệp ốc (nhà kép nối nhau) với 80 cột gỗ lim sơn son thếp vàng chạm rồng, lưu giữ ngai vàng biểu tượng quyền uy vương triều.",
    "visitor_summary_en": "The grand ceremonial throne hall of the Nguyễn Dynasty, where coronation rites, royal birthdays, and imperial audiences occurred. Constructed in the classic double-roof timber pavilion style (trùng thiềm điệp ốc) supported by 80 lacquered and gilded ironwood columns framing the sacred Imperial Throne.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": true,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "CHILD-003",
    "slug": "the-mieu",
    "name_vi": "Thế Tổ Miếu (Thế Miếu)",
    "name_en": "Ancestral Temple (Thế Tổ Miếu)",
    "entity_type": "building",
    "heritage_category": "imperial_architecture",
    "parent_id": "kinh-thanh-hue",
    "official_reference_id": "678-001-TM",
    "official_designation": "Component Monument within UNESCO 678-001 / Di tích Quốc gia Đặc biệt",
    "period_label": "Triều Minh Mạng (Xây dựng năm Minh Mạng thứ 2, 1821; thờ các vua triều Nguyễn)",
    "historical_state": "standing",
    "location_lat": 16.4689,
    "location_lon": 107.5761,
    "geo_precision": "exact_gps",
    "current_access_status": "open",
    "visitor_summary_vi": "Miếu thờ tổ tiên hoàng tộc quan trọng nhất của triều Nguyễn, gồm tòa đại điện 9 gian 2 chái bằng gỗ lim sơn son thếp vàng tôn nghiêm. Trước sân Thế Miếu là nơi đặt bộ Cửu Đỉnh đúc năm 1835 và đối diện với lầu Hiển Lâm Các, tạo nên không gian tâm linh hoàng gia toàn vẹn bậc nhất Cố đô.",
    "visitor_summary_en": "The principal ancestral sanctuary of the Nguyễn Imperial Clan, featuring a nine-bay gilded timber temple enshrining royal altars. The courtyard before Thế Miếu holds the Nine Dynastic Urns cast in 1835, facing the elevated Hiển Lâm Các Pavilion across a sacred geometric plaza.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": true,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "CHILD-004",
    "slug": "hien-lam-cac",
    "name_vi": "Hiển Lâm Các",
    "name_en": "Pavilion of Benevolence (Hiển Lâm Các)",
    "entity_type": "building",
    "heritage_category": "imperial_architecture",
    "parent_id": "kinh-thanh-hue",
    "official_reference_id": "678-001-HLC",
    "official_designation": "Component Monument within UNESCO 678-001 / Di tích Quốc gia Đặc biệt",
    "period_label": "Triều Minh Mạng (Xây dựng năm 1821–1822)",
    "historical_state": "standing",
    "location_lat": 16.4686,
    "location_lon": 107.5761,
    "geo_precision": "exact_gps",
    "current_access_status": "open",
    "visitor_summary_vi": "Công trình kiến trúc gỗ cao nhất trong Hoàng thành Huế (17m), đóng vai trò đài kỷ niệm ghi công các đại thần công thần khai quốc và phò tá triều đình. Kiến trúc 3 tầng bằng gỗ lim thanh thoát với 12 mái lợp ngói liệt, tạo thế đối trọng cân xứng với Thế Miếu qua khoảng sân đặt Cửu Đỉnh.",
    "visitor_summary_en": "The tallest historical wooden structure inside the Imperial Citadel (17 meters), erected in 1821–1822 as a memorial pavilion honoring meritorious ministers and officials of the dynasty. Its three-tiered cedar-and-ironwood timber structure stands in direct architectural dialogue with Thế Miếu across the Urn plaza.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "CHILD-005",
    "slug": "dien-kien-trung",
    "name_vi": "Điện Kiến Trung",
    "name_en": "Kiến Trung Palace (Điện Kiến Trung)",
    "entity_type": "building",
    "heritage_category": "imperial_architecture",
    "parent_id": "kinh-thanh-hue",
    "official_reference_id": "678-001-DKT",
    "official_designation": "Component Monument within UNESCO 678-001 / Di tích Quốc gia Đặc biệt",
    "period_label": "Triều Khải Định & Bảo Đại (Xây dựng 1921–1923; phục dựng hoàn thành 2024)",
    "historical_state": "restored",
    "location_lat": 16.4736,
    "location_lon": 107.5786,
    "geo_precision": "exact_gps",
    "current_access_status": "open",
    "visitor_summary_vi": "Cung điện sinh hoạt và làm việc của hai vị hoàng đế cuối cùng triều Nguyễn (Khải Định và Bảo Đại), tọa lạc tại điểm cực bắc của trục Thần đạo Tử Cấm thành. Tòa điện kết hợp độc đáo giữa kiến trúc Phục Hưng Pháp, trường phái Art Deco và nghệ thuật khảm sành sứ cung đình Huế; bị phá hủy hoàn toàn năm 1947 và vừa phục dựng thành công năm 2024.",
    "visitor_summary_en": "The residential and private administrative palace of the final two monarchs (Khải Định and Bảo Đại), terminating the northern end of the Forbidden City's sacred axis. Merges French Renaissance and Art Deco geometry with Vietnamese ceramic mosaic art; meticulously reconstructed from archaeological foundations between 2019 and 2024.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "CHILD-006",
    "slug": "duyet-thi-duong",
    "name_vi": "Duyệt Thị Đường",
    "name_en": "Royal Theatre (Duyệt Thị Đường)",
    "entity_type": "building",
    "heritage_category": "imperial_architecture",
    "parent_id": "kinh-thanh-hue",
    "official_reference_id": "678-001-DTD",
    "official_designation": "Component Monument within UNESCO 678-001 / Di tích Quốc gia Đặc biệt",
    "period_label": "Triều Minh Mạng (Xây dựng năm Minh Mạng thứ 7, 1826)",
    "historical_state": "restored",
    "location_lat": 16.4714,
    "location_lon": 107.5806,
    "geo_precision": "exact_gps",
    "current_access_status": "open",
    "visitor_summary_vi": "Nhà hát hoàng gia cổ nhất còn tồn tại của Việt Nam, nơi vua, hoàng thân và quan lại thưởng thức các vở Tuồng cung đình và âm nhạc Nhã nhạc cổ điển. Trần nhà hát trang trí vòm trời với các vì tinh tú và nhật nguyệt, kết hợp hệ thống sân khấu nâng hạ và buồng phục trang chuyên nghiệp thời quân chủ.",
    "visitor_summary_en": "The oldest surviving royal theatrical auditorium in Vietnam, erected in 1826 for performances of Classical Court Opera (Tuồng) and UNESCO-inscribed Nhã nhạc court music. Features an iconic ceiling painted with astronomical constellations and cosmic symbols above an elevated imperial wooden stage.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "CRAFT-001",
    "slug": "duc-dong-phuong-duc",
    "name_vi": "Nghề đúc đồng truyền thống Phường Đúc",
    "name_en": "Phường Đúc Traditional Bronze Casting Craft Community",
    "entity_type": "community",
    "heritage_category": "craft_living_culture",
    "parent_id": null,
    "official_reference_id": "CRAFT-HUE-PD",
    "official_designation": "Di sản Văn hóa Phi vật thể Quốc gia / Làng nghề thủ công truyền thống Huế",
    "period_label": "Thời Chúa Nguyễn đến nay (Thế kỷ 17 – nay; dòng họ Nguyễn, Phan, Bùi)",
    "historical_state": "living_tradition",
    "location_lat": 16.4528,
    "location_lon": 107.5667,
    "geo_precision": "approximate_site",
    "current_access_status": "open",
    "visitor_summary_vi": "Cái nôi kỹ nghệ luyện kim đúc đồng lừng danh xứ Đàng Trong và Kinh đô Huế. Các nghệ nhân Phường Đúc (tiền thân là làng Dương Xuân / Giang Hến) là tác giả của các kiệt tác quốc gia: Đại Hồng Chung chùa Thiên Mụ (1710), Cửu Vị Thần Công (1803–1804), và Bảo vật quốc gia Cửu Đỉnh (1835–1837). Hiện các lò đúc gia truyền vẫn đỏ lửa lưu giữ kỹ thuật đúc sáp ong và khuôn đất sét độc đáo.",
    "visitor_summary_en": "The historic metallurgical crucible of central Vietnam and the royal capital. The master founders of Phường Đúc cast Vietnam's pinnacle bronze national treasures: the 1710 Thiên Mụ Bell, the Nine Holy Cannons (1803–1804), and the Nine Dynastic Urns (1835–1837). Today, multi-generational familial forges continue practicing ancient beeswax-clay lost-wax casting methods.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "CRAFT-002",
    "slug": "hoa-giay-thanh-tien",
    "name_vi": "Làng nghề hoa giấy truyền thống Thanh Tiên",
    "name_en": "Thanh Tiên Traditional Paper Flower Craft Village",
    "entity_type": "community",
    "heritage_category": "craft_living_culture",
    "parent_id": null,
    "official_reference_id": "CRAFT-HUE-TT",
    "official_designation": "Di sản Văn hóa Phi vật thể Quốc gia / Làng nghề truyền thống Thừa Thiên Huế",
    "period_label": "Thời Hậu Lê đến nay (Hơn 300 năm lịch sử; khởi phát từ thế kỷ 18)",
    "historical_state": "living_tradition",
    "location_lat": 16.5056,
    "location_lon": 107.625,
    "geo_precision": "approximate_site",
    "current_access_status": "open",
    "visitor_summary_vi": "Làng nghề thủ công dân gian độc đáo nằm ven hạ lưu sông Hương thuộc xã Phú Mậu. Nghề làm hoa giấy bắt nguồn từ tập tục thờ cúng gia tiên, am miếu và trang bà vào dịp Tết Nguyên Đán khi hoa tươi mùa đông xứ Huế khan hiếm. Nghệ nhân dùng tre chẻ nan, nhuộm màu tự nhiên từ lá cây, khoét cánh hoa sen, hoa cúc thanh tao trang nghiêm.",
    "visitor_summary_en": "A distinctive folk artisanal settlement along the lower reaches of the Perfume River in Phú Mậu commune. Developed over 300 years to provide vibrant ceremonial paper flowers (lotuses, chrysanthemums) for domestic and outdoor shrines during cold monsoon winters when fresh blossoms were scarce. Created using shaved bamboo, natural botanical dyes, and hand-chiseled petals.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "CRAFT-003",
    "slug": "kham-sanh-su-hue",
    "name_vi": "Nghệ thuật khảm sành sứ cung đình và dân gian Huế",
    "name_en": "Huế Imperial and Folk Porcelain Mosaic (Khảm Sành Sứ) Art Tradition",
    "entity_type": "community",
    "heritage_category": "craft_living_culture",
    "parent_id": null,
    "official_reference_id": "CRAFT-HUE-KSS",
    "official_designation": "Di sản Nghệ thuật Thủ công Truyền thống Huế",
    "period_label": "Thời Nguyễn (Thế kỷ 17 đến nay; bùng nổ cuối thế kỷ 19 – đầu thế kỷ 20)",
    "historical_state": "living_tradition",
    "location_lat": 16.46,
    "location_lon": 107.58,
    "geo_precision": "approximate_site",
    "current_access_status": "open",
    "visitor_summary_vi": "Nghệ thuật trang trí kiến trúc đặc sắc bậc nhất của xứ Huế, biến các mảnh vỡ bát đĩa sành sứ, chén chén men màu phế liệu thành những đồ án long phụng, hoa lá, câu đối lộng lẫy bền vững trước mưa nắng khắc nghiệt miền Trung. Đỉnh cao của nghệ thuật khảm sành sứ được lưu giữ tại Điện Khải Thành (Lăng Khải Định) và Điện Kiến Trung.",
    "visitor_summary_en": "A transcendent architectural decorative art native to Huế, transforming broken fragments of porcelain bowls, imported ceramics, and glazed pottery tiles into vivid dragon, phoenix, and floral mosaics capable of withstanding the tropical monsoon. Masterworks are exemplified across Khải Thành Palace (Ứng Tomb) and the newly restored Kiến Trung Palace.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  },
  {
    "id": "unesco-nha-nhac",
    "slug": "nha-nhac-cung-dinh-hue",
    "name_vi": "Nhã nhạc Cung đình Huế",
    "name_en": "Nhã Nhạc — Vietnamese Court Music",
    "entity_type": "intangible",
    "heritage_category": "music_performance",
    "parent_id": null,
    "official_reference_id": "UNESCO-ICH-00074",
    "official_designation": "Kiệt tác Di sản Phi vật thể và Truyền khẩu Nhân loại (UNESCO 2003)",
    "period_label": "Thời Lê sơ đến Triều Nguyễn (Thế kỷ XV – 1945)",
    "historical_state": "standing",
    "location_lat": 16.4705,
    "location_lon": 107.579,
    "geo_precision": "approximate_site",
    "current_access_status": "open",
    "visitor_summary_vi": "Nhã nhạc là hình thức âm nhạc cung đình bác học được trình diễn tại các đại lễ tế Giao, tế Miếu, đại triều và yến tiệc hoàng gia triều Nguyễn. Năm 2003, Nhã nhạc được UNESCO vinh danh là Di sản Phi vật thể đầu tiên của Việt Nam.",
    "visitor_summary_en": "Nhã Nhạc refers to the court music refined during the Nguyễn Dynasty, performed at imperial coronations, ancestral temple rituals, and official receptions. In 2003, it was inscribed by UNESCO as Vietnam's first Masterpiece of the Oral and Intangible Heritage of Humanity.",
    "editorial_status": "published",
    "content_scope": "RBPC_HUE",
    "has_3d": false,
    "thumbnail_url": null,
    "created_at": "2026-10-18T00:00:00Z",
    "updated_at": "2026-10-18T00:00:00Z"
  }
];
