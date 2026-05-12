mod config;

use std::{
    io::{Read, Write},
    net::{TcpListener, TcpStream},
    thread,
    time::Duration,
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

fn proxy_to_legacy(
    client: &mut TcpStream,
    request: &[u8],
    settings: &Settings,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut upstream = TcpStream::connect(settings.legacy_api_addr)?;
    upstream.set_read_timeout(Some(Duration::from_secs(180)))?;
    upstream.set_write_timeout(Some(Duration::from_secs(180)))?;

    let request = normalize_proxy_request(request);
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

fn normalize_proxy_request(request: &[u8]) -> Vec<u8> {
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
            normalized.push_str("host: api:8000\r\n");
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
        let normalized = String::from_utf8(normalize_proxy_request(request)).unwrap();

        assert!(normalized.contains("host: api:8000\r\n"));
        assert!(normalized.contains("connection: close\r\n"));
    }
}
