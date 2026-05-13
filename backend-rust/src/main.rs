mod config;
mod pg;

use std::{
    io::{Read, Write},
    net::{TcpListener, TcpStream},
    thread,
    time::{Duration, SystemTime, UNIX_EPOCH},
};

use crate::config::Settings;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let settings = Settings::from_env();
    let listener = TcpListener::bind(settings.bind_addr)?;

    println!("starting {} on {}", settings.app_name, settings.bind_addr);
    for stream in listener.incoming() {
        let settings = settings.clone();
        match stream {
            Ok(stream) => {
                thread::spawn(move || {
                    if let Err(error) = handle_connection(stream, settings) {
                        eprintln!("request failed: {error}");
                    }
                });
            }
            Err(error) => eprintln!("connection failed: {error}"),
        }
    }

    Ok(())
}

fn handle_connection(
    mut stream: TcpStream,
    settings: Settings,
) -> Result<(), Box<dyn std::error::Error>> {
    stream.set_read_timeout(Some(Duration::from_secs(180)))?;
    stream.set_write_timeout(Some(Duration::from_secs(180)))?;

    let request = read_http_message(&mut stream)?;
    let request_text = String::from_utf8_lossy(&request);

    if request_text.starts_with("GET /health ") {
        write_json(
            &mut stream,
            "200 OK",
            &format!(
                r#"{{"status":"ok","service":"{}","mode":"gateway"}}"#,
                json_escape(&settings.app_name)
            ),
        )?;
    } else if request_text.starts_with("GET /api/v1/internal/db-health ") {
        write_db_health(&mut stream, &settings)?;
    } else if request_text.starts_with("GET /api/v1/content/ratings ") {
        write_json(&mut stream, "200 OK", content_ratings_json())?;
    } else if request_text.starts_with("GET /api/v1/ranks ") {
        match extract_auth_token(&request_text)
            .and_then(|token| verify_access_token(token, &settings.jwt_secret_key).ok())
        {
            Some(_) => write_json(&mut stream, "200 OK", ranks_json())?,
            None => write_unauthorized(&mut stream)?,
        }
    } else if should_short_circuit_unauthenticated(&request_text) {
        write_unauthorized(&mut stream)?;
    } else {
        proxy_to_legacy(&mut stream, &request, &settings)?;
    }

    Ok(())
}

fn write_json(stream: &mut TcpStream, status: &str, body: &str) -> std::io::Result<()> {
    let response = format!(
        "HTTP/1.1 {status}\r\ncontent-type: application/json\r\ncontent-length: {}\r\nconnection: close\r\n\r\n{body}",
        body.len()
    );
    stream.write_all(response.as_bytes())?;
    stream.flush()
}

fn write_unauthorized(stream: &mut TcpStream) -> std::io::Result<()> {
    let body = r#"{"error":{"code":"HTTP_ERROR","message":"Could not validate credentials","details":{}}}"#;
    let response = format!(
        "HTTP/1.1 401 Unauthorized\r\ncontent-type: application/json\r\ncontent-length: {}\r\nwww-authenticate: Bearer\r\nconnection: close\r\n\r\n{body}",
        body.len()
    );
    stream.write_all(response.as_bytes())?;
    stream.flush()
}

fn write_db_health(stream: &mut TcpStream, settings: &Settings) -> std::io::Result<()> {
    match check_database(&settings.database_url) {
        Ok(()) => write_json(stream, "200 OK", db_health_json("ok")),
        Err(error) => {
            eprintln!("database health check failed: {error}");
            write_json(stream, "503 Service Unavailable", db_health_json("error"))
        }
    }
}

fn check_database(database_url: &str) -> Result<(), Box<dyn std::error::Error>> {
    pg::check_select_one(database_url)
}

fn proxy_to_legacy(
    client: &mut TcpStream,
    request: &[u8],
    settings: &Settings,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut upstream =
        TcpStream::connect((settings.legacy_api_host.as_str(), settings.legacy_api_port))?;
    upstream.set_read_timeout(Some(Duration::from_secs(180)))?;
    upstream.set_write_timeout(Some(Duration::from_secs(180)))?;

    let request =
        normalize_proxy_request(request, &settings.legacy_api_host, settings.legacy_api_port);
    upstream.write_all(&request)?;
    upstream.flush()?;

    let mut buffer = [0; 16 * 1024];
    loop {
        let bytes_read = upstream.read(&mut buffer)?;
        if bytes_read == 0 {
            break;
        }
        client.write_all(&buffer[..bytes_read])?;
    }
    client.flush()?;

    Ok(())
}

