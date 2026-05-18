//! Contract test harness for Rust ↔ Python response equivalence.
//!
//! Task 1.20: Loads snapshot fixtures captured from Python_Service and
//! compares them against Rust_Service responses. Equivalence is defined as:
//!
//! 1. HTTP status codes are equal.
//! 2. `Content-Type` headers are equal.
//! 3. JSON bodies are structurally equal modulo per-route `ignore_fields`
//!    defined in `tests/contract/ignore.toml`.
//!
//! **Validates:** Req 4.1, 4.2, 4.3, 4.4, 4.6, 4.7, 4.8; Property 11

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};

/// A single contract test fixture — a captured request/response pair from Python.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContractFixture {
    /// Human-readable test case name (e.g., "happy_path", "auth_error")
    pub name: String,
    /// The request that was sent
    pub request: FixtureRequest,
    /// The expected response from Python
    pub expected: FixtureResponse,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FixtureRequest {
    pub method: String,
    pub path: String,
    #[serde(default)]
    pub headers: HashMap<String, String>,
    #[serde(default)]
    pub body: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FixtureResponse {
    pub status: u16,
    pub content_type: String,
    #[serde(default)]
    pub body: Option<serde_json::Value>,
}

/// Per-route ignore configuration loaded from `ignore.toml`.
#[derive(Debug, Clone, Deserialize)]
pub struct IgnoreConfig {
    #[serde(default)]
    pub routes: HashMap<String, RouteIgnore>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct RouteIgnore {
    /// Fields to ignore during JSON comparison (e.g., "server_time", "request_id")
    #[serde(default)]
    pub ignore_fields: Vec<String>,
}

/// Load the ignore configuration from the TOML file.
pub fn load_ignore_config(path: &Path) -> IgnoreConfig {
    let content = std::fs::read_to_string(path).unwrap_or_else(|_| String::from("[routes]"));
    toml::from_str(&content).unwrap_or_else(|e| {
        panic!("Failed to parse ignore.toml at {}: {}", path.display(), e);
    })
}

/// Load all fixture files from a directory.
pub fn load_fixtures(dir: &Path) -> Vec<ContractFixture> {
    if !dir.exists() {
        return Vec::new();
    }

    let mut fixtures = Vec::new();
    for entry in std::fs::read_dir(dir).expect("read fixture directory") {
        let entry = entry.expect("read dir entry");
        let path = entry.path();
        if path.extension().map_or(false, |ext| ext == "json") {
            let content = std::fs::read_to_string(&path)
                .unwrap_or_else(|e| panic!("Failed to read fixture {}: {}", path.display(), e));
            let fixture: ContractFixture = serde_json::from_str(&content)
                .unwrap_or_else(|e| panic!("Failed to parse fixture {}: {}", path.display(), e));
            fixtures.push(fixture);
        }
    }
    fixtures
}

/// Compare two JSON values, ignoring specified fields at the top level.
/// Returns `Ok(())` if equivalent, `Err(description)` if not.
pub fn json_equivalent(
    expected: &serde_json::Value,
    actual: &serde_json::Value,
    ignore_fields: &[String],
) -> Result<(), String> {
    match (expected, actual) {
        (serde_json::Value::Object(exp_map), serde_json::Value::Object(act_map)) => {
            // Check all expected keys (minus ignored) exist in actual with same value
            for (key, exp_val) in exp_map {
                if ignore_fields.contains(key) {
                    continue;
                }
                match act_map.get(key) {
                    Some(act_val) => {
                        // Recurse without ignore_fields (only top-level ignores)
                        json_equivalent(exp_val, act_val, &[]).map_err(|e| {
                            format!("field \"{}\": {}", key, e)
                        })?;
                    }
                    None => {
                        return Err(format!("missing field \"{}\" in actual response", key));
                    }
                }
            }
            // Check actual doesn't have extra keys (minus ignored)
            for key in act_map.keys() {
                if ignore_fields.contains(key) {
                    continue;
                }
                if !exp_map.contains_key(key) {
                    return Err(format!("unexpected field \"{}\" in actual response", key));
                }
            }
            Ok(())
        }
        (serde_json::Value::Array(exp_arr), serde_json::Value::Array(act_arr)) => {
            if exp_arr.len() != act_arr.len() {
                return Err(format!(
                    "array length mismatch: expected {}, got {}",
                    exp_arr.len(),
                    act_arr.len()
                ));
            }
            for (i, (exp_item, act_item)) in exp_arr.iter().zip(act_arr.iter()).enumerate() {
                json_equivalent(exp_item, act_item, &[])
                    .map_err(|e| format!("array[{}]: {}", i, e))?;
            }
            Ok(())
        }
        _ => {
            if expected == actual {
                Ok(())
            } else {
                Err(format!("value mismatch: expected {:?}, got {:?}", expected, actual))
            }
        }
    }
}

/// Assert contract equivalence between a fixture's expected response and
/// the actual response from Rust_Service.
pub fn assert_contract_equivalence(
    fixture: &ContractFixture,
    actual_status: u16,
    actual_content_type: &str,
    actual_body: Option<&serde_json::Value>,
    ignore_fields: &[String],
) -> Result<(), String> {
    // 1. Status code equality (Req 4.2)
    if fixture.expected.status != actual_status {
        return Err(format!(
            "[{}] Status mismatch: expected {}, got {}",
            fixture.name, fixture.expected.status, actual_status
        ));
    }

    // 2. Content-Type equality (Req 4.4)
    if fixture.expected.content_type != actual_content_type {
        return Err(format!(
            "[{}] Content-Type mismatch: expected \"{}\", got \"{}\"",
            fixture.name, fixture.expected.content_type, actual_content_type
        ));
    }

    // 3. JSON structural equality modulo ignore_fields (Req 4.3)
    match (&fixture.expected.body, actual_body) {
        (Some(expected_body), Some(actual_body)) => {
            json_equivalent(expected_body, actual_body, ignore_fields).map_err(|e| {
                format!("[{}] Body mismatch: {}", fixture.name, e)
            })?;
        }
        (None, None) => {}
        (Some(_), None) => {
            return Err(format!("[{}] Expected body but got none", fixture.name));
        }
        (None, Some(_)) => {
            return Err(format!("[{}] Expected no body but got one", fixture.name));
        }
    }

    Ok(())
}

/// Get the fixtures directory path for a given endpoint group.
pub fn fixtures_dir(group: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("contract")
        .join("fixtures")
        .join(group)
}

/// Get the ignore config path.
pub fn ignore_config_path() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("contract")
        .join("ignore.toml")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn json_equivalent_identical_objects() {
        let a = serde_json::json!({"name": "test", "value": 42});
        let b = serde_json::json!({"name": "test", "value": 42});
        assert!(json_equivalent(&a, &b, &[]).is_ok());
    }

    #[test]
    fn json_equivalent_with_ignored_field() {
        let a = serde_json::json!({"name": "test", "server_time": "2024-01-01"});
        let b = serde_json::json!({"name": "test", "server_time": "2024-06-15"});
        let ignore = vec!["server_time".to_string()];
        assert!(json_equivalent(&a, &b, &ignore).is_ok());
    }

    #[test]
    fn json_equivalent_detects_missing_field() {
        let a = serde_json::json!({"name": "test", "value": 42});
        let b = serde_json::json!({"name": "test"});
        assert!(json_equivalent(&a, &b, &[]).is_err());
    }

    #[test]
    fn json_equivalent_detects_extra_field() {
        let a = serde_json::json!({"name": "test"});
        let b = serde_json::json!({"name": "test", "extra": true});
        assert!(json_equivalent(&a, &b, &[]).is_err());
    }

    #[test]
    fn json_equivalent_detects_value_mismatch() {
        let a = serde_json::json!({"name": "test", "value": 42});
        let b = serde_json::json!({"name": "test", "value": 99});
        assert!(json_equivalent(&a, &b, &[]).is_err());
    }

    #[test]
    fn json_equivalent_arrays_order_matters() {
        let a = serde_json::json!([1, 2, 3]);
        let b = serde_json::json!([1, 3, 2]);
        assert!(json_equivalent(&a, &b, &[]).is_err());
    }

    #[test]
    fn json_equivalent_nested_objects() {
        let a = serde_json::json!({"user": {"name": "alice", "age": 30}});
        let b = serde_json::json!({"user": {"name": "alice", "age": 30}});
        assert!(json_equivalent(&a, &b, &[]).is_ok());
    }

    #[test]
    fn load_ignore_config_missing_file_returns_default() {
        let config = load_ignore_config(Path::new("/nonexistent/ignore.toml"));
        assert!(config.routes.is_empty());
    }
}
