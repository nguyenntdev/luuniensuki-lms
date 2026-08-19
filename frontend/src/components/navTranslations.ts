// Navbar i18n source of truth (security-hardening Req 22).
//
// Extracted from the navbar component so the translation tables and the pure
// lookup function can be unit-tested directly (Property 10: Roundtrip i18n)
// without importing the React component (and its client-only deps) into the
// Node-environment Vitest runner.
//
// Contract:
//   - `translations` holds one table per supported language. The `en` strings
//     are real English, distinct from the Vietnamese `vi` strings (Req 22.1).
//   - The tables are separate and non-duplicated (Req 22.3).
//   - `translate(lang, key)` resolves safely: a missing key (or unknown lang)
//     falls back to the key itself rather than throwing (Req 22.2).

export type NavLang = "vi" | "en";

export const translations: Record<string, Record<string, string>> = {
  vi: {
    "nav.dashboard": "Học tập",
    "nav.explore": "Khám phá",
    "nav.cuu-dinh": "Cửu Đỉnh",
    "nav.atlas": "Atlas 162",
    "nav.sources": "Nguồn",
    "nav.map": "Bản đồ",
    "nav.timeline": "Dòng thời gian",
    "nav.stories": "Câu chuyện",
    "nav.network": "Mạng lưới",
    "nav.compare": "So sánh",
    "nav.vr360": "360°",
    "nav.home": "Trang chủ",
    "nav.study": "Học",
    "nav.learn-now": "Bắt đầu học",
    "nav.login": "Đăng nhập",
    "nav.about-sources": "Về nguồn tư liệu",
    "nav.quests": "Hành trình",
    "nav.collection": "Bộ sưu tập",
    "nav.practice": "Ôn tập",
    "nav.ai": "AI giáo viên",
    "nav.friends": "Bạn bè",
    "nav.achievements": "Thành tích",
    "nav.profile": "Hồ sơ",
    "nav.admin": "Giáo viên",
    "nav.leaderboard": "Bảng hạng",
    "nav.leagues": "Liên đoàn",
    "nav.menu": "Mục lục",
    "nav.logout": "Đăng xuất",
    "nav.start": "Tiếp tục học",
  },
  en: {
    "nav.dashboard": "Learn",
    "nav.explore": "Explore",
    "nav.cuu-dinh": "Nine Urns",
    "nav.atlas": "Atlas of 162 reliefs",
    "nav.sources": "Sources",
    "nav.map": "Map",
    "nav.timeline": "Timeline",
    "nav.stories": "Stories",
    "nav.network": "Connections",
    "nav.compare": "Compare",
    "nav.vr360": "360° tour",
    "nav.home": "Home",
    "nav.study": "Learn",
    "nav.learn-now": "Start learning",
    "nav.login": "Log in",
    "nav.about-sources": "About the sources",
    "nav.quests": "Journey",
    "nav.collection": "Collection",
    "nav.practice": "Practice",
    "nav.ai": "AI Teacher",
    "nav.friends": "Friends",
    "nav.achievements": "Achievements",
    "nav.profile": "Profile",
    "nav.admin": "Teacher",
    "nav.leaderboard": "Leaderboard",
    "nav.leagues": "Leagues",
    "nav.menu": "Menu",
    "nav.logout": "Log out",
    "nav.start": "Continue learning",
  },
};

// Pure translation lookup: `translations[lang]?.[key] ?? key`.
// Never throws — an unknown language or missing key resolves to the key.
export function translate(lang: string | undefined, key: string): string {
  return translations[lang ?? ""]?.[key] ?? key;
}
