//! Admin mesh-processing pipeline.
//!
//! Gap 1 from `docs/CONFERENCE_PAPER_MATCH_ANALYSIS.md`: triggers the
//! mesh-processor Python CLI (`tools/mesh-processor/process_mesh.py`) and
//! records every run in the `mesh_processing_jobs` audit table.
//!
//! Endpoints (admin-only):
//!   * `POST /api/v1/admin/mesh/reprocess`        — currently 501 (Phase D2)
//!   * `GET  /api/v1/admin/mesh/jobs`             — paginated job listing
//!   * `GET  /api/v1/admin/mesh/jobs/:id`         — fetch a single job
//!   * `GET  /api/v1/admin/mesh/inventory`        — list GLB files in models_upload/
//!
//! Phase D status: the `api_rust` container does not bind-mount the host's
//! `tools/mesh-processor/venv` or `models_upload/`, so it cannot shell out to
//! the Python CLI. Until a worker container ships in Phase D2, `reprocess`
//! returns 501. Operators run `tools/mesh-processor/process_cuu_dinh.sh`
//! from the host shell instead. The DB schema and the listing/inventory
//! endpoints are still useful so that bash runs can `INSERT` audit rows.

use axum::{
    extract::{Multipart, Path, Query, State},
    http::{header, HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value as JsonValue;
use sqlx::PgPool;
use std::path::PathBuf;
use std::time::Duration;
use tokio::process::Command;
use tokio::time::timeout;
use uuid::Uuid;

use crate::auth;
use crate::config::Settings;
use crate::error::AppError;
use crate::routes::auth::AuthState;

// ---------------------------------------------------------------------------
// Constants — pinned host paths. The api_rust container mounts these from
// the host (see docker-compose.override.yml).
// ---------------------------------------------------------------------------

const MESH_PROCESSOR_DIR: &str = "/opt/luuniensuki-lms/tools/mesh-processor";
const MESH_PROCESSOR_PY: &str = "/opt/luuniensuki-lms/tools/mesh-processor/process_mesh.py";
const MESH_PROCESSOR_VENV_PY: &str =
    "/opt/luuniensuki-lms/tools/mesh-processor/venv/bin/python";
const MODELS_UPLOAD_PREFIX: &str = "/opt/luuniensuki-lms/models_upload/";
const JOB_TIMEOUT_SECS: u64 = 300;
const ALLOWED_LODS: [&str; 3] = ["512", "1k", "2k"];
const MAX_UPLOAD_BYTES: usize = 200 * 1024 * 1024; // 200 MB

/// Resolve mesh-processor python interpreter path. Override via
/// `MESH_PROCESSOR_PYTHON` env var (e.g. when the venv lives somewhere else
/// or to point at the host Python from inside the api_rust container).
fn mesh_processor_python() -> String {
    std::env::var("MESH_PROCESSOR_PYTHON")
        .unwrap_or_else(|_| MESH_PROCESSOR_VENV_PY.to_string())
}

/// Resolve the path to `process_mesh.py`. Override via
/// `MESH_PROCESSOR_SCRIPT`.
fn mesh_processor_script() -> String {
    std::env::var("MESH_PROCESSOR_SCRIPT")
        .unwrap_or_else(|_| MESH_PROCESSOR_PY.to_string())
}

/// Resolve the working directory passed to the python tool. Override via
/// `MESH_PROCESSOR_DIR`.
fn mesh_processor_dir() -> String {
    std::env::var("MESH_PROCESSOR_DIR")
        .unwrap_or_else(|_| MESH_PROCESSOR_DIR.to_string())
}

// ---------------------------------------------------------------------------
// Auth helpers (mirror routes/admin.rs)
// ---------------------------------------------------------------------------

fn extract_token_from_headers(headers: &HeaderMap) -> Option<String> {
    if let Some(auth_header) = headers.get(header::AUTHORIZATION) {
        if let Ok(auth_str) = auth_header.to_str() {
            if let Some(token) = auth_str.strip_prefix("Bearer ") {
                return Some(token.to_string());
            }
        }
    }
    if let Some(cookie_header) = headers.get(header::COOKIE) {
        if let Ok(cookie_str) = cookie_header.to_str() {
            for part in cookie_str.split(';') {
                let trimmed = part.trim();
                if let Some(value) = trimmed.strip_prefix("luuniensuki_access=") {
                    return Some(value.to_string());
                }
            }
        }
    }
    None
}

fn require_pool(pool: &Option<PgPool>) -> Result<&PgPool, AppError> {
    pool.as_ref().ok_or_else(|| AppError::Http {
        status: StatusCode::SERVICE_UNAVAILABLE,
        message: "Database unavailable".to_string(),
    })
}

fn authenticate_admin(
    headers: &HeaderMap,
    settings: &Settings,
) -> Result<Uuid, AppError> {
    let token = extract_token_from_headers(headers).ok_or(AppError::Unauthorized)?;
    let claims = auth::verify_access_token(&token, &settings.jwt_secret_key)
        .map_err(|_| AppError::Unauthorized)?;
    if claims.role != "admin" {
        return Err(AppError::Http {
            status: StatusCode::FORBIDDEN,
            message: "Admin access required".to_string(),
        });
    }
    let user_id: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;
    Ok(user_id)
}

// ---------------------------------------------------------------------------
// DTOs
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
pub struct ReprocessRequest {
    pub input_path: String,
    pub output_path: String,
    pub lod: String,
    pub urn_slug: Option<String>,
    #[serde(default = "default_fill_holes")]
    pub fill_holes: bool,
    #[serde(default = "default_smooth_iter")]
    pub smooth_iter: i32,
}

fn default_fill_holes() -> bool {
    true
}
fn default_smooth_iter() -> i32 {
    5
}

#[derive(Debug, Serialize)]
pub struct MeshJob {
    pub id: Uuid,
    pub actor_user_id: Uuid,
    pub urn_slug: Option<String>,
    pub input_path: String,
    pub output_path: String,
    pub lod_label: String,
    pub fill_holes: bool,
    pub smooth_iter: i32,
    pub status: String,
    pub started_at: DateTime<Utc>,
    pub completed_at: Option<DateTime<Utc>>,
    pub input_bytes: Option<i64>,
    pub output_bytes: Option<i64>,
    pub size_reduction_pct: Option<f64>,
    pub faces_initial: Option<i64>,
    pub faces_final: Option<i64>,
    pub elapsed_ms: Option<i32>,
    pub summary_json: Option<JsonValue>,
    pub error_message: Option<String>,
    pub created_at: DateTime<Utc>,
}

#[derive(sqlx::FromRow)]
struct MeshJobRow {
    id: Uuid,
    actor_user_id: Uuid,
    urn_slug: Option<String>,
    input_path: String,
    output_path: String,
    lod_label: String,
    fill_holes: bool,
    smooth_iter: i32,
    status: String,
    started_at: DateTime<Utc>,
    completed_at: Option<DateTime<Utc>>,
    input_bytes: Option<i64>,
    output_bytes: Option<i64>,
    size_reduction_pct: Option<String>,
    faces_initial: Option<i64>,
    faces_final: Option<i64>,
    elapsed_ms: Option<i32>,
    summary_json: Option<JsonValue>,
    error_message: Option<String>,
    created_at: DateTime<Utc>,
}

impl From<MeshJobRow> for MeshJob {
    fn from(r: MeshJobRow) -> Self {
        MeshJob {
            id: r.id,
            actor_user_id: r.actor_user_id,
            urn_slug: r.urn_slug,
            input_path: r.input_path,
            output_path: r.output_path,
            lod_label: r.lod_label,
            fill_holes: r.fill_holes,
            smooth_iter: r.smooth_iter,
            status: r.status,
            started_at: r.started_at,
            completed_at: r.completed_at,
            input_bytes: r.input_bytes,
            output_bytes: r.output_bytes,
            size_reduction_pct: r
                .size_reduction_pct
                .and_then(|s| s.parse::<f64>().ok()),
            faces_initial: r.faces_initial,
            faces_final: r.faces_final,
            elapsed_ms: r.elapsed_ms,
            summary_json: r.summary_json,
            error_message: r.error_message,
            created_at: r.created_at,
        }
    }
}

#[derive(Debug, Deserialize)]
pub struct JobsListQuery {
    pub page: Option<i32>,
    pub per_page: Option<i32>,
    pub status: Option<String>,
    pub urn_slug: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct JobsListResponse {
    pub jobs: Vec<MeshJob>,
    pub page: i32,
    pub per_page: i32,
    pub total: i64,
}

// ---------------------------------------------------------------------------
// Validation helpers
// ---------------------------------------------------------------------------

fn validate_lod(lod: &str) -> Result<(), AppError> {
    if !ALLOWED_LODS.contains(&lod) {
        return Err(AppError::Domain {
            status: StatusCode::BAD_REQUEST,
            code: "INVALID_LOD".to_string(),
            message: format!("lod must be one of {:?}", ALLOWED_LODS),
            details: serde_json::json!({ "lod": lod }),
        });
    }
    Ok(())
}

/// Reject anything that isn't a normal absolute path under
/// `/opt/luuniensuki-lms/models_upload/`. We forbid `..` segments to defeat
/// the obvious traversal vector ("/opt/luuniensuki-lms/models_upload/../etc/passwd").
fn validate_path(path: &str, code: &'static str, label: &str) -> Result<(), AppError> {
    let bad = !path.starts_with(MODELS_UPLOAD_PREFIX)
        || path.contains("/../")
        || path.ends_with("/..")
        || path.contains('\0');
    if bad {
        return Err(AppError::Domain {
            status: StatusCode::BAD_REQUEST,
            code: code.to_string(),
            message: format!(
                "{} must be an absolute path under {}",
                label, MODELS_UPLOAD_PREFIX
            ),
            details: serde_json::json!({ label: path }),
        });
    }
    Ok(())
}

// ---------------------------------------------------------------------------
// Handlers
// ---------------------------------------------------------------------------

/// POST /api/v1/admin/mesh/reprocess
///
/// **Phase D status:** the `api_rust` container does not have the Python
/// venv or model files mounted, so we cannot execute the mesh-processor
/// CLI from inside the container. This endpoint validates the admin's
/// request and then returns 501 with operator guidance. Phase D2 will
/// ship a dedicated worker container that owns the pipeline.
pub async fn reprocess(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(body): Json<ReprocessRequest>,
) -> Result<axum::response::Response, AppError> {
    let _ = authenticate_admin(&headers, &state.settings)?;

    // Validate inputs so admins still get a fast 400 if they mistype the
    // path or LOD before we reject with 501.
    validate_lod(&body.lod)?;
    validate_path(&body.input_path, "INVALID_INPUT_PATH", "input_path")?;
    validate_path(&body.output_path, "INVALID_OUTPUT_PATH", "output_path")?;

    Err(AppError::Domain {
        status: StatusCode::NOT_IMPLEMENTED,
        code: "MESH_REPROCESS_NOT_IMPLEMENTED".to_string(),
        message: "Mesh reprocessing must currently be run from the host shell. \
                  Use `./tools/mesh-processor/process_cuu_dinh.sh` or \
                  `./tools/mesh-processor/venv/bin/python tools/mesh-processor/process_mesh.py ...`. \
                  This endpoint is reserved for Phase D2 when a worker container ships."
            .to_string(),
        details: serde_json::json!({
            "input_path": body.input_path,
            "output_path": body.output_path,
            "lod": body.lod,
            "host_command": format!(
                "/opt/luuniensuki-lms/tools/mesh-processor/venv/bin/python \
/opt/luuniensuki-lms/tools/mesh-processor/process_mesh.py {} --output {} --lod {}{} --smooth-iter {} --quiet",
                body.input_path,
                body.output_path,
                body.lod,
                if body.fill_holes { " --fill-holes" } else { "" },
                body.smooth_iter.max(0),
            ),
        }),
    })
}

// ---------------------------------------------------------------------------
// Upload handler — Phase D entrypoint
// ---------------------------------------------------------------------------

/// Sanitize a user-provided filename by keeping only safe characters.
/// Strips path separators, NUL, leading dots, and limits length.
#[allow(dead_code)]
fn sanitize_filename(name: &str) -> String {
    let cleaned: String = name
        .chars()
        .filter(|c| !matches!(c, '/' | '\\' | '\0'))
        .collect();
    let trimmed = cleaned.trim_start_matches('.').trim();
    let max_len = 80;
    if trimmed.is_empty() {
        return "scan.glb".to_string();
    }
    if trimmed.len() > max_len {
        // truncate at UTF-8 boundary
        let mut end = max_len;
        while end > 0 && !trimmed.is_char_boundary(end) {
            end -= 1;
        }
        return trimmed[..end].to_string();
    }
    trimmed.to_string()
}

/// POST /api/v1/admin/mesh/upload (multipart)
///
/// Accepts a raw GLB upload, persists it under `<uploads>/scans/raw/`,
/// records a `pending` row in `mesh_processing_jobs`, and spawns a tokio
/// task that runs the Python mesh-processor CLI. Returns 202 immediately.
#[allow(dead_code)]
pub async fn upload_scan(
    headers: HeaderMap,
    State(state): State<AuthState>,
    mut multipart: Multipart,
) -> Result<impl IntoResponse, AppError> {
    let actor_user_id = authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?.clone();

    // Parse multipart form ----------------------------------------------------
    let mut file_data: Option<(String, Vec<u8>)> = None;
    let mut urn_slug: Option<String> = None;
    let mut target_lod: Option<String> = None;
    let mut fill_holes: bool = true;

    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|e| AppError::Http {
            status: StatusCode::BAD_REQUEST,
            message: format!("Invalid multipart data: {}", e),
        })?
    {
        let name = field.name().unwrap_or("").to_string();
        match name.as_str() {
            "file" => {
                let filename = field
                    .file_name()
                    .map(|s| s.to_string())
                    .unwrap_or_else(|| "scan.glb".to_string());
                let data = field
                    .bytes()
                    .await
                    .map_err(|e| AppError::Http {
                        status: StatusCode::BAD_REQUEST,
                        message: format!("Failed to read file bytes: {}", e),
                    })?;
                if data.len() > MAX_UPLOAD_BYTES {
                    return Err(AppError::Domain {
                        status: StatusCode::PAYLOAD_TOO_LARGE,
                        code: "UPLOAD_TOO_LARGE".to_string(),
                        message: format!(
                            "Uploaded file exceeds {} byte limit",
                            MAX_UPLOAD_BYTES
                        ),
                        details: serde_json::json!({
                            "max_bytes": MAX_UPLOAD_BYTES,
                            "actual_bytes": data.len()
                        }),
                    });
                }
                file_data = Some((filename, data.to_vec()));
            }
            "urn_slug" => {
                let s = field.text().await.map_err(|e| AppError::Http {
                    status: StatusCode::BAD_REQUEST,
                    message: format!("Invalid urn_slug: {}", e),
                })?;
                let s = s.trim();
                if !s.is_empty() {
                    urn_slug = Some(s.to_string());
                }
            }
            "target_lod" => {
                let s = field.text().await.map_err(|e| AppError::Http {
                    status: StatusCode::BAD_REQUEST,
                    message: format!("Invalid target_lod: {}", e),
                })?;
                target_lod = Some(s.trim().to_string());
            }
            "fill_holes" => {
                let s = field.text().await.map_err(|e| AppError::Http {
                    status: StatusCode::BAD_REQUEST,
                    message: format!("Invalid fill_holes: {}", e),
                })?;
                let v = s.trim().to_ascii_lowercase();
                fill_holes = matches!(v.as_str(), "true" | "1" | "yes" | "on");
            }
            _ => {
                // Drain unknown fields to keep the parser happy.
                let _ = field.bytes().await;
            }
        }
    }

    let (orig_filename, bytes) = file_data.ok_or_else(|| AppError::Http {
        status: StatusCode::BAD_REQUEST,
        message: "Missing required field: file".to_string(),
    })?;
    let lod = target_lod.ok_or_else(|| AppError::Http {
        status: StatusCode::BAD_REQUEST,
        message: "Missing required field: target_lod".to_string(),
    })?;
    validate_lod(&lod)?;

    // Persist the raw upload --------------------------------------------------
    let uploads_root = state.settings.uploads_dir.clone();
    let raw_dir = uploads_root.join("scans").join("raw");
    let processed_dir = uploads_root.join("scans").join("processed");
    tokio::fs::create_dir_all(&raw_dir).await.map_err(|e| {
        AppError::Internal(anyhow::anyhow!(
            "Failed to create scans/raw dir: {}",
            e
        ))
    })?;
    tokio::fs::create_dir_all(&processed_dir).await.map_err(|e| {
        AppError::Internal(anyhow::anyhow!(
            "Failed to create scans/processed dir: {}",
            e
        ))
    })?;

    let safe_name = sanitize_filename(&orig_filename);
    let upload_id = Uuid::new_v4();
    let raw_filename = format!("{}-{}", upload_id, safe_name);
    let raw_disk_path: PathBuf = raw_dir.join(&raw_filename);
    tokio::fs::write(&raw_disk_path, &bytes).await.map_err(|e| {
        AppError::Internal(anyhow::anyhow!("Failed to write raw upload: {}", e))
    })?;

    let input_bytes = bytes.len() as i64;
    let raw_disk_str = raw_disk_path.to_string_lossy().to_string();

    // Insert the pending job row ---------------------------------------------
    // Output path stored in DB is the public URL pattern; nginx (or a future
    // route) maps `/uploads/scans/processed/...` → the processed_dir on disk.
    let job_id = Uuid::new_v4();
    let public_output_path =
        format!("/uploads/scans/processed/{}-{}.glb", job_id, lod);
    let processed_disk_path: PathBuf =
        processed_dir.join(format!("{}-{}.glb", job_id, lod));
    let processed_disk_str = processed_disk_path.to_string_lossy().to_string();

    sqlx::query(
        r#"
        INSERT INTO mesh_processing_jobs
            (id, actor_user_id, urn_slug, input_path, output_path,
             lod_label, fill_holes, smooth_iter, status,
             input_bytes, started_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, 5, 'pending', $8, NOW())
        "#,
    )
    .bind(job_id)
    .bind(actor_user_id)
    .bind(&urn_slug)
    .bind(&raw_disk_str)
    .bind(&public_output_path)
    .bind(&lod)
    .bind(fill_holes)
    .bind(input_bytes)
    .execute(&pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Spawn the processing task ----------------------------------------------
    let pool_clone = pool.clone();
    let lod_clone = lod.clone();
    tokio::spawn(async move {
        run_mesh_job(
            pool_clone,
            job_id,
            raw_disk_str,
            processed_disk_str,
            lod_clone,
            fill_holes,
        )
        .await;
    });

    Ok((
        StatusCode::ACCEPTED,
        Json(serde_json::json!({
            "job_id": job_id,
            "status": "pending",
            "output_path": public_output_path,
        })),
    ))
}

/// Background worker that runs the Python mesh-processor for a single job.
/// Updates the DB row through every state transition.
#[allow(dead_code)]
async fn run_mesh_job(
    pool: PgPool,
    job_id: Uuid,
    input_disk_path: String,
    output_disk_path: String,
    lod: String,
    fill_holes: bool,
) {
    // Mark running.
    if let Err(e) = sqlx::query(
        "UPDATE mesh_processing_jobs SET status = 'running', started_at = NOW() WHERE id = $1",
    )
    .bind(job_id)
    .execute(&pool)
    .await
    {
        tracing::error!(job_id = %job_id, error = %e, "failed to mark job running");
        return;
    }

    let venv_py = mesh_processor_python();
    let script = mesh_processor_script();
    let work_dir = mesh_processor_dir();

    let mut cmd = Command::new(&venv_py);
    cmd.arg(&script)
        .arg(&input_disk_path)
        .arg("--output")
        .arg(&output_disk_path)
        .arg("--lod")
        .arg(&lod)
        .arg("--quiet")
        .current_dir(&work_dir)
        .kill_on_drop(true);
    if fill_holes {
        cmd.arg("--fill-holes");
    }

    let exec_result =
        timeout(Duration::from_secs(JOB_TIMEOUT_SECS), cmd.output()).await;

    match exec_result {
        Err(_) => {
            let _ = mark_job_failed(
                &pool,
                job_id,
                &format!("timeout after {}s", JOB_TIMEOUT_SECS),
            )
            .await;
        }
        Ok(Err(spawn_err)) => {
            let _ = mark_job_failed(
                &pool,
                job_id,
                &format!("spawn failed: {}", spawn_err),
            )
            .await;
        }
        Ok(Ok(output)) => {
            let stdout = String::from_utf8_lossy(&output.stdout).to_string();
            let stderr = String::from_utf8_lossy(&output.stderr).to_string();
            if !output.status.success() {
                let exit_code = output.status.code().unwrap_or(-1);
                let err = if !stderr.is_empty() {
                    format!("exit {}: {}", exit_code, stderr)
                } else {
                    format!("exit {}: {}", exit_code, stdout)
                };
                let _ = mark_job_failed(&pool, job_id, truncate(&err, 4000)).await;
            } else {
                match serde_json::from_str::<JsonValue>(stdout.trim()) {
                    Ok(summary) => {
                        let _ = mark_job_succeeded(&pool, job_id, &summary).await;
                    }
                    Err(e) => {
                        let _ = mark_job_failed(
                            &pool,
                            job_id,
                            &format!(
                                "could not parse summary JSON: {}\nstdout: {}\nstderr: {}",
                                e,
                                truncate(&stdout, 1000),
                                truncate(&stderr, 1000)
                            ),
                        )
                        .await;
                    }
                }
            }
        }
    }
}

/// GET /api/v1/admin/mesh/jobs
pub async fn list_jobs(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Query(params): Query<JobsListQuery>,
) -> Result<impl IntoResponse, AppError> {
    authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;

    let page = params.page.unwrap_or(1).max(1);
    let per_page = params.per_page.unwrap_or(20).clamp(1, 100);
    let offset = (page - 1) as i64 * per_page as i64;

    let status = params.status.as_deref();
    let urn_slug = params.urn_slug.as_deref();

    let total: i64 = sqlx::query_scalar(
        r#"
        SELECT COUNT(*) FROM mesh_processing_jobs
        WHERE ($1::text IS NULL OR status = $1)
          AND ($2::text IS NULL OR urn_slug = $2)
        "#,
    )
    .bind(status)
    .bind(urn_slug)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let rows = sqlx::query_as::<_, MeshJobRow>(
        r#"
        SELECT id, actor_user_id, urn_slug, input_path, output_path,
               lod_label, fill_holes, smooth_iter, status,
               started_at, completed_at,
               input_bytes, output_bytes,
               size_reduction_pct::text AS size_reduction_pct,
               faces_initial, faces_final, elapsed_ms,
               summary_json, error_message, created_at
        FROM mesh_processing_jobs
        WHERE ($1::text IS NULL OR status = $1)
          AND ($2::text IS NULL OR urn_slug = $2)
        ORDER BY started_at DESC
        LIMIT $3 OFFSET $4
        "#,
    )
    .bind(status)
    .bind(urn_slug)
    .bind(per_page as i64)
    .bind(offset)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(Json(JobsListResponse {
        jobs: rows.into_iter().map(MeshJob::from).collect(),
        page,
        per_page,
        total,
    }))
}

/// GET /api/v1/admin/mesh/jobs/:id
pub async fn get_job(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let row = fetch_job(pool, id).await?;
    Ok(Json(row))
}

// ---------------------------------------------------------------------------
// Inventory handler — list GLB files available as mesh-processor inputs
// ---------------------------------------------------------------------------

#[derive(Debug, Serialize)]
pub struct InventoryEntry {
    pub name: String,
    pub size_bytes: i64,
    pub modified_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Serialize)]
pub struct InventoryResponse {
    pub root: String,
    pub models: Vec<InventoryEntry>,
}

/// Resolve the directory we list. Override via `MESH_INVENTORY_DIR` so the
/// admin tests / future container deploys don't hard-depend on the host
/// path layout.
fn inventory_dir() -> std::path::PathBuf {
    if let Ok(v) = std::env::var("MESH_INVENTORY_DIR") {
        return std::path::PathBuf::from(v);
    }
    std::path::PathBuf::from(MODELS_UPLOAD_PREFIX)
}

/// GET /api/v1/admin/mesh/inventory
///
/// Lists `*.glb` files directly inside the `models_upload/` directory. Used
/// by the admin UI to pick an input file for a reprocess job. Files are
/// returned sorted by name; sizes are reported in bytes and `modified_at`
/// uses the filesystem mtime when available.
pub async fn inventory(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    authenticate_admin(&headers, &state.settings)?;

    let root = inventory_dir();
    let root_str = root.to_string_lossy().to_string();

    let mut entries = match tokio::fs::read_dir(&root).await {
        Ok(rd) => rd,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
            // Empty inventory rather than 500 when the dir doesn't exist.
            return Ok(Json(InventoryResponse {
                root: root_str,
                models: Vec::new(),
            }));
        }
        Err(e) => {
            return Err(AppError::Internal(anyhow::anyhow!(
                "failed to read inventory dir {}: {}",
                root.display(),
                e
            )));
        }
    };

    let mut models: Vec<InventoryEntry> = Vec::new();
    while let Some(entry) = entries.next_entry().await.map_err(|e| {
        AppError::Internal(anyhow::anyhow!("dir iteration failed: {}", e))
    })? {
        let path = entry.path();
        // Only top-level *.glb files, no recursion.
        let name = match path.file_name().and_then(|s| s.to_str()) {
            Some(n) => n.to_string(),
            None => continue,
        };
        if !name.to_ascii_lowercase().ends_with(".glb") {
            continue;
        }
        let meta = match entry.metadata().await {
            Ok(m) => m,
            Err(_) => continue,
        };
        if !meta.is_file() {
            continue;
        }
        let size_bytes = meta.len() as i64;
        let modified_at: Option<DateTime<Utc>> = meta
            .modified()
            .ok()
            .map(|st| DateTime::<Utc>::from(st));

        models.push(InventoryEntry {
            name,
            size_bytes,
            modified_at,
        });
    }
    models.sort_by(|a, b| a.name.cmp(&b.name));

    Ok(Json(InventoryResponse {
        root: root_str,
        models,
    }))
}

// ---------------------------------------------------------------------------
// DB helpers
// ---------------------------------------------------------------------------

async fn fetch_job(pool: &PgPool, id: Uuid) -> Result<MeshJob, AppError> {
    let row = sqlx::query_as::<_, MeshJobRow>(
        r#"
        SELECT id, actor_user_id, urn_slug, input_path, output_path,
               lod_label, fill_holes, smooth_iter, status,
               started_at, completed_at,
               input_bytes, output_bytes,
               size_reduction_pct::text AS size_reduction_pct,
               faces_initial, faces_final, elapsed_ms,
               summary_json, error_message, created_at
        FROM mesh_processing_jobs
        WHERE id = $1
        "#,
    )
    .bind(id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "Job not found".to_string(),
    })?;
    Ok(row.into())
}

