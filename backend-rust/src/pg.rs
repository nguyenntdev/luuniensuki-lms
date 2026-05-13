use std::{
    io::{Read, Write},
    net::{TcpStream, ToSocketAddrs},
    time::{Duration, SystemTime, UNIX_EPOCH},
};

use crate::{base64_decode, hmac_sha256, sha256};

#[derive(Debug, PartialEq)]
struct DatabaseUrl {
    user: String,
    password: String,
    host: String,
    port: u16,
    database: String,
}

pub fn check_select_one(database_url: &str) -> Result<(), Box<dyn std::error::Error>> {
    let config = parse_database_url(database_url).ok_or("bad database url")?;
    let mut stream = connect(&config)?;
    startup(&mut stream, &config)?;
    let rows = simple_query(&mut stream, "SELECT 1::INT")?;
    if rows
        .first()
        .and_then(|row| row.first())
        .and_then(|value| value.as_deref())
        == Some("1")
    {
        Ok(())
    } else {
        Err("database health query returned no row".into())
    }
}

pub fn tags_json(
    database_url: &str,
    tag_type: Option<&str>,
) -> Result<String, Box<dyn std::error::Error>> {
    let config = parse_database_url(database_url).ok_or("bad database url")?;
    let mut stream = connect(&config)?;
    startup(&mut stream, &config)?;
    let mut query = String::from(
        "SELECT id::text, slug, name, tag_type, description, is_active::text, \
         to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"+00:00\"') \
         FROM tags WHERE is_active = true",
    );
    if let Some(tag_type) = tag_type {
        query.push_str(" AND tag_type = '");
        query.push_str(&sql_string_escape(tag_type));
        query.push('\'');
    }
    query.push_str(" ORDER BY name");
    let rows = simple_query(&mut stream, &query)?;
    Ok(tags_rows_json(&rows))
}

pub fn badges_json(database_url: &str) -> Result<String, Box<dyn std::error::Error>> {
    let config = parse_database_url(database_url).ok_or("bad database url")?;
    let mut stream = connect(&config)?;
    startup(&mut stream, &config)?;
    let rows = simple_query(
        &mut stream,
        "SELECT id::text, slug, name, name_en, description, icon_url, category::text, \
         COALESCE(xp_bonus, 0)::text \
         FROM badges WHERE is_active = true AND is_secret = false",
    )?;
    Ok(badges_rows_json(&rows))
}

fn connect(config: &DatabaseUrl) -> Result<TcpStream, Box<dyn std::error::Error>> {
    let mut addrs = (config.host.as_str(), config.port).to_socket_addrs()?;
    let addr = addrs.next().ok_or("database host unresolved")?;
    let stream = TcpStream::connect_timeout(&addr, Duration::from_secs(2))?;
    stream.set_read_timeout(Some(Duration::from_secs(3)))?;
    stream.set_write_timeout(Some(Duration::from_secs(3)))?;
    Ok(stream)
}

fn startup(stream: &mut TcpStream, config: &DatabaseUrl) -> Result<(), Box<dyn std::error::Error>> {
    let mut body = Vec::new();
    body.extend_from_slice(&196608i32.to_be_bytes());
    push_cstr(&mut body, "user");
    push_cstr(&mut body, &config.user);
    push_cstr(&mut body, "database");
    push_cstr(&mut body, &config.database);
    push_cstr(&mut body, "client_encoding");
    push_cstr(&mut body, "UTF8");
    body.push(0);
    write_startup_message(stream, &body)?;

    let mut scram = None;
    loop {
        let message = read_message(stream)?;
        match message.tag {
            b'R' => {
                let code = read_i32(&message.body, 0)?;
                match code {
                    0 => {}
                    3 => send_password_message(stream, &config.password)?,
                    10 => {
                        if !sasl_mechanisms(&message.body[4..])
                            .iter()
                            .any(|item| item == "SCRAM-SHA-256")
                        {
                            return Err("server does not support SCRAM-SHA-256".into());
                        }
                        let client_nonce = client_nonce(&config.user, &config.database);
                        let client_first_bare = format!("n={},r={client_nonce}", config.user);
                        let client_first = format!("n,,{client_first_bare}");
                        send_sasl_initial_response(stream, "SCRAM-SHA-256", &client_first)?;
                        scram = Some(ScramState {
                            client_first_bare,
                            client_nonce,
                        });
                    }
                    11 => {
                        let state = scram.as_ref().ok_or("missing scram state")?;
                        let server_first = std::str::from_utf8(&message.body[4..])?;
                        let response = build_scram_client_final(
                            &config.password,
                            &state.client_first_bare,
                            &state.client_nonce,
                            server_first,
                        )?;
                        send_sasl_response(stream, &response.client_final)?;
                        scram = Some(ScramState {
                            client_first_bare: response.expected_server_signature,
                            client_nonce: String::new(),
                        });
                    }
                    12 => {
                        let state = scram.as_ref().ok_or("missing scram final state")?;
                        let server_final = std::str::from_utf8(&message.body[4..])?;
                        let signature =
                            scram_field(server_final, "v").ok_or("missing server signature")?;
                        if signature != state.client_first_bare {
                            return Err("bad server signature".into());
                        }
                    }
                    _ => return Err(format!("unsupported auth code {code}").into()),
                }
            }
            b'S' | b'K' => {}
            b'Z' => return Ok(()),
            b'E' => return Err(format!("postgres error: {}", error_message(&message.body)).into()),
            _ => {}
        }
    }
}

