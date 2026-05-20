//! Minimal PDF writer for trail certificates.
//!
//! Produces a single-page A4 PDF (Helvetica, no embedded fonts) containing
//! the recipient name, trail title, issued date, and the certificate hash.
//! Implemented from scratch to avoid pulling in a heavy external crate that
//! would push the build host past its memory budget. Output is a valid
//! PDF 1.4 document.
//!
//! Spec: `.kiro/specs/heritage-trail-mode/` (Requirement 5).
//!
//! The renderer is best-effort: if any I/O step fails, the caller logs and
//! the certificate row remains with `pdf_url = NULL`. A retry can be wired
//! later if needed.

use chrono::{DateTime, Utc};
use std::io::Write;
use std::path::{Path, PathBuf};

/// Render and write a certificate PDF to `<uploads_dir>/certificates/<hash>.pdf`.
///
/// Returns the public URL path on success, or `None` on any rendering or
/// I/O failure (errors are logged via `tracing`).
pub fn render_to_disk(
    uploads_dir: &Path,
    hash: &str,
    user_display_name: &str,
    trail_title: &str,
    issued_at: DateTime<Utc>,
) -> Option<String> {
    let dir = uploads_dir.join("certificates");
    if let Err(err) = std::fs::create_dir_all(&dir) {
        tracing::warn!(
            error = %err,
            dir = %dir.display(),
            "certificate dir create failed",
        );
        return None;
    }
    let path = dir.join(format!("{}.pdf", sanitize_hash(hash)));
    let bytes = render_pdf(user_display_name, trail_title, issued_at, hash);
    if let Err(err) = write_atomically(&path, &bytes) {
        tracing::warn!(
            error = %err,
            path = %path.display(),
            "certificate write failed",
        );
        return None;
    }
    Some(format!("/uploads/certificates/{}.pdf", sanitize_hash(hash)))
}

/// Strip anything that isn't 0-9a-f to keep the filename safe.
fn sanitize_hash(hash: &str) -> String {
    hash.chars()
        .filter(|c| c.is_ascii_hexdigit())
        .collect::<String>()
}

fn write_atomically(path: &Path, bytes: &[u8]) -> std::io::Result<()> {
    let mut tmp = PathBuf::from(path);
    tmp.set_extension("pdf.tmp");
    {
        let mut f = std::fs::File::create(&tmp)?;
        f.write_all(bytes)?;
        f.sync_all()?;
    }
    std::fs::rename(tmp, path)
}

