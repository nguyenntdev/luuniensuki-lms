mod config;

use std::{
    io::{Read, Write},
    net::{TcpListener, TcpStream},
    thread,
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
    let mut buffer = [0; 1024];
    let bytes_read = stream.read(&mut buffer)?;
    let request = String::from_utf8_lossy(&buffer[..bytes_read]);

    let (status, body) = if request.starts_with("GET /health ") {
        (
            "200 OK",
            format!(
                r#"{{"status":"ok","service":"{}"}}"#,
                json_escape(&settings.app_name)
            ),
        )
    } else {
        (
            "404 Not Found",
            r#"{"error":{"code":"not_found","message":"not found"}}"#.to_string(),
        )
    };

    let response = format!(
        "HTTP/1.1 {status}\r\ncontent-type: application/json\r\ncontent-length: {}\r\nconnection: close\r\n\r\n{body}",
        body.len()
    );
    stream.write_all(response.as_bytes())?;
    stream.flush()?;

    Ok(())
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
}
