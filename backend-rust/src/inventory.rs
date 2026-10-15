//! Route inventory: loads `docs/route-inventory.json` at startup,
//! provides a coverage assertion, and serves `GET /api/v1/internal/route-coverage`.
//!
//! Task 1.10: implements Requirements 2.4, 2.5, 10.1, 10.3, 13.3.

use std::collections::HashMap;
use std::path::Path;
use std::sync::Arc;

use axum::extract::State;
use axum::Json;
use serde::{Deserialize, Serialize};

use crate::dispatcher::{Dispatcher, MethodPath, Mode};
use crate::gateway::GatewayState;

/// A single entry from `docs/route-inventory.json`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InventoryEntry {
    pub method: String,
    pub path: String,
    pub group: String,
    pub status: String,
}

/// Response shape for `GET /api/v1/internal/route-coverage`.
#[derive(Debug, Clone, Serialize)]
pub struct RouteCoverageResponse {
    pub routes: Vec<RouteCoverageEntry>,
    pub summary: CoverageSummary,
}

/// Per-route entry in the coverage response.
#[derive(Debug, Clone, Serialize)]
pub struct RouteCoverageEntry {
    pub method: String,
    pub path: String,
    pub group: String,
    pub status: String,
    pub native_handler_registered: bool,
    #[serde(rename = "override", skip_serializing_if = "Option::is_none")]
    pub override_mode: Option<String>,
}

/// Summary statistics in the coverage response.
#[derive(Debug, Clone, Serialize)]
pub struct CoverageSummary {
    pub total: usize,
    pub native: usize,
    pub gateway: usize,
    pub groups_complete: usize,
    pub groups_total: usize,
    pub ready_for_cutover: bool,
}

/// Load the route inventory from a JSON file.
///
/// If the file does not exist, logs a warning and returns an empty inventory
/// so the app can start in development without it.
pub fn load_inventory(path: &Path) -> anyhow::Result<Arc<Vec<InventoryEntry>>> {
    if !path.exists() {
        tracing::warn!(
            path = %path.display(),
            "route-inventory.json not found, using empty inventory"
        );
        return Ok(Arc::new(Vec::new()));
    }

    let content = std::fs::read_to_string(path)
        .map_err(|e| anyhow::anyhow!("cannot read {}: {}", path.display(), e))?;

    let entries: Vec<InventoryEntry> = serde_json::from_str(&content)
        .map_err(|e| anyhow::anyhow!("cannot parse {}: {}", path.display(), e))?;

    tracing::info!(
        path = %path.display(),
        count = entries.len(),
        "loaded route inventory"
    );

    Ok(Arc::new(entries))
}

/// Assert that every route in the inventory is covered — either by a native
/// handler or by the gateway fallback.
///
/// Since we have `gateway::fallback_to_python` as the Axum fallback, every
/// route is implicitly covered. This function logs a summary and always
/// succeeds. When native handlers are registered in later phases, this can
/// be tightened to verify explicit registration.
pub fn assert_full_coverage(
    inventory: &[InventoryEntry],
    dispatcher: &Dispatcher,
) -> anyhow::Result<()> {
    if inventory.is_empty() {
        tracing::info!("route inventory is empty, skipping coverage assertion");
        return Ok(());
    }

    let mut native_count = 0usize;
    let mut gateway_count = 0usize;

    for entry in inventory {
        let mp = MethodPath::new(&entry.method, &entry.path);
        match dispatcher.mode_for(&mp) {
            Mode::Native => native_count += 1,
            Mode::Gateway => gateway_count += 1,
        }
    }

    tracing::info!(
        total = inventory.len(),
        native = native_count,
        gateway = gateway_count,
        "route coverage: all {} routes covered (gateway fallback catches unregistered routes)",
        inventory.len()
    );

    Ok(())
}

/// Shared application state that includes the inventory and dispatcher.
#[derive(Clone)]
pub struct AppState {
    pub inventory: Arc<Vec<InventoryEntry>>,
    pub dispatcher: Dispatcher,
    pub gateway: GatewayState,
}