fn tags_rows_json(rows: &[Vec<Option<String>>]) -> String {
    let mut out = String::from("[");
    for (index, row) in rows.iter().enumerate() {
        if index > 0 {
            out.push(',');
        }
        let id = row_value(row, 0);
        let slug = row_value(row, 1);
        let name = row_value(row, 2);
        let tag_type = row_value(row, 3);
        let description = row.get(4).and_then(|value| value.as_deref());
        let is_active = row_value(row, 5) == "true";
        let created_at = row_value(row, 6);
        out.push_str("{\"id\":\"");
        out.push_str(&json_escape(id));
        out.push_str("\",\"slug\":\"");
        out.push_str(&json_escape(slug));
        out.push_str("\",\"name\":\"");
        out.push_str(&json_escape(name));
        out.push_str("\",\"tag_type\":\"");
        out.push_str(&json_escape(tag_type));
        out.push_str("\",\"description\":");
        match description {
            Some(value) => {
                out.push('"');
                out.push_str(&json_escape(value));
                out.push('"');
            }
            None => out.push_str("null"),
        }
        out.push_str(",\"is_active\":");
        out.push_str(if is_active { "true" } else { "false" });
        out.push_str(",\"created_at\":\"");
        out.push_str(&json_escape(created_at));
        out.push_str("\"}");
    }
    out.push(']');
    out
}

fn badges_rows_json(rows: &[Vec<Option<String>>]) -> String {
    let mut out = String::from("[");
    for (index, row) in rows.iter().enumerate() {
        if index > 0 {
            out.push(',');
        }
        out.push_str("{\"id\":\"");
        out.push_str(&json_escape(row_value(row, 0)));
        out.push_str("\",\"slug\":\"");
        out.push_str(&json_escape(row_value(row, 1)));
        out.push_str("\",\"name\":\"");
        out.push_str(&json_escape(row_value(row, 2)));
        out.push_str("\",\"name_en\":");
        push_json_nullable_string(&mut out, row.get(3).and_then(|value| value.as_deref()));
        out.push_str(",\"description\":");
        push_json_nullable_string(&mut out, row.get(4).and_then(|value| value.as_deref()));
        out.push_str(",\"icon_url\":\"");
        out.push_str(&json_escape(row_value(row, 5)));
        out.push_str("\",\"category\":\"");
        out.push_str(&json_escape(row_value(row, 6)));
        out.push_str("\",\"xp_bonus\":");
        out.push_str(row_value(row, 7).parse::<i64>().unwrap_or(0).to_string().as_str());
        out.push('}');
    }
    out.push(']');
    out
}

fn push_json_nullable_string(out: &mut String, value: Option<&str>) {
    match value {
        Some(value) => {
            out.push('"');
            out.push_str(&json_escape(value));
            out.push('"');
        }
        None => out.push_str("null"),
    }
}

fn row_value(row: &[Option<String>], index: usize) -> &str {
    row.get(index)
        .and_then(|value| value.as_deref())
        .unwrap_or("")
}

fn sql_string_escape(value: &str) -> String {
    value.replace('\'', "''")
}

fn json_escape(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"")
}