fn read_http_message(stream: &mut TcpStream) -> std::io::Result<Vec<u8>> {
    let mut request = Vec::with_capacity(4096);
    let mut buffer = [0; 4096];
    let mut header_end = None;
    let mut content_length = 0usize;

    loop {
        let bytes_read = stream.read(&mut buffer)?;
        if bytes_read == 0 {
            break;
        }
        request.extend_from_slice(&buffer[..bytes_read]);

        if header_end.is_none() {
            header_end = find_header_end(&request);
            if let Some(end) = header_end {
                content_length = parse_content_length(&request[..end]).unwrap_or(0);
            }
        }

        if let Some(end) = header_end {
            let body_start = end + 4;
            if request.len().saturating_sub(body_start) >= content_length {
                break;
            }
        }
    }

    Ok(request)
}

fn normalize_proxy_request(request: &[u8], upstream_host: &str, upstream_port: u16) -> Vec<u8> {
    let text = String::from_utf8_lossy(request);
    let Some(header_end) = text.find("\r\n\r\n") else {
        return request.to_vec();
    };

    let (headers, body) = text.split_at(header_end);
    let mut lines = headers.lines();
    let Some(request_line) = lines.next() else {
        return request.to_vec();
    };

    let mut normalized = String::with_capacity(headers.len() + body.len() + 64);
    normalized.push_str(request_line);
    normalized.push_str("\r\n");

    let mut saw_connection = false;
    for line in lines {
        let lower = line.to_ascii_lowercase();
        if lower.starts_with("connection:") {
            normalized.push_str("connection: close\r\n");
            saw_connection = true;
        } else if lower.starts_with("host:") {
            normalized.push_str(&format!("host: {upstream_host}:{upstream_port}\r\n"));
        } else {
            normalized.push_str(line);
            normalized.push_str("\r\n");
        }
    }

    if !saw_connection {
        normalized.push_str("connection: close\r\n");
    }
    normalized.push_str("\r\n");
    normalized.push_str(&body[4..]);

    normalized.into_bytes()
}

fn find_header_end(buffer: &[u8]) -> Option<usize> {
    buffer.windows(4).position(|window| window == b"\r\n\r\n")
}

fn parse_content_length(headers: &[u8]) -> Option<usize> {
    let text = String::from_utf8_lossy(headers);
    text.lines().find_map(|line| {
        let (name, value) = line.split_once(':')?;
        if name.eq_ignore_ascii_case("content-length") {
            value.trim().parse::<usize>().ok()
        } else {
            None
        }
    })
}

fn should_short_circuit_unauthenticated(request: &str) -> bool {
    let Some(path) = request_path(request) else {
        return false;
    };

    is_native_auth_guard_path(path) && !has_auth_token(request)
}

fn request_path(request: &str) -> Option<&str> {
    let first_line = request.lines().next()?;
    let mut parts = first_line.split_whitespace();
    let _method = parts.next()?;
    let raw_path = parts.next()?;
    Some(raw_path.split('?').next().unwrap_or(raw_path))
}

fn is_native_auth_guard_path(path: &str) -> bool {
    matches!(
        path,
        "/api/v1/auth/me"
            | "/api/v1/ranks"
            | "/api/v1/badges"
            | "/api/v1/urns"
            | "/api/v1/dashboard/summary"
            | "/api/v1/users/me/collection"
            | "/api/v1/users/me/badges"
            | "/api/v1/users/me/streak"
    )
}

fn has_auth_token(request: &str) -> bool {
    extract_auth_token(request).is_some()
}

fn extract_auth_token(request: &str) -> Option<&str> {
    request.lines().find_map(|line| {
        let lower = line.to_ascii_lowercase();
        if lower.starts_with("authorization: bearer ") {
            return line.split_once("Bearer ").map(|(_, token)| token.trim());
        }
        if lower.starts_with("cookie:") {
            return line
                .split_once(':')
                .and_then(|(_, cookies)| find_cookie(cookies, "luuniensuki_access"));
        }
        None
    })
}

fn find_cookie<'a>(cookies: &'a str, name: &str) -> Option<&'a str> {
    cookies.split(';').find_map(|cookie| {
        let (key, value) = cookie.trim().split_once('=')?;
        if key == name {
            Some(value.trim())
        } else {
            None
        }
    })
}

