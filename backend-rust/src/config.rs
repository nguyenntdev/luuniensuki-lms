use std::net::{IpAddr, Ipv4Addr, SocketAddr};
use std::path::PathBuf;

/// Application settings loaded from environment variables.
///
/// All fields have sensible defaults so the service can start in
/// development without a `.env` file. Production deployments MUST set
/// at least `DATABASE_URL` and `JWT_SECRET_KEY`.
#[derive(Clone, Debug)]
pub struct Settings {
    pub bind_addr: SocketAddr,
    pub database_url: String,
    pub database_max_connections: u32,
    pub legacy_api_host: String,
    pub legacy_api_port: u16,
    pub jwt_secret_key: String,
    pub jwt_algorithm: String,
    pub access_token_expire_minutes: i64,
    pub refresh_token_expire_days: i64,
    pub route_modes_path: PathBuf,
    pub route_inventory_path: PathBuf,
    pub uploads_dir: PathBuf,
}

impl Settings {
    /// Load settings from environment variables (with `dotenvy` `.env`
    /// support). Returns an error only if a required variable is present
    /// but malformed; missing variables fall back to defaults.
    pub fn from_env() -> anyhow::Result<Self> {
        dotenvy::dotenv().ok();

        let host = std::env::var("API_HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
        let port: u16 = std::env::var("API_PORT")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(8001);
        let ip: IpAddr = host
            .parse()
            .unwrap_or(IpAddr::V4(Ipv4Addr::UNSPECIFIED));

        let database_max_connections: u32 = std::env::var("DATABASE_MAX_CONNECTIONS")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(10);

        let legacy_api_host =
            std::env::var("LEGACY_API_HOST").unwrap_or_else(|_| "api".to_string());
        let legacy_api_port: u16 = std::env::var("LEGACY_API_PORT")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(8000);

        let access_token_expire_minutes: i64 = std::env::var("ACCESS_TOKEN_EXPIRE_MINUTES")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(60);

        let refresh_token_expire_days: i64 = std::env::var("REFRESH_TOKEN_EXPIRE_DAYS")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(7);

        Ok(Self {
            bind_addr: SocketAddr::new(ip, port),
            database_url: std::env::var("DATABASE_URL")
                .unwrap_or_else(|_| "postgres://postgres:postgres@db:5432/luuniensuki".to_string()),
            database_max_connections,
            legacy_api_host,
            legacy_api_port,
            jwt_secret_key: std::env::var("JWT_SECRET_KEY")
                .unwrap_or_else(|_| "CHANGE_ME_IN_PRODUCTION".to_string()),
            jwt_algorithm: std::env::var("JWT_ALGORITHM")
                .unwrap_or_else(|_| "HS256".to_string()),
            access_token_expire_minutes,
            refresh_token_expire_days,
            route_modes_path: std::env::var("ROUTE_MODES_PATH")
                .map(PathBuf::from)
                .unwrap_or_else(|_| PathBuf::from("config/route-modes.toml")),
            route_inventory_path: std::env::var("ROUTE_INVENTORY_PATH")
                .map(PathBuf::from)
                .unwrap_or_else(|_| PathBuf::from("docs/route-inventory.json")),
            uploads_dir: std::env::var("UPLOADS_DIR")
                .map(PathBuf::from)
                .unwrap_or_else(|_| PathBuf::from("../uploads")),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn from_env_loads_without_panic() {
        // `dotenvy::dotenv()` may load the project `.env` file, so we
        // cannot assert exact default values in CI. Instead we verify
        // that `from_env()` succeeds and returns a well-formed struct.
        let settings = Settings::from_env().unwrap();

        assert!(settings.bind_addr.port() > 0);
        assert!(!settings.database_url.is_empty());
        assert!(settings.database_max_connections > 0);
        assert!(!settings.jwt_secret_key.is_empty());
        assert!(!settings.jwt_algorithm.is_empty());
        assert!(settings.access_token_expire_minutes > 0);
        assert!(settings.refresh_token_expire_days > 0);
    }
}
