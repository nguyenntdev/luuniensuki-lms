use std::net::{IpAddr, Ipv4Addr, SocketAddr};

#[derive(Clone, Debug)]
pub struct Settings {
    pub bind_addr: SocketAddr,
    pub app_name: String,
    pub legacy_api_host: String,
    pub legacy_api_port: u16,
    pub database_url: String,
    pub jwt_secret_key: String,
}

impl Settings {
    pub fn from_env() -> Self {
        let host = std::env::var("API_HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
        let port = std::env::var("API_PORT")
            .ok()
            .and_then(|value| value.parse::<u16>().ok())
            .unwrap_or(8001);
        let ip = host
            .parse::<IpAddr>()
            .unwrap_or(IpAddr::V4(Ipv4Addr::UNSPECIFIED));
        let legacy_host = std::env::var("LEGACY_API_HOST").unwrap_or_else(|_| "api".to_string());
        let legacy_port = std::env::var("LEGACY_API_PORT")
            .ok()
            .and_then(|value| value.parse::<u16>().ok())
            .unwrap_or(8000);

        Self {
            bind_addr: SocketAddr::new(ip, port),
            app_name: "luuniensuki-api-rust".to_string(),
            legacy_api_host: legacy_host,
            legacy_api_port: legacy_port,
            database_url: std::env::var("DATABASE_URL")
                .unwrap_or_else(|_| "postgres://postgres:postgres@db:5432/luuniensuki".to_string()),
            jwt_secret_key: std::env::var("JWT_SECRET_KEY")
                .unwrap_or_else(|_| "CHANGE_ME_IN_PRODUCTION".to_string()),
        }
    }
}
