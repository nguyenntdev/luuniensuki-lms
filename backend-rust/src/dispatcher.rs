//! Strangler dispatcher: per-route mode (Native/Gateway) loaded from
//! `config/route-modes.toml` with hot-reload via SIGHUP or 30s poll.
//!
//! Task 1.5: implements Requirement 13.1–13.4.

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::Duration;

use arc_swap::ArcSwap;
use tokio::sync::watch;

/// The serving mode for a route.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Mode {
    Native,
    Gateway,
}

/// A `(METHOD, path)` key for the route map.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct MethodPath {
    pub method: String,
    pub path: String,
}

impl MethodPath {
    pub fn new(method: &str, path: &str) -> Self {
        Self {
            method: method.to_uppercase(),
            path: path.to_string(),
        }
    }

    /// Key format used in TOML: "GET /api/v1/urns"
    pub fn toml_key(&self) -> String {
        format!("{} {}", self.method, self.path)
    }
}

/// The dispatcher holds the route-mode map behind an `ArcSwap` for
/// lock-free reads and atomic hot-reload.
#[derive(Clone)]
pub struct Dispatcher {
    map: Arc<ArcSwap<RouteMap>>,
    config_path: PathBuf,
    _shutdown: watch::Sender<()>,
}

#[derive(Debug)]
struct RouteMap {
    routes: HashMap<String, Mode>,
    default_mode: Mode,
}

impl Dispatcher {
    /// Load the dispatcher from the TOML file at `path`.
    pub fn load(path: &Path) -> anyhow::Result<Self> {
        let map = load_route_map(path)?;
        let (shutdown_tx, _shutdown_rx) = watch::channel(());

        Ok(Self {
            map: Arc::new(ArcSwap::from_pointee(map)),
            config_path: path.to_path_buf(),
            _shutdown: shutdown_tx,
        })
    }

    /// Spawn the background reload task (SIGHUP + 30s poll).
    pub fn spawn_reload_task(&self) {
        let map = self.map.clone();
        let path = self.config_path.clone();
        let mut shutdown_rx = self._shutdown.subscribe();

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(30));
            interval.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);

            #[cfg(unix)]
            let mut sighup = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::hangup())
                .expect("install SIGHUP handler");

            loop {
                #[cfg(unix)]
                tokio::select! {
                    _ = interval.tick() => {},
                    _ = sighup.recv() => {
                        tracing::info!("received SIGHUP, reloading route-modes.toml");
                    },
                    _ = shutdown_rx.changed() => break,
                }

                #[cfg(not(unix))]
                tokio::select! {
                    _ = interval.tick() => {},
                    _ = shutdown_rx.changed() => break,
                }

                match load_route_map(&path) {
                    Ok(new_map) => {
                        map.store(Arc::new(new_map));
                        tracing::debug!("route-modes.toml reloaded");
                    }
                    Err(e) => {
                        tracing::warn!(error = %e, "failed to reload route-modes.toml, keeping previous map");
                    }
                }
            }
        });
    }

    /// Get the effective mode for a given method+path.
    /// Returns `Native` if the route is explicitly set to native,
    /// `Gateway` if explicitly set to gateway, or the default mode
    /// if the route is not in the map.
    pub fn mode_for(&self, mp: &MethodPath) -> Mode {
        let guard = self.map.load();
        guard
            .routes
            .get(&mp.toml_key())
            .copied()
            .unwrap_or(guard.default_mode)
    }

    /// Get the override value for a route (None if not in the map).
    pub fn override_for(&self, mp: &MethodPath) -> Option<Mode> {
        let guard = self.map.load();
        guard.routes.get(&mp.toml_key()).copied()
    }

    /// Get the default mode.
    pub fn default_mode(&self) -> Mode {
        self.map.load().default_mode
    }
}

fn load_route_map(path: &Path) -> anyhow::Result<RouteMap> {
    let content = std::fs::read_to_string(path)
        .map_err(|e| anyhow::anyhow!("cannot read {}: {}", path.display(), e))?;

    let table: toml::Value = content
        .parse()
        .map_err(|e| anyhow::anyhow!("cannot parse {}: {}", path.display(), e))?;

    let mut routes = HashMap::new();

    if let Some(routes_table) = table.get("routes").and_then(|v| v.as_table()) {
        for (key, value) in routes_table {
            let mode = match value.as_str() {
                Some("native") => Mode::Native,
                Some("gateway") => Mode::Gateway,
                other => {
                    anyhow::bail!(
                        "invalid mode {:?} for route {:?} in {}",
                        other,
                        key,
                        path.display()
                    );
                }
            };
            routes.insert(key.clone(), mode);
        }
    }

    let default_mode = table
        .get("defaults")
        .and_then(|v| v.as_table())
        .and_then(|t| t.get("unknown_routes"))
        .and_then(|v| v.as_str())
        .map(|s| match s {
            "native" => Mode::Native,
            _ => Mode::Gateway,
        })
        .unwrap_or(Mode::Gateway);

    Ok(RouteMap {
        routes,
        default_mode,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    fn write_toml(content: &str) -> NamedTempFile {
        let mut f = NamedTempFile::new().unwrap();
        f.write_all(content.as_bytes()).unwrap();
        f
    }

    #[test]
    fn load_parses_routes_and_defaults() {
        let f = write_toml(
            r#"
[routes]
"GET /health" = "native"
"POST /api/v1/auth/login" = "gateway"

[defaults]
unknown_routes = "gateway"
"#,
        );

        let d = Dispatcher::load(f.path()).unwrap();

        assert_eq!(d.mode_for(&MethodPath::new("GET", "/health")), Mode::Native);
        assert_eq!(
            d.mode_for(&MethodPath::new("POST", "/api/v1/auth/login")),
            Mode::Gateway
        );
        // Unknown route falls back to default
        assert_eq!(
            d.mode_for(&MethodPath::new("GET", "/api/v1/unknown")),
            Mode::Gateway
        );
    }

    #[test]
    fn load_rejects_invalid_mode() {
        let f = write_toml(
            r#"
[routes]
"GET /health" = "invalid"
"#,
        );

        assert!(Dispatcher::load(f.path()).is_err());
    }
}