fn verify_access_token(token: &str, secret: &str) -> Result<String, &'static str> {
    let mut parts = token.split('.');
    let header = parts.next().ok_or("missing header")?;
    let payload = parts.next().ok_or("missing payload")?;
    let signature = parts.next().ok_or("missing signature")?;
    if parts.next().is_some() {
        return Err("too many parts");
    }

    let signed = format!("{header}.{payload}");
    let expected = base64_url_encode(&hmac_sha256(secret.as_bytes(), signed.as_bytes()));
    if !constant_time_eq(expected.as_bytes(), signature.as_bytes()) {
        return Err("bad signature");
    }

    let payload_bytes = base64_url_decode(payload)?;
    let claims = String::from_utf8(payload_bytes).map_err(|_| "bad json")?;
    if json_string_field(&claims, "type") != Some("access") {
        return Err("wrong token type");
    }

    let exp = json_i64_field(&claims, "exp").ok_or("missing exp")?;
    if exp < unix_now() as i64 {
        return Err("expired");
    }

    Ok(claims)
}

fn json_string_field<'a>(json: &'a str, field: &str) -> Option<&'a str> {
    let needle = format!("\"{field}\":\"");
    let start = json.find(&needle)? + needle.len();
    let rest = &json[start..];
    let end = rest.find('"')?;
    Some(&rest[..end])
}

fn json_i64_field(json: &str, field: &str) -> Option<i64> {
    let needle = format!("\"{field}\":");
    let start = json.find(&needle)? + needle.len();
    let rest = json[start..].trim_start();
    let end = rest
        .find(|ch: char| !ch.is_ascii_digit() && ch != '-')
        .unwrap_or(rest.len());
    rest[..end].parse().ok()
}

fn base64_url_decode(input: &str) -> Result<Vec<u8>, &'static str> {
    let mut normalized = input.replace('-', "+").replace('_', "/");
    while normalized.len() % 4 != 0 {
        normalized.push('=');
    }
    base64_decode(&normalized)
}

fn base64_decode(input: &str) -> Result<Vec<u8>, &'static str> {
    let mut out = Vec::with_capacity(input.len() * 3 / 4);
    let mut chunk = [0u8; 4];
    let mut chunk_len = 0usize;

    for byte in input.bytes() {
        let value = match byte {
            b'A'..=b'Z' => byte - b'A',
            b'a'..=b'z' => byte - b'a' + 26,
            b'0'..=b'9' => byte - b'0' + 52,
            b'+' => 62,
            b'/' => 63,
            b'=' => 64,
            b'\r' | b'\n' | b' ' => continue,
            _ => return Err("bad base64"),
        };
        chunk[chunk_len] = value;
        chunk_len += 1;
        if chunk_len == 4 {
            out.push((chunk[0] << 2) | (chunk[1] >> 4));
            if chunk[2] != 64 {
                out.push((chunk[1] << 4) | (chunk[2] >> 2));
            }
            if chunk[3] != 64 {
                out.push((chunk[2] << 6) | chunk[3]);
            }
            chunk_len = 0;
        }
    }

    if chunk_len != 0 {
        Err("bad base64 length")
    } else {
        Ok(out)
    }
}

fn base64_url_encode(bytes: &[u8]) -> String {
    const TABLE: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
    let mut out = String::with_capacity(bytes.len().div_ceil(3) * 4);
    for chunk in bytes.chunks(3) {
        let b0 = chunk[0];
        let b1 = *chunk.get(1).unwrap_or(&0);
        let b2 = *chunk.get(2).unwrap_or(&0);
        out.push(TABLE[(b0 >> 2) as usize] as char);
        out.push(TABLE[(((b0 & 0b0000_0011) << 4) | (b1 >> 4)) as usize] as char);
        if chunk.len() > 1 {
            out.push(TABLE[(((b1 & 0b0000_1111) << 2) | (b2 >> 6)) as usize] as char);
        }
        if chunk.len() > 2 {
            out.push(TABLE[(b2 & 0b0011_1111) as usize] as char);
        }
    }
    out
}

