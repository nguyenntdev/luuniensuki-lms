/**
 * GPS Coordinates and Geodetic Mapping Engine for Đại Nội Huế (Imperial City of Huế).
 * Authoritative coordinates for 16 primary monuments across the 4 royal spatial zones:
 * - Trục trung tâm (Central Ceremonial Axis)
 * - Không gian thờ tự (Ancestral Worship Space)
 * - Tử Cấm Thành (Purple Forbidden City)
 * - Không gian sinh hoạt (Royal Living and Gardens)
 *
 * Referenced to WGS84 datum (EPSG:4326).
 */

export interface MonumentGpsCoordinate {
  slug: string;
  name_vi: string;
  name_en: string;
  name_han_nom: string;
  lat: number;
  lng: number;
  zone_slug: string;
  zone_title_vi: string;
  google_place_query: string;
}

/**
 * Centroid of the Imperial City of Huế (Điện Thái Hòa / Kỳ Đài axis).
 */
export const HUE_IMPERIAL_CITY_CENTER = {
  lat: 16.4697,
  lng: 107.5786,
  zoom: 17,
  minZoom: 15,
  maxZoom: 20,
};

/**
 * Geodetic bounding box enclosing the entire Hoàng Thành and Tử Cấm Thành.
 */
export const HUE_IMPERIAL_CITY_BOUNDS = {
  north: 16.4755,
  south: 16.465,
  east: 107.583,
  west: 107.573,
};

/**
 * Authoritative GPS coordinates of the 16 primary monuments in Đại Nội Huế.
 */
export const MONUMENT_GPS_REGISTRY: Record<string, MonumentGpsCoordinate> = {
  "ngo-mon": {
    slug: "ngo-mon",
    name_vi: "Ngọ Môn",
    name_en: "Meridian Gate",
    name_han_nom: "午門",
    lat: 16.4678,
    lng: 107.5786,
    zone_slug: "central-ceremonial-axis",
    zone_title_vi: "Trục trung tâm",
    google_place_query: "Ngọ Môn Huế, Phú Hậu, Thành phố Huế, Thừa Thiên Huế",
  },
  "cau-trung-dao": {
    slug: "cau-trung-dao",
    name_vi: "Cầu Trung Đạo",
    name_en: "Trung Dao Bridge",
    name_han_nom: "中道橋",
    lat: 16.4688,
    lng: 107.5786,
    zone_slug: "central-ceremonial-axis",
    zone_title_vi: "Trục trung tâm",
    google_place_query: "Cầu Trung Đạo, Đại Nội Huế",
  },
  "san-dai-trieu-nghi": {
    slug: "san-dai-trieu-nghi",
    name_vi: "Sân Đại Triều Nghi",
    name_en: "Grand Court Esplanade",
    name_han_nom: "大朝儀丹墀",
    lat: 16.4693,
    lng: 107.5786,
    zone_slug: "central-ceremonial-axis",
    zone_title_vi: "Trục trung tâm",
    google_place_query: "Sân Đại Triều Nghi, Điện Thái Hòa, Đại Nội Huế",
  },
  "dien-thai-hoa": {
    slug: "dien-thai-hoa",
    name_vi: "Điện Thái Hòa",
    name_en: "Palace of Supreme Harmony",
    name_han_nom: "太和殿",
    lat: 16.4697,
    lng: 107.5786,
    zone_slug: "central-ceremonial-axis",
    zone_title_vi: "Trục trung tâm",
    google_place_query: "Điện Thái Hòa, Đại Nội Huế",
  },
  "the-to-mieu": {
    slug: "the-to-mieu",
    name_vi: "Thế Tổ Miếu",
    name_en: "The To Temple (The Mieu)",
    name_han_nom: "世祖廟",
    lat: 16.4685,
    lng: 107.5772,
    zone_slug: "ancestral-worship-space",
    zone_title_vi: "Không gian thờ tự",
    google_place_query: "Thế Miếu, Đại Nội Huế",
  },
  "hien-lam-cac": {
    slug: "hien-lam-cac",
    name_vi: "Hiển Lâm Các & Cửu Đỉnh",
    name_en: "Hien Lam Pavilion & Nine Dynastic Urns",
    name_han_nom: "顯臨閣",
    lat: 16.4687,
    lng: 107.5776,
    zone_slug: "ancestral-worship-space",
    zone_title_vi: "Không gian thờ tự",
    google_place_query: "Hiển Lâm Các, Thế Miếu, Đại Nội Huế",
  },
  "hung-to-mieu": {
    slug: "hung-to-mieu",
    name_vi: "Hưng Tổ Miếu",
    name_en: "Hung To Temple (Hung Mieu)",
    name_han_nom: "興祖廟",
    lat: 16.4692,
    lng: 107.5772,
    zone_slug: "ancestral-worship-space",
    zone_title_vi: "Không gian thờ tự",
    google_place_query: "Hưng Miếu, Đại Nội Huế",
  },
  "trieu-to-mieu": {
    slug: "trieu-to-mieu",
    name_vi: "Triệu Tổ Miếu",
    name_en: "Trieu To Temple (Trieu Mieu)",
    name_han_nom: "肇祖廟",
    lat: 16.4685,
    lng: 107.5802,
    zone_slug: "ancestral-worship-space",
    zone_title_vi: "Không gian thờ tự",
    google_place_query: "Triệu Miếu, Đại Nội Huế",
  },
  "dai-cung-mon": {
    slug: "dai-cung-mon",
    name_vi: "Đại Cung Môn",
    name_en: "Great Golden Gate",
    name_han_nom: "大宮門",
    lat: 16.4704,
    lng: 107.5786,
    zone_slug: "purple-forbidden-city",
    zone_title_vi: "Tử Cấm Thành",
    google_place_query: "Đại Cung Môn, Tử Cấm Thành Huế",
  },
  "dien-can-chanh": {
    slug: "dien-can-chanh",
    name_vi: "Điện Cần Chánh",
    name_en: "Can Chanh Palace",
    name_han_nom: "勤政殿",
    lat: 16.471,
    lng: 107.5786,
    zone_slug: "purple-forbidden-city",
    zone_title_vi: "Tử Cấm Thành",
    google_place_query: "Điện Cần Chánh, Tử Cấm Thành Huế",
  },
  "dien-kien-trung": {
    slug: "dien-kien-trung",
    name_vi: "Điện Kiến Trung",
    name_en: "Kien Trung Palace",
    name_han_nom: "建忠殿",
    lat: 16.4736,
    lng: 107.5786,
    zone_slug: "purple-forbidden-city",
    zone_title_vi: "Tử Cấm Thành",
    google_place_query: "Điện Kiến Trung, Tử Cấm Thành Huế",
  },
  "duyet-thi-duong": {
    slug: "duyet-thi-duong",
    name_vi: "Duyệt Thị Đường",
    name_en: "Duyet Thi Duong Royal Theater",
    name_han_nom: "閱是堂",
    lat: 16.4714,
    lng: 107.5798,
    zone_slug: "purple-forbidden-city",
    zone_title_vi: "Tử Cấm Thành",
    google_place_query: "Duyệt Thị Đường, Đại Nội Huế",
  },
  "thai-binh-lau": {
    slug: "thai-binh-lau",
    name_vi: "Thái Bình Lâu",
    name_en: "Thai Binh Royal Library",
    name_han_nom: "太平樓",
    lat: 16.4725,
    lng: 107.5796,
    zone_slug: "purple-forbidden-city",
    zone_title_vi: "Tử Cấm Thành",
    google_place_query: "Thái Bình Lâu, Tử Cấm Thành Huế",
  },
  "cung-dien-tho": {
    slug: "cung-dien-tho",
    name_vi: "Cung Diên Thọ",
    name_en: "Dien Tho Palace Complex",
    name_han_nom: "延壽宮",
    lat: 16.4714,
    lng: 107.576,
    zone_slug: "royal-living-gardens",
    zone_title_vi: "Không gian sinh hoạt",
    google_place_query: "Cung Diên Thọ, Đại Nội Huế",
  },
  "cung-truong-sanh": {
    slug: "cung-truong-sanh",
    name_vi: "Cung Trường Sanh",
    name_en: "Truong Sanh Palace & Gardens",
    name_han_nom: "長生宮",
    lat: 16.473,
    lng: 107.5756,
    zone_slug: "royal-living-gardens",
    zone_title_vi: "Không gian sinh hoạt",
    google_place_query: "Cung Trường Sanh, Đại Nội Huế",
  },
  "dien-phung-tien": {
    slug: "dien-phung-tien",
    name_vi: "Điện Phụng Tiên",
    name_en: "Phung Tien Palace",
    name_han_nom: "奉先殿",
    lat: 16.4702,
    lng: 107.5768,
    zone_slug: "ancestral-worship-space",
    zone_title_vi: "Không gian thờ tự",
    google_place_query: "Điện Phụng Tiên, Đại Nội Huế",
  },
};

