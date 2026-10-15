use std::net::{IpAddr, Ipv4Addr, SocketAddr};
use std::path::PathBuf;

/// Returns `true` if `value` is a sentinel placeholder secret that must
/// never be used in a production deployment.
///
/// A value is treated as a sentinel when it is empty or starts with the
/// `"CHANGE_ME"` placeholder prefix (e.g. `"CHANGE_ME_IN_PRODUCTION"`,
/// `"CHANGE_ME_JANUS_ADMIN"`). Used by [`Settings::validate`] to fail
/// closed when required secrets are not externally supplied.
fn is_sentinel(value: &str) -> bool {
    value.is_empty() || value.starts_with("CHANGE_ME")
}

/// Application settings loaded from environment variables.
///
/// All fields have sensible defaults so the service can start in
/// development without a `.env` file. Production deployments MUST set
/// at least `DATABASE_URL` and `JWT_SECRET_KEY`.
#[derive(Clone, Debug)]
pub struct Settings {
    pub app_env: String,
    pub bind_addr: SocketAddr,
    pub database_url: String,
    pub database_max_connections: u32,
    pub legacy_api_host: String,
    pub legacy_api_port: u16,
    pub jwt_secret_key: String,
    pub jwt_algorithm: String,
    pub jwt_issuer: String,
    pub jwt_audience: String,
    /// Transition flag (env `JWT_VALIDATE_NEW_CLAIMS`, default `false`).
    ///
    /// Gates issue-then-enforce rollout of the `iss`/`aud` identity claims
    /// (Req 26.4). While `false`, tokens are accepted whether or not they
    /// carry `iss`/`aud`. Once both backends are known to issue the new
    /// claims, set this to `true` to require and validate them.
    pub jwt_validate_new_claims: bool,
    pub access_token_expire_minutes: i64,
    pub refresh_token_expire_days: i64,
    pub route_modes_path: PathBuf,
    pub route_inventory_path: PathBuf,
    pub uploads_dir: PathBuf,
    pub app_name: String,
    pub janus_ws_url: String,
    pub janus_public_ws_url: String,
    pub janus_http_url: String,
    pub janus_admin_url: String,
    pub janus_admin_secret: String,
    pub janus_api_secret: String,
    pub live_media_backend: String,
    pub live_reconnect_grace_seconds: u64,
    pub live_internal_token: String,
    pub live_join_credential_ttl_minutes: i64,
    pub turn_static_auth_secret: String,
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
        let ip: IpAddr = host.parse().unwrap_or(IpAddr::V4(Ipv4Addr::UNSPECIFIED));

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

        let live_reconnect_grace_seconds: u64 = std::env::var("LIVE_RECONNECT_GRACE_SECONDS")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(20);

        let live_join_credential_ttl_minutes: i64 =
            std::env::var("LIVE_JOIN_CREDENTIAL_TTL_MINUTES")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(30);