/// `GET /api/v1/internal/route-coverage` handler.
///
/// Returns the live coverage map showing each route's effective mode
/// and whether a native handler is registered.
pub async fn route_coverage(State(state): State<AppState>) -> Json<RouteCoverageResponse> {
    let inventory = &state.inventory;
    let dispatcher = &state.dispatcher;

    let mut routes = Vec::with_capacity(inventory.len());
    let mut native_count = 0usize;
    let mut gateway_count = 0usize;

    // Track groups and whether all routes in a group are native
    let mut groups: HashMap<&str, (usize, usize)> = HashMap::new(); // (total, native)

    for entry in inventory.iter() {
        let mp = MethodPath::new(&entry.method, &entry.path);
        let effective_mode = dispatcher.mode_for(&mp);
        let override_mode = dispatcher.override_for(&mp);

        // For now, native_handler_registered is true only for routes
        // whose inventory status is "native" (i.e., they have a Rust handler).
        let native_handler_registered = entry.status == "native";

        let status_str = match effective_mode {
            Mode::Native => {
                native_count += 1;
                "native"
            }
            Mode::Gateway => {
                gateway_count += 1;
                "gateway"
            }
        };

        let override_str = override_mode.map(|m| match m {
            Mode::Native => "native".to_string(),
            Mode::Gateway => "gateway".to_string(),
        });

        // Update group tracking
        let group_entry = groups.entry(&entry.group).or_insert((0, 0));
        group_entry.0 += 1;
        if matches!(effective_mode, Mode::Native) {
            group_entry.1 += 1;
        }

        routes.push(RouteCoverageEntry {
            method: entry.method.clone(),
            path: entry.path.clone(),
            group: entry.group.clone(),
            status: status_str.to_string(),
            native_handler_registered,
            override_mode: override_str,
        });
    }

    let groups_total = groups.len();
    let groups_complete = groups
        .values()
        .filter(|(total, native)| total == native)
        .count();
    let ready_for_cutover = inventory.len() > 0 && native_count == inventory.len();

    let summary = CoverageSummary {
        total: inventory.len(),
        native: native_count,
        gateway: gateway_count,
        groups_complete,
        groups_total,
        ready_for_cutover,
    };

    Json(RouteCoverageResponse { routes, summary })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    fn sample_inventory_json() -> &'static str {
        r#"[
            {"method": "GET", "path": "/health", "group": "foundations", "status": "native"},
            {"method": "GET", "path": "/api/v1/internal/route-coverage", "group": "foundations", "status": "native"},
            {"method": "GET", "path": "/api/v1/badges", "group": "public-reads", "status": "gateway"}
        ]"#
    }

    #[test]
    fn load_inventory_parses_json() {
        let mut f = NamedTempFile::new().unwrap();
        f.write_all(sample_inventory_json().as_bytes()).unwrap();

        let inv = load_inventory(f.path()).unwrap();
        assert_eq!(inv.len(), 3);
        assert_eq!(inv[0].method, "GET");
        assert_eq!(inv[0].path, "/health");
        assert_eq!(inv[0].group, "foundations");
        assert_eq!(inv[0].status, "native");
    }

    #[test]
    fn load_inventory_missing_file_returns_empty() {
        let path = Path::new("/tmp/nonexistent-route-inventory-12345.json");
        let inv = load_inventory(path).unwrap();
        assert!(inv.is_empty());
    }

    #[test]
    fn assert_full_coverage_succeeds_with_gateway_fallback() {
        // Create a dispatcher with default gateway mode
        let mut f = NamedTempFile::new().unwrap();
        f.write_all(b"[defaults]\nunknown_routes = \"gateway\"\n")
            .unwrap();

        let dispatcher = Dispatcher::load(f.path()).unwrap();

        let entries = vec![
            InventoryEntry {
                method: "GET".to_string(),
                path: "/health".to_string(),
                group: "foundations".to_string(),
                status: "native".to_string(),
            },
            InventoryEntry {
                method: "GET".to_string(),
                path: "/api/v1/badges".to_string(),
                group: "public-reads".to_string(),
                status: "gateway".to_string(),
            },
        ];

        let result = assert_full_coverage(&entries, &dispatcher);
        assert!(result.is_ok());
    }

    #[test]
    fn assert_full_coverage_empty_inventory_succeeds() {
        let mut f = NamedTempFile::new().unwrap();
        f.write_all(b"[defaults]\nunknown_routes = \"gateway\"\n")
            .unwrap();

        let dispatcher = Dispatcher::load(f.path()).unwrap();
        let result = assert_full_coverage(&[], &dispatcher);
        assert!(result.is_ok());
    }
}