fn hmac_sha256(key: &[u8], message: &[u8]) -> [u8; 32] {
    let mut normalized_key = if key.len() > 64 {
        sha256(key).to_vec()
    } else {
        key.to_vec()
    };
    normalized_key.resize(64, 0);

    let mut outer = [0x5c; 64];
    let mut inner = [0x36; 64];
    for (index, byte) in normalized_key.iter().enumerate() {
        outer[index] ^= byte;
        inner[index] ^= byte;
    }

    let mut inner_message = Vec::with_capacity(64 + message.len());
    inner_message.extend_from_slice(&inner);
    inner_message.extend_from_slice(message);
    let inner_hash = sha256(&inner_message);

    let mut outer_message = Vec::with_capacity(96);
    outer_message.extend_from_slice(&outer);
    outer_message.extend_from_slice(&inner_hash);
    sha256(&outer_message)
}

fn sha256(input: &[u8]) -> [u8; 32] {
    const K: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
        0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
        0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
        0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
        0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
        0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
        0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
        0xc67178f2,
    ];
    let mut h = [
        0x6a09e667u32,
        0xbb67ae85,
        0x3c6ef372,
        0xa54ff53a,
        0x510e527f,
        0x9b05688c,
        0x1f83d9ab,
        0x5be0cd19,
    ];

    let bit_len = (input.len() as u64) * 8;
    let mut message = input.to_vec();
    message.push(0x80);
    while (message.len() + 8) % 64 != 0 {
        message.push(0);
    }
    message.extend_from_slice(&bit_len.to_be_bytes());

    for block in message.chunks(64) {
        let mut w = [0u32; 64];
        for (index, word) in w.iter_mut().take(16).enumerate() {
            let start = index * 4;
            *word = u32::from_be_bytes([
                block[start],
                block[start + 1],
                block[start + 2],
                block[start + 3],
            ]);
        }
        for index in 16..64 {
            let s0 = w[index - 15].rotate_right(7)
                ^ w[index - 15].rotate_right(18)
                ^ (w[index - 15] >> 3);
            let s1 = w[index - 2].rotate_right(17)
                ^ w[index - 2].rotate_right(19)
                ^ (w[index - 2] >> 10);
            w[index] = w[index - 16]
                .wrapping_add(s0)
                .wrapping_add(w[index - 7])
                .wrapping_add(s1);
        }

        let mut a = h[0];
        let mut b = h[1];
        let mut c = h[2];
        let mut d = h[3];
        let mut e = h[4];
        let mut f = h[5];
        let mut g = h[6];
        let mut hh = h[7];

        for index in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let temp1 = hh
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(K[index])
                .wrapping_add(w[index]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = s0.wrapping_add(maj);

            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(temp1);
            d = c;
            c = b;
            b = a;
            a = temp1.wrapping_add(temp2);
        }

        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
        h[5] = h[5].wrapping_add(f);
        h[6] = h[6].wrapping_add(g);
        h[7] = h[7].wrapping_add(hh);
    }

    let mut out = [0u8; 32];
    for (index, word) in h.iter().enumerate() {
        out[index * 4..index * 4 + 4].copy_from_slice(&word.to_be_bytes());
    }
    out
}

fn constant_time_eq(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut diff = 0u8;
    for (left, right) in a.iter().zip(b.iter()) {
        diff |= left ^ right;
    }
    diff == 0
}

fn unix_now() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

fn ranks_json() -> &'static str {
    r#"[{"level":1,"name":"Lính Mới","xp":0},{"level":2,"name":"Thư Sinh","xp":500},{"level":3,"name":"Tú Tài","xp":1500},{"level":4,"name":"Cử Nhân","xp":3500},{"level":5,"name":"Tiến Sĩ","xp":7000},{"level":6,"name":"Thám Hoa","xp":12000},{"level":7,"name":"Bảng Nhãn","xp":20000},{"level":8,"name":"Trạng Nguyên","xp":35000},{"level":9,"name":"Hàn Lâm","xp":55000},{"level":10,"name":"Sử Quan","xp":80000}]"#
}

fn content_ratings_json() -> &'static str {
    r#"{"ratings":[{"rating":"everyone","label":"Everyone","description":"Suitable for all ages","min_age":null},{"rating":"teen","label":"Teen","description":"Suitable for ages 13 and up","min_age":13},{"rating":"mature","label":"Mature","description":"Suitable for ages 18 and up","min_age":18}]}"#
}

fn db_health_json(status: &str) -> &'static str {
    match status {
        "ok" => r#"{"status":"ok","database":"ok"}"#,
        _ => r#"{"status":"error","database":"error"}"#,
    }
}