#[allow(dead_code)]
async fn mark_job_succeeded(
    pool: &PgPool,
    job_id: Uuid,
    summary: &JsonValue,
) -> Result<(), AppError> {
    let input_bytes = summary.get("input_bytes").and_then(|v| v.as_i64());
    let output_bytes = summary.get("output_bytes").and_then(|v| v.as_i64());
    let size_reduction = summary.get("size_reduction_pct").and_then(|v| v.as_f64());
    // The column is numeric(5,2). Bind the value as text and cast on the SQL
    // side; this avoids pulling in the `bigdecimal` sqlx feature.
    let size_reduction_text: Option<String> = size_reduction.map(|f| {
        let clamped = f.clamp(-999.99, 999.99);
        format!("{:.2}", clamped)
    });
    let faces_initial = summary.get("faces_initial").and_then(|v| v.as_i64());
    let faces_final = summary.get("faces_final").and_then(|v| v.as_i64());
    let elapsed_ms = summary
        .get("elapsed_ms")
        .and_then(|v| v.as_i64())
        .map(|x| x as i32);

    sqlx::query(
        r#"
        UPDATE mesh_processing_jobs
        SET status = 'succeeded',
            completed_at = NOW(),
            input_bytes = $2,
            output_bytes = $3,
            size_reduction_pct = $4::numeric,
            faces_initial = $5,
            faces_final = $6,
            elapsed_ms = $7,
            summary_json = $8
        WHERE id = $1
        "#,
    )
    .bind(job_id)
    .bind(input_bytes)
    .bind(output_bytes)
    .bind(size_reduction_text)
    .bind(faces_initial)
    .bind(faces_final)
    .bind(elapsed_ms)
    .bind(summary)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    Ok(())
}