/// Build the PDF byte stream.
///
/// Uses a single content stream with built-in Helvetica (no font embedding).
/// Lines are rendered using PDF text-positioning operators (`Tj` + `T*`) so
/// the document stays small (~2 KB).
///
/// Long strings are truncated to fit on one page; the certificate hash is
/// still rendered in full at small font size at the bottom.
fn render_pdf(
    name: &str,
    trail_title: &str,
    issued_at: DateTime<Utc>,
    hash: &str,
) -> Vec<u8> {
    // Approximate character budgets at each font size on an A4 595pt page
    // with 110pt left margin. Helvetica width is ~0.5 * size for ASCII.
    // Page usable width = 595 - 110 - 50 = 435pt.
    //   22pt -> 435 / (22*0.5) ~= 39 chars
    //   16pt -> 435 / (16*0.5) ~= 54 chars
    let name_safe = truncate_with_ellipsis(name, 39);
    let title_safe = truncate_with_ellipsis(trail_title, 54);

    // Build the content stream first.
    let issued = issued_at.format("%d/%m/%Y").to_string();
    let lines: [(&str, u32); 5] = [
        ("CHUNG CHI HOAN THANH", 32),
        ("Luu Nien Su Ki LMS", 14),
        (name_safe.as_str(), 22),
        (title_safe.as_str(), 16),
        ("", 12),
    ];

    let mut content = String::new();
    content.push_str("BT\n");
    // First line at (110, 720)
    content.push_str("/F1 32 Tf\n1 0 0 1 110 720 Tm\n");
    content.push_str(&format!("({}) Tj\n", escape_pdf_string(lines[0].0)));
    // Subtitle
    content.push_str("0 -40 Td\n/F1 14 Tf\n");
    content.push_str(&format!("({}) Tj\n", escape_pdf_string(lines[1].0)));
    // Recipient
    content.push_str("0 -80 Td\n/F1 22 Tf\n");
    content.push_str(&format!("({}) Tj\n", escape_pdf_string(lines[2].0)));
    // Trail title
    content.push_str("0 -50 Td\n/F1 16 Tf\n");
    content.push_str(&format!("({}) Tj\n", escape_pdf_string(lines[3].0)));
    // Issued date
    content.push_str("0 -60 Td\n/F1 12 Tf\n");
    content.push_str(&format!(
        "(Cap ngay {}) Tj\n",
        escape_pdf_string(&issued),
    ));
    // Hash
    content.push_str("0 -180 Td\n/F1 8 Tf\n");
    content.push_str(&format!(
        "(Ma xac thuc: {}) Tj\n",
        escape_pdf_string(hash),
    ));
    content.push_str("ET\n");

    let content_bytes = content.into_bytes();

    // Now assemble the PDF.
    let mut buf: Vec<u8> = Vec::with_capacity(2048);
    let mut offsets: Vec<usize> = Vec::with_capacity(5);

    buf.extend_from_slice(b"%PDF-1.4\n%\xC2\xA5\xC2\xB1\xC3\xAB\n");

    // Object 1: Catalog
    offsets.push(buf.len());
    buf.extend_from_slice(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n");

    // Object 2: Pages
    offsets.push(buf.len());
    buf.extend_from_slice(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n");

    // Object 3: Page
    offsets.push(buf.len());
    buf.extend_from_slice(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] \
          /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>\nendobj\n",
    );

    // Object 4: Contents
    offsets.push(buf.len());
    buf.extend_from_slice(format!("4 0 obj\n<< /Length {} >>\nstream\n", content_bytes.len()).as_bytes());
    buf.extend_from_slice(&content_bytes);
    buf.extend_from_slice(b"\nendstream\nendobj\n");

    // Object 5: Font
    offsets.push(buf.len());
    buf.extend_from_slice(
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\nendobj\n",
    );

    // xref
    let xref_offset = buf.len();
    buf.extend_from_slice(b"xref\n");
    buf.extend_from_slice(format!("0 {}\n", offsets.len() + 1).as_bytes());
    buf.extend_from_slice(b"0000000000 65535 f \n");
    for off in &offsets {
        buf.extend_from_slice(format!("{:010} 00000 n \n", off).as_bytes());
    }

    // trailer
    buf.extend_from_slice(b"trailer\n");
    buf.extend_from_slice(
        format!("<< /Size {} /Root 1 0 R >>\n", offsets.len() + 1).as_bytes(),
    );
    buf.extend_from_slice(b"startxref\n");
    buf.extend_from_slice(format!("{}\n", xref_offset).as_bytes());
    buf.extend_from_slice(b"%%EOF\n");

    buf
}

/// Escape characters that have special meaning inside a PDF string literal.
/// Also drops any byte > 0x7E (built-in Helvetica + WinAnsi can't represent
/// the full Vietnamese codepoint range without font embedding). Vietnamese
/// diacritics are dropped here; the on-screen UI keeps full Unicode while
/// the PDF is a verifiable artifact carrying ASCII-safe copy.
fn escape_pdf_string(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    for c in s.chars() {
        let mapped = strip_diacritics(c);
        match mapped {
            '(' => out.push_str("\\("),
            ')' => out.push_str("\\)"),
            '\\' => out.push_str("\\\\"),
            '\r' => out.push_str("\\r"),
            '\n' => out.push_str("\\n"),
            ch if (ch as u32) >= 0x20 && (ch as u32) <= 0x7E => out.push(ch),
            _ => out.push('?'),
        }
    }
    out
}

/// Truncate `s` to at most `max_chars` characters, appending `…` when the
/// input is too long. Operates on chars (not bytes) so multibyte input is
/// handled before the diacritic strip runs.
fn truncate_with_ellipsis(s: &str, max_chars: usize) -> String {
    if max_chars == 0 {
        return String::new();
    }
    let count = s.chars().count();
    if count <= max_chars {
        return s.to_string();
    }
    let take = max_chars.saturating_sub(1);
    let mut out: String = s.chars().take(take).collect();
    out.push('.');
    out
}

fn strip_diacritics(c: char) -> char {
    // A small Vietnamese-aware fold to ASCII. Anything we can't map falls
    // through and gets replaced with '?' downstream.
    match c {
        'à' | 'á' | 'ả' | 'ã' | 'ạ' | 'ă' | 'ằ' | 'ắ' | 'ẳ' | 'ẵ' | 'ặ'
        | 'â' | 'ầ' | 'ấ' | 'ẩ' | 'ẫ' | 'ậ' => 'a',
        'À' | 'Á' | 'Ả' | 'Ã' | 'Ạ' | 'Ă' | 'Ằ' | 'Ắ' | 'Ẳ' | 'Ẵ' | 'Ặ'
        | 'Â' | 'Ầ' | 'Ấ' | 'Ẩ' | 'Ẫ' | 'Ậ' => 'A',
        'è' | 'é' | 'ẻ' | 'ẽ' | 'ẹ' | 'ê' | 'ề' | 'ế' | 'ể' | 'ễ' | 'ệ' => 'e',
        'È' | 'É' | 'Ẻ' | 'Ẽ' | 'Ẹ' | 'Ê' | 'Ề' | 'Ế' | 'Ể' | 'Ễ' | 'Ệ' => 'E',
        'ì' | 'í' | 'ỉ' | 'ĩ' | 'ị' => 'i',
        'Ì' | 'Í' | 'Ỉ' | 'Ĩ' | 'Ị' => 'I',
        'ò' | 'ó' | 'ỏ' | 'õ' | 'ọ' | 'ô' | 'ồ' | 'ố' | 'ổ' | 'ỗ' | 'ộ'
        | 'ơ' | 'ờ' | 'ớ' | 'ở' | 'ỡ' | 'ợ' => 'o',
        'Ò' | 'Ó' | 'Ỏ' | 'Õ' | 'Ọ' | 'Ô' | 'Ồ' | 'Ố' | 'Ổ' | 'Ỗ' | 'Ộ'
        | 'Ơ' | 'Ờ' | 'Ớ' | 'Ở' | 'Ỡ' | 'Ợ' => 'O',
        'ù' | 'ú' | 'ủ' | 'ũ' | 'ụ' | 'ư' | 'ừ' | 'ứ' | 'ử' | 'ữ' | 'ự' => 'u',
        'Ù' | 'Ú' | 'Ủ' | 'Ũ' | 'Ụ' | 'Ư' | 'Ừ' | 'Ứ' | 'Ử' | 'Ữ' | 'Ự' => 'U',
        'ỳ' | 'ý' | 'ỷ' | 'ỹ' | 'ỵ' => 'y',
        'Ỳ' | 'Ý' | 'Ỷ' | 'Ỹ' | 'Ỵ' => 'Y',
        'đ' => 'd',
        'Đ' => 'D',
        other => other,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pdf_starts_with_header_and_ends_with_eof() {
        let pdf = render_pdf(
            "Nguyen Van A",
            "Linh vat Cao Dinh",
            Utc::now(),
            "abc123",
        );
        assert!(pdf.starts_with(b"%PDF-1.4"));
        let trailing = String::from_utf8_lossy(&pdf[pdf.len().saturating_sub(8)..]);
        assert!(trailing.contains("%%EOF"));
    }

    #[test]
    fn pdf_contains_supplied_strings_after_diacritic_strip() {
        let pdf = render_pdf("Nguyễn Văn A", "Linh vật Cao Đỉnh", Utc::now(), "abc");
        let text = String::from_utf8_lossy(&pdf);
        assert!(text.contains("Nguyen Van A"), "expected ASCII-folded name");
        assert!(text.contains("Linh vat Cao Dinh"), "expected ASCII-folded title");
        assert!(text.contains("abc"));
    }

    #[test]
    fn diacritic_strip_handles_common_vn_chars() {
        assert_eq!(strip_diacritics('đ'), 'd');
        assert_eq!(strip_diacritics('Đ'), 'D');
        assert_eq!(strip_diacritics('ư'), 'u');
        assert_eq!(strip_diacritics('ố'), 'o');
        assert_eq!(strip_diacritics('A'), 'A');
    }

    #[test]
    fn sanitize_hash_drops_non_hex() {
        assert_eq!(sanitize_hash("ab/cd"), "abcd");
        assert_eq!(sanitize_hash("DEAD-BEEF"), "DEADBEEF");
    }

    #[test]
    fn escape_pdf_string_escapes_parens_and_backslash() {
        assert_eq!(escape_pdf_string("foo (bar) \\baz"), "foo \\(bar\\) \\\\baz");
    }

    #[test]
    fn truncate_keeps_short_strings() {
        assert_eq!(truncate_with_ellipsis("short", 10), "short");
        assert_eq!(truncate_with_ellipsis("", 10), "");
    }

    #[test]
    fn truncate_clips_long_strings() {
        let out = truncate_with_ellipsis("aaaaaaaaaaaaaaaaa", 5);
        assert_eq!(out.chars().count(), 5);
        assert!(out.ends_with('.'));
    }

    #[test]
    fn truncate_handles_unicode() {
        let s = "Linh vật Cao Đỉnh — chuyến hành trình dài lê thê qua các thời đại Nguyễn";
        let out = truncate_with_ellipsis(s, 20);
        assert_eq!(out.chars().count(), 20);
    }
}