        Ok(Self {
            app_env: std::env::var("APP_ENV").unwrap_or_else(|_| "development".to_string()),
            bind_addr: SocketAddr::new(ip, port),
            database_url: std::env::var("DATABASE_URL")
                .unwrap_or_else(|_| "postgres://postgres:postgres@db:5432/luuniensuki".to_string()),
            database_max_connections,
            legacy_api_host,
            legacy_api_port,
            jwt_secret_key: std::env::var("JWT_SECRET_KEY").unwrap_or_else(|_| String::new()),
            jwt_algorithm: std::env::var("JWT_ALGORITHM").unwrap_or_else(|_| "HS256".to_string()),
            jwt_issuer: std::env::var("JWT_ISSUER").unwrap_or_else(|_| "luuniensuki".to_string()),
            jwt_audience: std::env::var("JWT_AUDIENCE")
                .unwrap_or_else(|_| "luuniensuki-app".to_string()),
            jwt_validate_new_claims: std::env::var("JWT_VALIDATE_NEW_CLAIMS")
                .map(|v| {
                    let v = v.trim();
                    v.eq_ignore_ascii_case("1") || v.eq_ignore_ascii_case("true")
                })
                .unwrap_or(false),
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
            app_name: std::env::var("APP_NAME")
                .unwrap_or_else(|_| "luuniensuki-api-rust".to_string()),
            janus_ws_url: std::env::var("JANUS_WS_URL")
                .unwrap_or_else(|_| "ws://janus-gateway:8188".to_string()),
            janus_public_ws_url: std::env::var("JANUS_PUBLIC_WS_URL")
                .unwrap_or_else(|_| "wss://lms.histolab.icu/janus".to_string()),
            janus_http_url: std::env::var("JANUS_HTTP_URL")
                .unwrap_or_else(|_| "http://janus-gateway:8088/janus".to_string()),
            janus_admin_url: std::env::var("JANUS_ADMIN_URL")
                .unwrap_or_else(|_| "http://janus-gateway:7088/admin".to_string()),
            janus_admin_secret: std::env::var("JANUS_ADMIN_SECRET")
                .unwrap_or_else(|_| String::new()),
            janus_api_secret: std::env::var("JANUS_API_SECRET").unwrap_or_else(|_| String::new()),
            live_media_backend: std::env::var("LIVE_MEDIA_BACKEND")
                .unwrap_or_else(|_| "livekit".to_string()),
            live_reconnect_grace_seconds,
            live_internal_token: std::env::var("LIVE_INTERNAL_TOKEN")
                .unwrap_or_else(|_| String::new()),
            live_join_credential_ttl_minutes,
            turn_static_auth_secret: std::env::var("TURN_STATIC_AUTH_SECRET")
                .unwrap_or_else(|_| "".to_string()),
        })
    }

    /// Returns `true` when the configured environment denotes production.
    ///
    /// The comparison is case-insensitive, so `APP_ENV=Production`,
    /// `production`, or `PRODUCTION` are all treated as production.
    pub fn is_production(&self) -> bool {
        self.app_env.eq_ignore_ascii_case("production")
    }

    /// Validate that production deployments are not running with insecure
    /// placeholder secrets.
    ///
    /// In a production environment every required service-to-service
    /// secret must be supplied externally with a non-sentinel value (see
    /// [`is_sentinel`]). When any required secret is missing or still set
    /// to a placeholder, this returns an error naming the offending
    /// environment-variable keys. The error message lists key names only
    /// and never includes secret values.
    ///
    /// Outside of production (development/test) this is a no-op and always
    /// returns `Ok(())`.
    pub fn validate(&self) -> anyhow::Result<()> {
        if self.is_production() {
            let mut offending: Vec<&str> = Vec::new();

            if is_sentinel(&self.jwt_secret_key) {
                offending.push("JWT_SECRET_KEY");
            }
            if is_sentinel(&self.janus_admin_secret) {
                offending.push("JANUS_ADMIN_SECRET");
            }
            if is_sentinel(&self.janus_api_secret) {
                offending.push("JANUS_API_SECRET");
            }
            if is_sentinel(&self.live_internal_token) {
                offending.push("LIVE_INTERNAL_TOKEN");
            }
            if self.turn_static_auth_secret.is_empty() {
                offending.push("TURN_STATIC_AUTH_SECRET");
            }

            if !offending.is_empty() {
                return Err(anyhow::anyhow!(
                    "Insecure production configuration: {}",
                    offending.join(", ")
                ));
            }
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Build a fully-populated production [`Settings`] with non-sentinel
    /// secrets. Individual tests override specific fields to exercise the
    /// validation paths in [`Settings::validate`].
    fn production_settings() -> Settings {
        Settings {
            app_env: "production".to_string(),
            bind_addr: SocketAddr::new(IpAddr::V4(Ipv4Addr::LOCALHOST), 8001),
            database_url: "postgres://user:pass@db:5432/app".to_string(),
            database_max_connections: 10,
            legacy_api_host: "api".to_string(),
            legacy_api_port: 8000,
            jwt_secret_key: "a-real-jwt-secret".to_string(),
            jwt_algorithm: "HS256".to_string(),
            jwt_issuer: "luuniensuki".to_string(),
            jwt_audience: "luuniensuki-app".to_string(),
            jwt_validate_new_claims: false,
            access_token_expire_minutes: 60,
            refresh_token_expire_days: 7,
            route_modes_path: PathBuf::from("config/route-modes.toml"),
            route_inventory_path: PathBuf::from("docs/route-inventory.json"),
            uploads_dir: PathBuf::from("../uploads"),
            app_name: "luuniensuki-api-rust".to_string(),
            janus_ws_url: "ws://janus-gateway:8188".to_string(),
            janus_public_ws_url: "wss://lms.histolab.icu/janus".to_string(),
            janus_http_url: "http://janus-gateway:8088/janus".to_string(),
            janus_admin_url: "http://janus-gateway:7088/admin".to_string(),
            janus_admin_secret: "a-real-janus-admin-secret".to_string(),
            janus_api_secret: "a-real-janus-api-secret".to_string(),
            live_media_backend: "livekit".to_string(),
            live_reconnect_grace_seconds: 20,
            live_internal_token: "a-real-live-internal-token".to_string(),
            live_join_credential_ttl_minutes: 30,
            turn_static_auth_secret: "a-real-turn-secret".to_string(),
        }
    }

    #[test]
    fn validate_rejects_production_with_sentinel_secrets() {
        let settings = Settings {
            jwt_secret_key: "CHANGE_ME_IN_PRODUCTION".to_string(),
            janus_admin_secret: "CHANGE_ME_JANUS_ADMIN".to_string(),
            janus_api_secret: "CHANGE_ME_JANUS_API".to_string(),
            live_internal_token: "CHANGE_ME_LIVE_INTERNAL".to_string(),
            turn_static_auth_secret: String::new(),
            ..production_settings()
        };

        let err = settings
            .validate()
            .expect_err("production with sentinel secrets must fail validation");
        let message = err.to_string();

        // The message names offending keys but never leaks secret values.
        assert!(message.contains("JWT_SECRET_KEY"));
        assert!(message.contains("JANUS_ADMIN_SECRET"));
        assert!(message.contains("JANUS_API_SECRET"));
        assert!(message.contains("LIVE_INTERNAL_TOKEN"));
        assert!(message.contains("TURN_STATIC_AUTH_SECRET"));
        assert!(!message.contains("CHANGE_ME"));
    }

    #[test]
    fn validate_accepts_fully_populated_production() {
        let settings = production_settings();
        assert!(settings.validate().is_ok());
    }

    #[test]
    fn validate_is_noop_outside_production() {
        // Sentinel secrets are tolerated in non-production environments.
        let settings = Settings {
            app_env: "development".to_string(),
            jwt_secret_key: "CHANGE_ME_IN_PRODUCTION".to_string(),
            turn_static_auth_secret: String::new(),
            ..production_settings()
        };
        assert!(settings.validate().is_ok());
    }

    #[test]
    fn from_env_loads_without_panic() {
        // `dotenvy::dotenv()` may load the project `.env` file, so we
        // cannot assert exact default values in CI. Secret fields now
        // default to an empty string when their env var is unset (empty is
        // itself a sentinel, so `validate()` still fails closed in
        // production), so we must not assert they are non-empty here.
        // Instead we verify that `from_env()` succeeds and returns a
        // well-formed struct for the non-secret fields.
        let settings = Settings::from_env().unwrap();

        assert!(settings.bind_addr.port() > 0);
        assert!(!settings.database_url.is_empty());
        assert!(settings.database_max_connections > 0);
        assert!(!settings.jwt_algorithm.is_empty());
        assert!(settings.access_token_expire_minutes > 0);
        assert!(settings.refresh_token_expire_days > 0);
    }
}