/**
 * Returns GPS coordinates for a monument slug or defaults to Huế Citadel center.
 */
export function getMonumentGps(slug?: string | null): MonumentGpsCoordinate {
  if (slug && MONUMENT_GPS_REGISTRY[slug]) {
    return MONUMENT_GPS_REGISTRY[slug];
  }
  return {
    slug: "dai-noi-hue",
    name_vi: "Đại Nội Huế",
    name_en: "Imperial City of Huế",
    name_han_nom: "大內順化",
    lat: HUE_IMPERIAL_CITY_CENTER.lat,
    lng: HUE_IMPERIAL_CITY_CENTER.lng,
    zone_slug: "central-ceremonial-axis",
    zone_title_vi: "Quần thể Di tích Cố đô Huế",
    google_place_query: "Đại Nội Huế, Phú Hậu, Thành phố Huế, Thừa Thiên Huế",
  };
}

/**
 * Generates an external Google Maps search / navigation URL.
 */
export function getGoogleMapsUrl(lat: number, lng: number, label?: string): string {
  const q = label ? `${encodeURIComponent(label)}` : `${lat},${lng}`;
  return `https://www.google.com/maps/search/?api=1&query=${q}&query_place_id=${lat},${lng}`;
}

/**
 * Generates an external Google Maps Directions URL from visitor's current location to the monument.
 */
export function getGoogleMapsDirectionsUrl(lat: number, lng: number, label?: string): string {
  const dest = label ? `${encodeURIComponent(label)}` : `${lat},${lng}`;
  return `https://www.google.com/maps/dir/?api=1&destination=${dest}&destination_place_id=${lat},${lng}`;
}

/**
 * Generates an embeddable Google Maps URL with satellite / hybrid mode.
 */
export function getGoogleMapsEmbedUrl(
  lat: number,
  lng: number,
  zoom: number = 18,
): string {
  // Using Google Maps search embed format
  return `https://maps.google.com/maps?q=${lat},${lng}&t=k&z=${zoom}&ie=UTF8&iwloc=&output=embed`;
}
