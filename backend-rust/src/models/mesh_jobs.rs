//! DTOs for the admin mesh-processing endpoints.
//!
//! The concrete struct definitions live alongside the route handlers in
//! `crate::routes::admin_mesh` so that response shapes track the SQL
//! schema closely. This module simply re-exports them under the
//! `crate::models::mesh_jobs` path so callers can depend on a stable
//! `models/` location, matching the layout of the other domain modules.

#[allow(unused_imports)]
pub use crate::routes::admin_mesh::{
    InventoryEntry, InventoryResponse, JobsListQuery, JobsListResponse, MeshJob,
    ReprocessRequest,
};