fn simple_query(
    stream: &mut TcpStream,
    query: &str,
) -> Result<Vec<Vec<Option<String>>>, Box<dyn std::error::Error>> {
    let mut body = query.as_bytes().to_vec();
    body.push(0);
    write_typed_message(stream, b'Q', &body)?;

    let mut rows = Vec::new();
    loop {
        let message = read_message(stream)?;
        match message.tag {
            b'D' => rows.push(data_row_values(&message.body)?),
            b'C' => {}
            b'Z' => return Ok(rows),
            b'E' => return Err(format!("postgres error: {}", error_message(&message.body)).into()),
            _ => {}
        }
    }
}

fn data_row_values(body: &[u8]) -> Result<Vec<Option<String>>, Box<dyn std::error::Error>> {
    if body.len() < 2 {
        return Err("short data row".into());
    }
    let columns = i16::from_be_bytes(body[0..2].try_into()?);
    if columns < 0 {
        return Err("bad data row column count".into());
    }
    let mut values = Vec::with_capacity(columns as usize);
    let mut offset = 2usize;
    for _ in 0..columns {
        let end = offset + 4;
        let length_bytes = body.get(offset..end).ok_or("short data row value length")?;
        let length = i32::from_be_bytes(length_bytes.try_into()?);
        offset = end;
        if length < 0 {
            values.push(None);
            continue;
        }
        let value_end = offset + length as usize;
        let value = body.get(offset..value_end).ok_or("short data row value")?;
        values.push(Some(std::str::from_utf8(value)?.to_string()));
        offset = value_end;
    }
    Ok(values)
}

struct ScramState {
    client_first_bare: String,
    client_nonce: String,
}

struct ScramFinal {
    client_final: String,
    expected_server_signature: String,
}

fn build_scram_client_final(
    password: &str,
    client_first_bare: &str,
    client_nonce: &str,
    server_first: &str,
) -> Result<ScramFinal, Box<dyn std::error::Error>> {
    let server_nonce = scram_field(server_first, "r").ok_or("missing nonce")?;
    if !server_nonce.starts_with(client_nonce) {
        return Err("bad server nonce".into());
    }
    let salt = base64_decode(scram_field(server_first, "s").ok_or("missing salt")?)?;
    let iterations: u32 = scram_field(server_first, "i")
        .ok_or("missing iterations")?
        .parse()?;
    if iterations == 0 {
        return Err("bad iterations".into());
    }

    let client_final_without_proof = format!("c=biws,r={server_nonce}");
    let auth_message = format!("{client_first_bare},{server_first},{client_final_without_proof}");
    let salted_password = pbkdf2_hmac_sha256(password.as_bytes(), &salt, iterations);
    let client_key = hmac_sha256(&salted_password, b"Client Key");
    let stored_key = sha256(&client_key);
    let client_signature = hmac_sha256(&stored_key, auth_message.as_bytes());
    let mut client_proof = [0u8; 32];
    for index in 0..client_proof.len() {
        client_proof[index] = client_key[index] ^ client_signature[index];
    }

    let server_key = hmac_sha256(&salted_password, b"Server Key");
    let server_signature = hmac_sha256(&server_key, auth_message.as_bytes());
    Ok(ScramFinal {
        client_final: format!(
            "{client_final_without_proof},p={}",
            base64_standard_encode(&client_proof)
        ),
        expected_server_signature: base64_standard_encode(&server_signature),
    })
}

fn pbkdf2_hmac_sha256(password: &[u8], salt: &[u8], iterations: u32) -> [u8; 32] {
    let mut first = Vec::with_capacity(salt.len() + 4);
    first.extend_from_slice(salt);
    first.extend_from_slice(&1u32.to_be_bytes());
    let mut u = hmac_sha256(password, &first);
    let mut out = u;
    for _ in 1..iterations {
        u = hmac_sha256(password, &u);
        for index in 0..out.len() {
            out[index] ^= u[index];
        }
    }
    out
}

fn parse_database_url(database_url: &str) -> Option<DatabaseUrl> {
    let after_scheme = database_url.split_once("://")?.1;
    let (auth, rest) = after_scheme.rsplit_once('@')?;
    let (user, password) = auth.split_once(':')?;
    let host_port = rest.split(['/', '?']).next()?;
    let database = rest.split_once('/')?.1.split('?').next()?.to_string();
    let (host, port) = host_port.rsplit_once(':')?;
    Some(DatabaseUrl {
        user: percent_decode(user),
        password: percent_decode(password),
        host: host.to_string(),
        port: port.parse().ok()?,
        database,
    })
}

