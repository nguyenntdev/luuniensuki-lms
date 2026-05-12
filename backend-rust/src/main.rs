mod config;

use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine as _};
use hmac::{Hmac, Mac};
use serde_json::Value;
use sha2::Sha256;
use std::{
    io::{Read, Write},
    net::{TcpListener, TcpStream},
    thread,
    time::{Duration, SystemTime, UNIX_EPOCH},
};

use crate::config::Settings;

type HmacSha256 = Hmac<Sha256>;

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

fn verify_access_token(token: &str, secret: &str) -> Result<Value, &'static str> {
    let mut parts = token.split('.');
    let header = parts.next().ok_or("missing header")?;
    let payload = parts.next().ok_or("missing payload")?;
    let signature = parts.next().ok_or("missing signature")?;
    if parts.next().is_some() {
        return Err("too many parts");
    }

    let signed = format!("{header}.{payload}");
    let mut mac = HmacSha256::new_from_slice(secret.as_bytes()).map_err(|_| "bad secret")?;
    mac.update(signed.as_bytes());
    let expected = URL_SAFE_NO_PAD.encode(mac.finalize().into_bytes());
    if !constant_time_eq(expected.as_bytes(), signature.as_bytes()) {
        return Err("bad signature");
    }

    let payload_bytes = URL_SAFE_NO_PAD
        .decode(payload.as_bytes())
        .map_err(|_| "bad payload")?;
    let claims: Value = serde_json::from_slice(&payload_bytes).map_err(|_| "bad json")?;
    if claims.get("type").and_then(Value::as_str) != Some("access") {
        return Err("wrong token type");
    }

    let exp = claims
        .get("exp")
        .and_then(Value::as_i64)
        .ok_or("missing exp")?;
    if exp < unix_now() as i64 {
        return Err("expired");
    }

    Ok(claims)
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
        let ranks: Value = serde_json::from_str(ranks_json()).unwrap();

        assert_eq!(ranks.as_array().unwrap().len(), 10);
        assert_eq!(ranks[0]["level"], 1);
        assert_eq!(ranks[0]["xp"], 0);
    }

    fn test_token(secret: &str, exp: u64, token_type: &str) -> String {
        let header = URL_SAFE_NO_PAD.encode(r#"{"alg":"HS256","typ":"JWT"}"#);
        let payload = URL_SAFE_NO_PAD.encode(format!(
            r#"{{"sub":"00000000-0000-0000-0000-000000000000","type":"{token_type}","exp":{exp}}}"#
        ));
        let signed = format!("{header}.{payload}");
        let mut mac = HmacSha256::new_from_slice(secret.as_bytes()).unwrap();
        mac.update(signed.as_bytes());
        let signature = URL_SAFE_NO_PAD.encode(mac.finalize().into_bytes());
        format!("{signed}.{signature}")
    }
}
