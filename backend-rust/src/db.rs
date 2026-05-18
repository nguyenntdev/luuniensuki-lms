use std::time::Duration;

use sqlx::postgres::{PgPool, PgPoolOptions};

use crate::config::Settings;

/// Create a connection pool configured from application settings.
///
/// Uses runtime `sqlx::query` / `query_as` only (no compile-time
/// `query!` macros) so the build does not require a live database.
pub async fn pool(settings: &Settings) -> sqlx::Result<PgPool> {
    PgPoolOptions::new()
        .max_connections(settings.database_max_connections)
        .acquire_timeout(Duration::from_secs(5))
        .connect(&settings.database_url)
        .await
}

/// Verify the pool can execute a trivial query.
pub async fn ping(pool: &PgPool) -> Result<(), sqlx::Error> {
    sqlx::query_scalar::<_, i32>("SELECT 1")
        .fetch_one(pool)
        .await
        .map(|_| ())
}