fn percent_decode(value: &str) -> String {
    let bytes = value.as_bytes();
    let mut out = Vec::with_capacity(bytes.len());
    let mut index = 0;
    while index < bytes.len() {
        if bytes[index] == b'%' && index + 2 < bytes.len() {
            if let Ok(hex) = u8::from_str_radix(&value[index + 1..index + 3], 16) {
                out.push(hex);
                index += 3;
                continue;
            }
        }
        out.push(bytes[index]);
        index += 1;
    }
    String::from_utf8_lossy(&out).to_string()
}

fn client_nonce(user: &str, database: &str) -> String {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    let seed = format!("{user}:{database}:{now}");
    base64_standard_encode(&sha256(seed.as_bytes())).replace('=', "")
}

struct PgMessage {
    tag: u8,
    body: Vec<u8>,
}

fn read_message(stream: &mut TcpStream) -> Result<PgMessage, Box<dyn std::error::Error>> {
    let mut tag = [0u8; 1];
    stream.read_exact(&mut tag)?;
    let mut length = [0u8; 4];
    stream.read_exact(&mut length)?;
    let length = i32::from_be_bytes(length);
    if length < 4 {
        return Err("bad postgres message length".into());
    }
    let mut body = vec![0u8; (length - 4) as usize];
    stream.read_exact(&mut body)?;
    Ok(PgMessage { tag: tag[0], body })
}

fn write_startup_message(stream: &mut TcpStream, body: &[u8]) -> std::io::Result<()> {
    let length = (body.len() + 4) as i32;
    stream.write_all(&length.to_be_bytes())?;
    stream.write_all(body)?;
    stream.flush()
}

fn write_typed_message(stream: &mut TcpStream, tag: u8, body: &[u8]) -> std::io::Result<()> {
    let length = (body.len() + 4) as i32;
    stream.write_all(&[tag])?;
    stream.write_all(&length.to_be_bytes())?;
    stream.write_all(body)?;
    stream.flush()
}

fn send_password_message(stream: &mut TcpStream, password: &str) -> std::io::Result<()> {
    let mut body = password.as_bytes().to_vec();
    body.push(0);
    write_typed_message(stream, b'p', &body)
}

fn send_sasl_initial_response(
    stream: &mut TcpStream,
    mechanism: &str,
    message: &str,
) -> std::io::Result<()> {
    let mut body = Vec::new();
    push_cstr(&mut body, mechanism);
    body.extend_from_slice(&(message.len() as i32).to_be_bytes());
    body.extend_from_slice(message.as_bytes());
    write_typed_message(stream, b'p', &body)
}

fn send_sasl_response(stream: &mut TcpStream, message: &str) -> std::io::Result<()> {
    write_typed_message(stream, b'p', message.as_bytes())
}

fn push_cstr(buffer: &mut Vec<u8>, value: &str) {
    buffer.extend_from_slice(value.as_bytes());
    buffer.push(0);
}

fn read_i32(buffer: &[u8], offset: usize) -> Result<i32, Box<dyn std::error::Error>> {
    let bytes = buffer
        .get(offset..offset + 4)
        .ok_or("short postgres i32")?
        .try_into()?;
    Ok(i32::from_be_bytes(bytes))
}

fn sasl_mechanisms(body: &[u8]) -> Vec<String> {
    body.split(|byte| *byte == 0)
        .filter(|part| !part.is_empty())
        .filter_map(|part| std::str::from_utf8(part).ok())
        .map(ToString::to_string)
        .collect()
}

fn scram_field<'a>(message: &'a str, key: &str) -> Option<&'a str> {
    let prefix = format!("{key}=");
    message
        .split(',')
        .find_map(|part| part.strip_prefix(&prefix))
}

fn error_message(body: &[u8]) -> String {
    let mut index = 0;
    while index < body.len() {
        let field = body[index];
        index += 1;
        if field == 0 {
            break;
        }
        let start = index;
        while index < body.len() && body[index] != 0 {
            index += 1;
        }
        if field == b'M' {
            return String::from_utf8_lossy(&body[start..index]).to_string();
        }
        index += 1;
    }
    "unknown".to_string()
}