#[allow(dead_code)]
async fn mark_job_failed(
    pool: &PgPool,
    job_id: Uuid,
    error_message: &str,
) -> Result<(), AppError> {
    sqlx::query(
        r#"
        UPDATE mesh_processing_jobs
        SET status = 'failed',
            completed_at = NOW(),
            error_message = $2
        WHERE id = $1
        "#,
    )
    .bind(job_id)
    .bind(error_message)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    Ok(())
}

#[allow(dead_code)]
fn truncate(s: &str, max: usize) -> &str {
    if s.len() <= max {
        s
    } else {
        // Find a UTF-8 boundary at or below `max`.
        let mut end = max;
        while end > 0 && !s.is_char_boundary(end) {
            end -= 1;
        }
        &s[..end]
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{
        body::Body,
        http::Request,
        routing::{get, post},
        Router,
    };
    use tower::ServiceExt;

    fn test_auth_state() -> AuthState {
        let settings = crate::config::Settings::from_env().unwrap();
        AuthState {
            pool: None,
            settings,
        }
    }

    fn test_router() -> Router {
        let state = test_auth_state();
        Router::new()
            .route("/api/v1/admin/mesh/reprocess", post(reprocess))
            .route("/api/v1/admin/mesh/inventory", get(inventory))
            .route("/api/v1/admin/mesh/jobs", get(list_jobs))
            .route("/api/v1/admin/mesh/jobs/:id", get(get_job))
            .with_state(state)
    }

    #[test]
    fn validate_lod_accepts_known() {
        for lod in ["512", "1k", "2k"] {
            assert!(validate_lod(lod).is_ok());
        }
    }

    #[test]
    fn validate_lod_rejects_unknown() {
        assert!(validate_lod("4k").is_err());
        assert!(validate_lod("").is_err());
        assert!(validate_lod("../etc").is_err());
    }

    #[test]
    fn validate_path_accepts_models_upload() {
        assert!(validate_path(
            "/opt/luuniensuki-lms/models_upload/foo.glb",
            "INVALID_INPUT_PATH",
            "input_path"
        )
        .is_ok());
        assert!(validate_path(
            "/opt/luuniensuki-lms/models_upload/sub/dir/foo.glb",
            "INVALID_INPUT_PATH",
            "input_path"
        )
        .is_ok());
    }

    #[test]
    fn validate_path_rejects_traversal_and_wrong_root() {
        assert!(validate_path(
            "/etc/passwd",
            "INVALID_INPUT_PATH",
            "input_path"
        )
        .is_err());
        assert!(validate_path(
            "/opt/luuniensuki-lms/models_upload/../etc/passwd",
            "INVALID_INPUT_PATH",
            "input_path"
        )
        .is_err());
        assert!(validate_path(
            "/opt/luuniensuki-lms/models_uploads/foo.glb",
            "INVALID_INPUT_PATH",
            "input_path"
        )
        .is_err());
        assert!(validate_path(
            "/opt/luuniensuki-lms/models_upload/foo\0bar",
            "INVALID_INPUT_PATH",
            "input_path"
        )
        .is_err());
    }

    #[test]
    fn truncate_handles_utf8() {
        assert_eq!(truncate("hello", 10), "hello");
        assert_eq!(truncate("hello world", 5), "hello");
        // Multi-byte char must not be split.
        let s = "héllo";
        let t = truncate(s, 2);
        assert!(s.starts_with(t));
    }

    #[tokio::test]
    async fn reprocess_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/admin/mesh/reprocess")
                    .header("content-type", "application/json")
                    .body(Body::from(
                        r#"{"input_path":"/opt/luuniensuki-lms/models_upload/a.glb","output_path":"/opt/luuniensuki-lms/models_upload/b.glb","lod":"512"}"#,
                    ))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn reprocess_returns_403_for_non_admin() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "user",
            &state.settings.jwt_secret_key,
            60,
        )
        .unwrap();
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/admin/mesh/reprocess")
                    .header("Authorization", format!("Bearer {}", token))
                    .header("content-type", "application/json")
                    .body(Body::from(
                        r#"{"input_path":"/opt/luuniensuki-lms/models_upload/a.glb","output_path":"/opt/luuniensuki-lms/models_upload/b.glb","lod":"512"}"#,
                    ))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::FORBIDDEN);
    }

    #[tokio::test]
    async fn list_jobs_returns_503_for_admin_without_pool() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "admin",
            &state.settings.jwt_secret_key,
            60,
        )
        .unwrap();
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/admin/mesh/jobs")
                    .header("Authorization", format!("Bearer {}", token))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn reprocess_returns_501_for_admin() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "admin",
            &state.settings.jwt_secret_key,
            60,
        )
        .unwrap();
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/admin/mesh/reprocess")
                    .header("Authorization", format!("Bearer {}", token))
                    .header("content-type", "application/json")
                    .body(Body::from(
                        r#"{"input_path":"/opt/luuniensuki-lms/models_upload/a.glb","output_path":"/opt/luuniensuki-lms/models_upload/b.glb","lod":"512"}"#,
                    ))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::NOT_IMPLEMENTED);
        let body = axum::body::to_bytes(resp.into_body(), 8192).await.unwrap();
        let parsed: serde_json::Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(
            parsed["error"]["code"], "MESH_REPROCESS_NOT_IMPLEMENTED",
            "expected the 501 envelope code"
        );
    }

    #[tokio::test]
    async fn reprocess_returns_400_for_bad_lod_before_501() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "admin",
            &state.settings.jwt_secret_key,
            60,
        )
        .unwrap();
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/admin/mesh/reprocess")
                    .header("Authorization", format!("Bearer {}", token))
                    .header("content-type", "application/json")
                    .body(Body::from(
                        r#"{"input_path":"/opt/luuniensuki-lms/models_upload/a.glb","output_path":"/opt/luuniensuki-lms/models_upload/b.glb","lod":"4k"}"#,
                    ))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::BAD_REQUEST);
    }

    #[tokio::test]
    async fn inventory_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/admin/mesh/inventory")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn inventory_returns_403_for_non_admin() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "user",
            &state.settings.jwt_secret_key,
            60,
        )
        .unwrap();
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/admin/mesh/inventory")
                    .header("Authorization", format!("Bearer {}", token))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::FORBIDDEN);
    }

    #[tokio::test]
    async fn inventory_lists_glb_files_from_temp_dir() {
        // Use a tempdir as the inventory root via MESH_INVENTORY_DIR.
        let tmp = tempfile::tempdir().unwrap();
        let glb_path = tmp.path().join("alpha.glb");
        std::fs::write(&glb_path, b"\x67\x6c\x54\x46pretend-glb").unwrap();
        let txt_path = tmp.path().join("ignore.txt");
        std::fs::write(&txt_path, b"not a glb").unwrap();
        std::env::set_var("MESH_INVENTORY_DIR", tmp.path());

        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "admin",
            &state.settings.jwt_secret_key,
            60,
        )
        .unwrap();
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/admin/mesh/inventory")
                    .header("Authorization", format!("Bearer {}", token))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        std::env::remove_var("MESH_INVENTORY_DIR");
        assert_eq!(resp.status(), StatusCode::OK);
        let body = axum::body::to_bytes(resp.into_body(), 8192).await.unwrap();
        let parsed: serde_json::Value = serde_json::from_slice(&body).unwrap();
        let models = parsed["models"].as_array().unwrap();
        assert_eq!(models.len(), 1, "only the .glb should be listed");
        assert_eq!(models[0]["name"], "alpha.glb");
        assert!(models[0]["size_bytes"].as_i64().unwrap() > 0);
    }
}
