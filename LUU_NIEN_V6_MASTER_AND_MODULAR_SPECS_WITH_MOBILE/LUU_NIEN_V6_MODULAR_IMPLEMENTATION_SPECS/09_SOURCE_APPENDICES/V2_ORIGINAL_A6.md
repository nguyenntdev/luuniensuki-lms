# V2 original archival technical chapter — A6

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## A6. Migrations: đầu nhánh theo static revision/down_revision graph

**71 migration definitions; 15 terminal revisions theo static graph**. Lệnh `alembic heads --verbose` là nguồn kiểm chứng cuối cùng, chưa chạy vì thiếu driver/deps môi trường.

- `0012_analytics_taxonomy` — `migrations/versions/0012_analytics_taxonomy.py`
- `0012_onboarding_fields` — `migrations/versions/0012_onboarding_fields.py`
- `0013_content_tagging` — `migrations/versions/0013_content_tagging.py`
- `0013_weekly_quests` — `migrations/versions/0013_weekly_quests.py`
- `0014` — `migrations/versions/0014_notification_settings.py`
- `0014_crash_reports` — `migrations/versions/0014_crash_reports.py`
- `0019_app_versions` — `migrations/versions/0019_app_versions.py`
- `0021_classroom_enhancements` — `migrations/versions/0021_classroom_enhancements.py`
- `0024` — `migrations/versions/0024_user_content_interactions.py`
- `0024_user_learning_paths` — `migrations/versions/0024_user_learning_paths.py`
- `0031_user_shares` — `migrations/versions/0031_user_shares.py`
- `0032_email_scheduling` — `migrations/versions/0032_email_scheduling.py`
- `0033_feature_flags_experiments` — `migrations/versions/0033_feature_flags_experiments.py`
- `0054_rbpc_heritage_schema` — `migrations/versions/0054_rbpc_heritage_schema.py`
- `0056_imperial_sources_claims_scope` — `migrations/versions/0056_imperial_sources_claims_scope.py`