fn base64_standard_encode(bytes: &[u8]) -> String {
    const TABLE: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::with_capacity(bytes.len().div_ceil(3) * 4);
    for chunk in bytes.chunks(3) {
        let b0 = chunk[0];
        let b1 = *chunk.get(1).unwrap_or(&0);
        let b2 = *chunk.get(2).unwrap_or(&0);
        out.push(TABLE[(b0 >> 2) as usize] as char);
        out.push(TABLE[(((b0 & 0b0000_0011) << 4) | (b1 >> 4)) as usize] as char);
        if chunk.len() > 1 {
            out.push(TABLE[(((b1 & 0b0000_1111) << 2) | (b2 >> 6)) as usize] as char);
        } else {
            out.push('=');
        }
        if chunk.len() > 2 {
            out.push(TABLE[(b2 & 0b0011_1111) as usize] as char);
        } else {
            out.push('=');
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_database_url_reads_parts() {
        assert_eq!(
            parse_database_url("postgres://user:pass@db:5432/luuniensuki"),
            Some(DatabaseUrl {
                user: "user".to_string(),
                password: "pass".to_string(),
                host: "db".to_string(),
                port: 5432,
                database: "luuniensuki".to_string()
            })
        );
    }

    #[test]
    fn percent_decode_handles_credentials() {
        assert_eq!(percent_decode("user%40x"), "user@x");
        assert_eq!(percent_decode("p%3Ass"), "p:ss");
    }

    #[test]
    fn pbkdf2_hmac_sha256_matches_scram_vector() {
        assert_eq!(
            base64_standard_encode(&pbkdf2_hmac_sha256(b"pencil", b"salt", 4096)),
            "CZdWTykpIycTEmmAN7awoGqL5/vZEkgIR8WhrOS40cc="
        );
    }

    #[test]
    fn scram_client_final_matches_rfc_vector() {
        let result = build_scram_client_final(
            "pencil",
            "n=user,r=fyko+d2lbbFgONRv9qkxdawL",
            "fyko+d2lbbFgONRv9qkxdawL",
            "r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,s=QSXCR+Q6sek8bf92,i=4096",
        )
        .unwrap();
        assert_eq!(
            result.client_final,
            "c=biws,r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,p=qQRLRHGPDGjB+7iVAE7NNi5xEoHKHuLCHPNQ8BTmvds="
        );
        assert_eq!(
            result.expected_server_signature,
            "XKW6VuW1FANROQabnJBz1KaeCnQL/HZByQtX/iU+o30="
        );
    }

    #[test]
    fn data_row_values_reads_text_values() {
        let mut body = Vec::new();
        body.extend_from_slice(&2i16.to_be_bytes());
        body.extend_from_slice(&1i32.to_be_bytes());
        body.extend_from_slice(b"1");
        body.extend_from_slice(&(-1i32).to_be_bytes());
        assert_eq!(
            data_row_values(&body).unwrap(),
            vec![Some("1".to_string()), None]
        );
    }

    #[test]
    fn tags_rows_json_matches_shape() {
        let rows = vec![vec![
            Some("00000000-0000-0000-0000-000000000001".to_string()),
            Some("bronze".to_string()),
            Some("Bronze".to_string()),
            Some("topic".to_string()),
            None,
            Some("true".to_string()),
            Some("2026-05-13T00:00:00.000000+00:00".to_string()),
        ]];
        assert_eq!(
            tags_rows_json(&rows),
            r#"[{"id":"00000000-0000-0000-0000-000000000001","slug":"bronze","name":"Bronze","tag_type":"topic","description":null,"is_active":true,"created_at":"2026-05-13T00:00:00.000000+00:00"}]"#
        );
    }

    #[test]
    fn badges_rows_json_matches_shape() {
        let rows = vec![vec![
            Some("00000000-0000-0000-0000-000000000001".to_string()),
            Some("first-discovery".to_string()),
            Some("Lan dau kham pha".to_string()),
            None,
            Some("Mo khoa mot hoa van".to_string()),
            Some("/assets/badges/first-discovery.svg".to_string()),
            Some("discovery".to_string()),
            Some("50".to_string()),
        ]];
        assert_eq!(
            badges_rows_json(&rows),
            r#"[{"id":"00000000-0000-0000-0000-000000000001","slug":"first-discovery","name":"Lan dau kham pha","name_en":null,"description":"Mo khoa mot hoa van","icon_url":"/assets/badges/first-discovery.svg","category":"discovery","xp_bonus":50}]"#
        );
    }

    #[test]
    fn sql_string_escape_doubles_quotes() {
        assert_eq!(sql_string_escape("a'b"), "a''b");
    }
}