fn json_escape(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn json_escape_handles_quotes() {
        assert_eq!(json_escape(r#"a"b"#), r#"a\"b"#);
    }

    #[test]
    fn parse_content_length_is_case_insensitive() {
        assert_eq!(
            parse_content_length(b"Host: x\r\nContent-Length: 42"),
            Some(42)
        );
    }

    #[test]
    fn normalize_proxy_request_closes_connection() {
        let request = b"GET /api/v1/urns HTTP/1.1\r\nHost: lms.histolab.icu\r\n\r\n";
        let normalized = String::from_utf8(normalize_proxy_request(request, "api", 8000)).unwrap();

        assert!(normalized.contains("host: api:8000\r\n"));
        assert!(normalized.contains("connection: close\r\n"));
    }

    #[test]
    fn request_path_ignores_query_string() {
        let request = "GET /api/v1/urns?page=1 HTTP/1.1\r\n\r\n";

        assert_eq!(request_path(request), Some("/api/v1/urns"));
    }

    #[test]
    fn auth_guard_short_circuits_missing_token() {
        let request = "GET /api/v1/badges HTTP/1.1\r\nHost: lms.histolab.icu\r\n\r\n";

        assert!(should_short_circuit_unauthenticated(request));
    }

    #[test]
    fn auth_guard_allows_bearer_token() {
        let request = "GET /api/v1/badges HTTP/1.1\r\nAuthorization: Bearer abc\r\n\r\n";

        assert!(!should_short_circuit_unauthenticated(request));
    }

    #[test]
    fn auth_guard_allows_access_cookie() {
        let request = "GET /api/v1/badges HTTP/1.1\r\nCookie: luuniensuki_access=abc\r\n\r\n";

        assert!(!should_short_circuit_unauthenticated(request));
    }

    #[test]
    fn auth_guard_ignores_unlisted_path() {
        let request = "GET /api/v1/auth/login HTTP/1.1\r\n\r\n";

        assert!(!should_short_circuit_unauthenticated(request));
    }

    #[test]
    fn extract_auth_token_reads_cookie() {
        let request = "GET / HTTP/1.1\r\nCookie: other=1; luuniensuki_access=abc.def.sig\r\n\r\n";

        assert_eq!(extract_auth_token(request), Some("abc.def.sig"));
    }

    #[test]
    fn verify_access_token_accepts_valid_hs256() {
        let token = test_token("secret", unix_now() + 60, "access");

        assert!(verify_access_token(&token, "secret").is_ok());
    }

    #[test]
    fn verify_access_token_rejects_wrong_secret() {
        let token = test_token("secret", unix_now() + 60, "access");

        assert!(verify_access_token(&token, "wrong").is_err());
    }

    #[test]
    fn verify_access_token_rejects_refresh_token() {
        let token = test_token("secret", unix_now() + 60, "refresh");

        assert!(verify_access_token(&token, "secret").is_err());
    }

    #[test]
    fn ranks_json_matches_shape() {
        assert!(ranks_json().contains(r#""level":1"#));
        assert!(ranks_json().contains(r#""xp":80000"#));
    }

    #[test]
    fn content_ratings_json_matches_shape() {
        assert!(content_ratings_json().contains(r#""ratings":["#));
        assert!(content_ratings_json().contains(r#""rating":"everyone""#));
        assert!(content_ratings_json().contains(r#""min_age":13"#));
        assert!(content_ratings_json().contains(r#""min_age":null"#));
    }

    #[test]
    fn db_health_json_matches_shape() {
        assert_eq!(db_health_json("ok"), r#"{"status":"ok","database":"ok"}"#);
        assert_eq!(
            db_health_json("error"),
            r#"{"status":"error","database":"error"}"#
        );
    }

    fn test_token(secret: &str, exp: u64, token_type: &str) -> String {
        let header = base64_url_encode(r#"{"alg":"HS256","typ":"JWT"}"#.as_bytes());
        let payload = base64_url_encode(
            format!(
                r#"{{"sub":"00000000-0000-0000-0000-000000000000","type":"{token_type}","exp":{exp}}}"#
            )
            .as_bytes(),
        );
        let signed = format!("{header}.{payload}");
        let signature = base64_url_encode(&hmac_sha256(secret.as_bytes(), signed.as_bytes()));
        format!("{signed}.{signature}")
    }

    #[test]
    fn sha256_known_vector() {
        assert_eq!(
            base64_url_encode(&sha256(b"abc")),
            "ungWv48Bz-pBQUDeXa4iI7ADYaOWF3qctBD_YfIAFa0"
        );
    }
}
