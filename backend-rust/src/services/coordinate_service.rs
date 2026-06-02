//! Motif coordinate persistence (annotation tool save path).
//!
//! Ports the matching logic of `backend/import_coordinates.py` into a runtime
//! upsert: given an urn slug and a list of annotated points, update the matching
//! `motifs` rows' `pos_x/pos_y/pos_z/bounding_radius` in place. A motif is
//! matched within its urn by `mesh_name` first, then by `name` (mirroring the
//! Python importer's `mesh_name`/`motif_name` precedence).
//!
//! Uses sqlx runtime queries (`query`, `query_scalar`) — NOT the `query!` macro.
//! sqlx errors map to `AppError::Internal`.

use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;

/// One annotated coordinate from the annotation tool.
#[derive(Debug, Clone, Deserialize)]
pub struct CoordinateInput {
    /// Urn slug the marker belongs to (e.g. `cao-dinh`).
    pub urn_slug: String,
    /// Human motif name (fallback match key).
    pub motif_name: String,
    /// Mesh name (preferred match key); falls back to `motif_name` when empty.
    #[serde(default)]
    pub mesh_name: Option<String>,
    pub pos_x: f64,
    pub pos_y: f64,
    pub pos_z: f64,
    #[serde(default = "default_radius")]
    pub bounding_radius: f64,
}

fn default_radius() -> f64 {
    0.08
}

/// Per-item outcome so the caller/UI can show which markers matched.
#[derive(Debug, Clone, Serialize)]
pub struct CoordinateResult {
    pub urn_slug: String,
    pub motif_name: String,
    pub matched: bool,
}

/// Summary returned to the admin client.
#[derive(Debug, Clone, Serialize)]
pub struct SaveCoordinatesResponse {
    pub total: usize,
    pub matched: usize,
    pub unmatched: usize,
    pub results: Vec<CoordinateResult>,
}

/// Upsert a batch of annotated coordinates onto their `motifs` rows.
///
/// Each item is matched within its urn (`urns.slug = urn_slug`) by
/// `mesh_name = <mesh>` OR `name = <motif_name>`, then its position columns are
/// updated. Items that match no motif are reported as `matched = false` and left
/// untouched (no rows are created — the annotation tool only repositions
/// existing motifs, matching the importer's behavior).
pub async fn save_coordinates(
    pool: &PgPool,
    items: &[CoordinateInput],
) -> Result<SaveCoordinatesResponse, AppError> {
    let mut results = Vec::with_capacity(items.len());
    let mut matched = 0usize;

    for item in items {
        let mesh = item
            .mesh_name
            .as_deref()
            .filter(|s| !s.trim().is_empty())
            .unwrap_or(item.motif_name.as_str());

        // Resolve the motif id within the urn, by mesh_name first then name.
        let motif_id: Option<Uuid> = sqlx::query_scalar(
            r#"
            SELECT m.id
            FROM motifs m
            JOIN urns u ON u.id = m.urn_id
            WHERE u.slug = $1
              AND (m.mesh_name = $2 OR m.name = $3)
            ORDER BY (m.mesh_name = $2) DESC
            LIMIT 1
            "#,
        )
        .bind(&item.urn_slug)
        .bind(mesh)
        .bind(&item.motif_name)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

        let did_match = if let Some(id) = motif_id {
            sqlx::query(
                r#"
                UPDATE motifs
                SET pos_x = $2, pos_y = $3, pos_z = $4, bounding_radius = $5
                WHERE id = $1
                "#,
            )
            .bind(id)
            .bind(item.pos_x)
            .bind(item.pos_y)
            .bind(item.pos_z)
            .bind(item.bounding_radius)
            .execute(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
            matched += 1;
            true
        } else {
            false
        };

        results.push(CoordinateResult {
            urn_slug: item.urn_slug.clone(),
            motif_name: item.motif_name.clone(),
            matched: did_match,
        });
    }

    Ok(SaveCoordinatesResponse {
        total: items.len(),
        matched,
        unmatched: items.len() - matched,
        results,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_radius_is_008() {
        assert_eq!(default_radius(), 0.08);
    }

    #[test]
    fn coordinate_input_deserializes_with_defaults() {
        let json = r#"{"urn_slug":"cao-dinh","motif_name":"Long","pos_x":1.0,"pos_y":2.0,"pos_z":3.0}"#;
        let parsed: CoordinateInput = serde_json::from_str(json).unwrap();
        assert_eq!(parsed.urn_slug, "cao-dinh");
        assert_eq!(parsed.motif_name, "Long");
        assert!(parsed.mesh_name.is_none());
        assert_eq!(parsed.bounding_radius, 0.08);
    }

    #[test]
    fn coordinate_input_accepts_mesh_and_radius() {
        let json = r#"{"urn_slug":"cao-dinh","motif_name":"Long","mesh_name":"Long_mesh","pos_x":1.0,"pos_y":2.0,"pos_z":3.0,"bounding_radius":0.2}"#;
        let parsed: CoordinateInput = serde_json::from_str(json).unwrap();
        assert_eq!(parsed.mesh_name.as_deref(), Some("Long_mesh"));
        assert_eq!(parsed.bounding_radius, 0.2);
    }
}
