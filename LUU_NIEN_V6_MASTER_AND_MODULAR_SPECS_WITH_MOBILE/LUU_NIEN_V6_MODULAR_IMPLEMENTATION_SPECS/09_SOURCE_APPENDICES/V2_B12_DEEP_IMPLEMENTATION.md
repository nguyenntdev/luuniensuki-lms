# V2 B12: source-derived engineering detail

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V2.B12`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## B12. GENERATED CODE ANCHOR INVENTORY — CHO PHÉP ĐỊNH VỊ IMPLEMENTATION

Phần này được sinh từ AST/regex cấu trúc source ZIP, **không chạy ứng dụng**, chỉ để tìm file/line cho dev. Nếu schema được sửa, phải regenerate. Không thể dùng bảng này thay thế runtime OpenAPI hoặc migrations thực.
### Models: `backend/history_models.py`

| Class (line) | DB table | Mapped field inventory |
|---|---|---|
| `HistoricalEntity` L232 | `historical_entities` | `id`, `entity_type`, `slug`, `name_vi`, `name_en`, `name_han_nom`, `alternative_names`, `summary_vi`, `summary_en`, `start_date`, `end_date`, `date_precision`, `latitude`, `longitude`, `geo_precision`, `thumbnail_asset_id`, `publication_status`, `content_version`, `created_by`, `updated_by`, `created_at`, `updated_at`, `deleted_at`, `content_scope` |
| `HistoricalSource` L274 | `historical_sources` | `id`, `source_type`, `title`, `subtitle`, `author_text`, `editor_text`, `publisher`, `publication_year`, `publication_date`, `edition`, `volume`, `issue`, `pages`, `isbn`, `issn`, `doi`, `url`, `archive_url`, `repository_identifier`, `language`, `citation_text`, `rights_status`, `license`, `attribution_text`, `public_display_allowed`, `derivative_allowed`, `verification_status`, `accessed_at`, `created_by`, `created_at`, `updated_at`, `content_scope` |
| `HistoricalClaim` L316 | `historical_claims` | `id`, `entity_id`, `claim_key`, `claim_type`, `statement_vi`, `statement_en`, `valid_from`, `valid_to`, `date_precision`, `confidence`, `verification_status`, `origin`, `risk_level`, `review_notes`, `created_by`, `reviewed_by`, `reviewed_at`, `verified_by`, `verified_at`, `created_at`, `updated_at`, `supersedes_claim_id`, `is_current`, `content_scope` |
| `HistoricalClaimSource` L360 | `historical_claim_sources` | `claim_id`, `source_id`, `support_type`, `locator_type`, `page_start`, `page_end`, `chapter`, `section`, `figure`, `folio`, `inscription_location`, `quotation_excerpt`, `quotation_language`, `editor_note`, `created_by`, `created_at` |
| `HistoricalEntityRelation` L391 | `historical_entity_relations` | `id`, `subject_entity_id`, `predicate`, `object_entity_id`, `claim_id`, `source_id`, `confidence`, `verification_status`, `valid_from`, `valid_to`, `created_by`, `created_at`, `updated_at` |
| `HistoricalGeography` L419 | `historical_geographies` | `entity_id`, `historical_name`, `modern_name`, `historical_geometry`, `modern_geometry`, `valid_from`, `valid_to`, `geo_precision`, `mapping_status`, `source_claim_id`, `notes` |
| `HistoricalAsset` L442 | `historical_assets` | `id`, `asset_type`, `storage_url`, `thumbnail_url`, `mime_type`, `width`, `height`, `duration`, `byte_size`, `sha256`, `rights_status`, `license`, `attribution`, `source_origin`, `public_display_allowed`, `derivative_allowed`, `entity_id`, `created_at` |
| `HistoricalContentAuditLog` L471 | `historical_content_audit_log` | `id`, `actor_id`, `action`, `resource_type`, `resource_id`, `before_json`, `after_json`, `reason`, `request_id`, `created_at` |
| `HistoryStory` L490 | `history_stories` | `id`, `slug`, `title_vi`, `title_en`, `summary_vi`, `summary_en`, `hero_image_url`, `blocks`, `status`, `publication_status`, `featured`, `created_by`, `created_at`, `updated_at`, `published_at` |
| `HistoryCollection` L525 | `history_collections` | `id`, `owner_id`, `slug`, `title_vi`, `title_en`, `description_vi`, `status`, `visibility`, `entity_ids`, `source_ids`, `story_ids`, `question_ids`, `created_at`, `updated_at`, `published_at` |

### Models: `backend/models_rbpc.py`

| Class (line) | DB table | Mapped field inventory |
|---|---|---|
| `HeritagePlace` L181 | `heritage_places` | `id`, `slug`, `name_vi`, `name_en`, `entity_type`, `heritage_category`, `parent_id`, `official_designation`, `official_reference_id`, `period_label`, `historical_state`, `location_lat`, `location_lon`, `geo_precision`, `current_access_status`, `access_notes`, `visitor_summary_vi`, `visitor_summary_en`, `historical_summary_vi`, `historical_summary_en`, `editorial_status`, `content_scope`, `thumbnail_url`, `published_at`, `created_at`, `updated_at` |
| `HeritageHeritageRelation` L298 | `heritage_heritage_relations` | `id`, `from_place_id`, `to_place_id`, `relationship_type`, `claim_id`, `review_state`, `created_at` |
| `HeritageSourceEvidence` L350 | `heritage_source_evidence` | `id`, `place_id`, `source_url`, `source_title`, `source_author`, `publisher`, `publication_year`, `cited_section`, `cited_page`, `retrieved_at`, `statement`, `interpretation_note`, `evidence_status`, `reuse_rights`, `reviewer_id`, `reviewed_at`, `content_scope`, `created_at`, `updated_at` |
| `HeritageMediaAsset` L422 | `heritage_media_assets` | `id`, `place_id`, `media_type`, `source_platform`, `original_url`, `title`, `creator_name`, `creator_url`, `model_uid`, `license_label`, `license_url`, `noai`, `commercial_use_status`, `embed_permission_status`, `accuracy_grade`, `provenance_notes`, `attribution_text`, `content_status`, `embed_url`, `rights_reviewed_by`, `rights_reviewed_at`, `checked_at`, `content_scope`, `created_at`, `updated_at` |
| `RbpcCreator` L524 | `rbpc_creators` | `id`, `slug`, `public_name`, `craft_tradition`, `craft_tradition_en`, `approved_bio_vi`, `approved_bio_en`, `approved_portrait_url`, `public_region`, `display_consent_ref`, `consent_status`, `is_verified`, `years_of_practice`, `generation_lineage`, `heritage_place_id`, `reviewer_id`, `created_at`, `updated_at` |
| `RbpcExperience` L607 | `rbpc_experiences` | `id`, `slug`, `creator_id`, `provider_name`, `provider_id`, `title_vi`, `title_en`, `description_vi`, `description_en`, `area_public`, `duration_minutes`, `pricing_display`, `indicative_price_amount`, `currency`, `availability_mode`, `publication_state`, `cancellation_policy_text_vi`, `cancellation_policy_text_en`, `max_party_size`, `languages_supported`, `notice`, `created_at`, `updated_at` |
| `RbpcStory` L680 | `rbpc_stories` | `id`, `slug`, `title_vi`, `title_en`, `intro_vi`, `intro_en`, `place_id`, `creator_id`, `experience_id`, `primary_asset_url`, `category`, `historical_context_json`, `approved_summary_vi`, `approved_summary_en`, `status`, `rights_id`, `version`, `reading_time_minutes`, `reviewed_by`, `reviewed_at`, `published_at`, `content_scope`, `created_at`, `updated_at` |
| `RbpcClaimEvidence` L766 | `rbpc_claim_evidence` | `id`, `story_id`, `statement`, `locale`, `claim_category`, `source_ref_id`, `source_title`, `source_url`, `support_type`, `citation_label`, `evidence_excerpt_private`, `review_status`, `reviewed_by`, `created_at` |
| `RbpcInquiry` L820 | `rbpc_inquiries` | `id`, `public_ref`, `experience_id`, `provider_id`, `name`, `contact_channel`, `contact_value`, `desired_date`, `party_size`, `message`, `consent_version`, `consent_time_utc`, `privacy_accepted`, `state`, `internal_note`, `idempotency_key`, `opaque_token`, `retention_due_at`, `created_at`, `updated_at` |
| `RbpcEvent` L911 | `rbpc_events` | `id`, `event_name`, `anonymous_session_id`, `story_id`, `experience_id`, `heritage_place_id`, `occurred_at`, `consent_scope`, `payload`, `created_at` |
| `RbpcContentAudit` L959 | `rbpc_content_audit` | `id`, `entity_type`, `entity_id`, `action`, `actor_id`, `previous_hash`, `new_hash`, `diff_payload`, `approved_scope`, `created_at` |

### Models: `backend/models.py`

| Class (line) | DB table | Mapped field inventory |
|---|---|---|
| `User` L257 | `users` | `id`, `email`, `password_hash`, `display_name`, `avatar_url`, `bio`, `username`, `starting_urn_id`, `is_profile_public`, `ai_personalization_enabled`, `role`, `total_xp`, `current_streak`, `longest_streak`, `streak_freezes`, `onboarding_goal`, `onboarding_completed`, `onboarding_completed_at`, `xp_boost_active`, `xp_boost_expires_at`, `xp_boost_multiplier`, `birth_year`, `age_verified`, `age_verified_at`, `push_permission_prompted`, `last_active_at`, `created_at`, `updated_at` |
| `UserNotificationSettings` L498 | `user_notification_settings` | `id`, `user_id`, `push_enabled`, `push_token`, `push_platform`, `email_enabled`, `streak_reminders`, `daily_mission_reminders`, `weekly_digest`, `marketing_enabled`, `quiet_hours_start`, `quiet_hours_end`, `created_at`, `updated_at` |
| `Urn` L560 | `urns` | `id`, `slug`, `name`, `name_han`, `represents`, `description`, `model_url`, `thumbnail_url`, `display_order`, `is_demo`, `created_at` |
| `AnalyticsEvent` L595 | `analytics_events` | `id`, `user_id`, `event_name`, `path`, `payload`, `session_id`, `cohort`, `event_category`, `device_info`, `created_at` |
| `Funnel` L630 | `funnels` | `id`, `user_id`, `funnel_type`, `stage`, `started_at`, `stage_timestamps`, `completed_at`, `metadata_json` |
| `Motif` L664 | `motifs` | `id`, `urn_id`, `mesh_name`, `name`, `name_en`, `category`, `rarity`, `content_rating`, `pos_x`, `pos_y`, `pos_z`, `bounding_radius`, `cam_pos_x`, `cam_pos_y`, `cam_pos_z`, `cam_look_at_x`, `cam_look_at_y`, `cam_look_at_z`, `thumbnail_url`, `silhouette_url`, `is_demo`, `is_active`, `display_order`, `created_at`, `updated_at` |
| `LessonContent` L754 | `lesson_content` | `id`, `motif_id`, `intro_text`, `description`, `historical_context`, `symbolism`, `fun_fact`, `audio_narration_url`, `additional_images`, `video_url`, `is_published`, `is_ai_generated`, `preview_eligible`, `content_validation_status`, `content_rating`, `difficulty_level`, `estimated_time_minutes`, `version`, `last_editor_id`, `published_at`, `publish_note`, `status`, `submitted_for_review_at`, `reviewed_by_id`, `reviewed_at`, `review_notes`, `created_at`, `updated_at` |
| `ContentVersion` L855 | `content_versions` | `id`, `content_type`, `content_id`, `version`, `data`, `editor_id`, `change_note`, `created_at` |
| `LessonPrerequisite` L885 | `lesson_prerequisites` | `id`, `lesson_id`, `prerequisite_lesson_id`, `is_strict`, `created_at` |
| `UserProgress` L934 | `user_progress` | `id`, `user_id`, `motif_id`, `ease_factor`, `interval_days`, `repetitions`, `next_review_at`, `last_reviewed_at`, `review_history`, `created_at`, `updated_at`, `status`, `discovered_at`, `lesson_viewed_at`, `learned_at`, `mastered_at`, `quiz_attempts`, `quiz_best_score`, `xp_earned`, `created_at`, `updated_at` |
| `QuizQuestion` L1026 | `quiz_questions` | `id`, `motif_id`, `urn_id`, `question_type`, `question_text`, `options`, `correct_answer`, `target_mesh_name`, `difficulty`, `skill_type`, `explanation`, `is_published`, `is_active`, `content_validation_status`, `skill_dimensions`, `entity_id`, `claim_ids`, `source_ids`, `answer_contract`, `status`, `submitted_for_review_at`, `reviewed_by_id`, `reviewed_at`, `review_notes`, `created_by_id`, `created_at` |
| `QuizAttempt` L1129 | `quiz_attempts` | `id`, `user_id`, `motif_id`, `score`, `max_score`, `percentage`, `answers`, `time_taken_seconds`, `completed_at` |
| `QuizHintRequest` L1165 | `quiz_hint_requests` | `id`, `user_id`, `question_id`, `hint_type`, `hint_text`, `heart_cost`, `rag_sources`, `created_at` |
| `UserSkillLevel` L1207 | `user_skill_levels` | `id`, `user_id`, `skill_type`, `skill_level`, `total_questions`, `correct_answers`, `skill_dimensions`, `last_updated_at`, `created_at` |
| `UrnExam` L1251 | `urn_exams` | `id`, `urn_id`, `questions`, `passing_score`, `xp_reward` |
| `UrnExamAttempt` L1279 | `urn_exam_attempts` | `id`, `user_id`, `urn_exam_id`, `score`, `passed`, `time_taken`, `answers`, `created_at` |
| `Badge` L1314 | `badges` | `id`, `slug`, `name`, `name_en`, `description`, `icon_url`, `category`, `tier`, `xp_bonus`, `tier_xp_bonus`, `unlock_criteria`, `is_secret`, `is_active`, `created_at` |
| `UserBadge` L1359 | `user_badges` | `id`, `user_id`, `badge_id`, `current_tier`, `earned_at` |
| `UserMilestone` L1392 | `user_milestones` | `id`, `user_id`, `milestone_type`, `achieved_at`, `context_data`, `celebrated`, `created_at` |
| `Certificate` L1427 | `certificates` | `id`, `user_id`, `code`, `issuer_name`, `reason_type`, `reason_id`, `status`, `issued_at` |
| `Quest` L1460 | `quests` | `id`, `slug`, `name`, `description`, `category`, `display_order`, `is_active`, `content_rating`, `prerequisite_id`, `created_at`, `updated_at` |
| `QuestStep` L1516 | `quest_steps` | `id`, `quest_id`, `title`, `description`, `display_order`, `created_at` |
| `QuestObjective` L1547 | `quest_objectives` | `id`, `quest_step_id`, `objective_type`, `target_value`, `params`, `display_order` |
| `QuestReward` L1574 | `quest_rewards` | `id`, `quest_id`, `reward_type`, `amount`, `badge_slug`, `metadata_payload` |
| `QuestProgress` L1597 | `quest_progress` | `id`, `user_id`, `quest_id`, `status`, `started_at`, `completed_at` |
| `Classroom` L1631 | `classes` | `id`, `name`, `description`, `teacher_id`, `class_code`, `max_students`, `is_archived`, `settings`, `created_at`, `updated_at` |
| `ClassMember` L1682 | `class_members` | `id`, `class_id`, `user_id`, `role`, `joined_at` |
| `LiveSession` L1714 | `live_sessions` | `id`, `classroom_id`, `created_by_id`, `room_name`, `idempotency_key`, `title`, `status`, `starts_at`, `ended_at`, `session_metadata`, `created_at`, `updated_at` |
| `LiveParticipant` L1778 | `live_participants` | `id`, `live_session_id`, `user_id`, `participant_identity`, `display_name`, `role`, `is_ai`, `joined_at`, `left_at`, `connection_metadata` |
| `LiveEvent` L1833 | `live_events` | `id`, `live_session_id`, `event_type`, `event_source`, `participant_identity`, `participant_user_id`, `payload`, `created_at` |
| `SessionTranscript` L1872 | `session_transcripts` | `id`, `live_session_id`, `source_event_id`, `speaker_type`, `speaker_identity`, `speaker_user_id`, `content_encrypted`, `confidence`, `started_at`, `ended_at`, `transcript_metadata`, `created_at`, `expires_at` |
| `SessionSummary` L1926 | `session_summaries` | `id`, `live_session_id`, `summary_encrypted`, `highlights`, `citations`, `rubric_overview`, `summary_metadata`, `created_by`, `created_at`, `expires_at` |
| `SessionAction` L1958 | `session_actions` | `id`, `live_session_id`, `action_type`, `actor_identity`, `actor_user_id`, `status`, `cost_usd`, `payload`, `created_at`, `expires_at` |
| `LiveRateLimitLog` L1996 | `live_rate_limit_logs` | `id`, `bucket`, `user_id`, `live_session_id`, `created_at` |
| `QuestAssignment` L2033 | `quest_assignments` | `id`, `class_id`, `quest_id`, `assigned_by_id`, `due_at`, `assigned_at`, `points_override`, `notes` |
| `AssignmentProgress` L2080 | `assignment_progress` | `id`, `assignment_id`, `user_id`, `status`, `completed_at` |
| `Recommendation` L2112 | `recommendations` | `id`, `user_id`, `source`, `items`, `created_at` |
| `AIJob` L2136 | `ai_jobs` | `id`, `user_id`, `job_type`, `status`, `provider`, `prompt`, `response`, `error`, `retry_count`, `created_at`, `updated_at` |
| `RagDocument` L2175 | `rag_documents` | `id`, `title`, `content`, `source_type`, `source_path`, `is_active`, `embedding`, `embedding_model`, `embedding_updated_at`, `created_at`, `updated_at` |
| `RagSettings` L2210 | `rag_settings` | `id`, `system_instruction`, `prompt_prefix`, `model_override`, `temperature`, `max_documents`, `embedding_enabled`, `hybrid_alpha`, `created_at`, `updated_at` |
| `EmbeddingJob` L2240 | `embedding_jobs` | `id`, `status`, `total_documents`, `processed_documents`, `started_at`, `completed_at`, `error_message`, `created_by_id`, `created_at` |
| `ContentProvenance` L2278 | `content_provenance` | `id`, `content_type`, `content_id`, `provider`, `model`, `generated_at`, `metadata_payload` |
| `ContentFlag` L2296 | `content_flags` | `id`, `user_id`, `content_type`, `content_id`, `reason`, `created_at` |
| `DailyMission` L2335 | `daily_missions` | `id`, `slug`, `name`, `description`, `mission_type`, `target_count`, `xp_reward`, `is_active`, `created_at` |
| `UserDailyMission` L2372 | `user_daily_missions` | `id`, `user_id`, `mission_id`, `mission_date`, `current_count`, `is_completed`, `completed_at`, `xp_awarded`, `created_at` |
| `Tag` L2421 | `tags` | `id`, `slug`, `name`, `tag_type`, `description`, `is_active`, `created_at` |
| `ContentTag` L2450 | `content_tags` | `id`, `tag_id`, `content_type`, `content_id`, `created_at` |
| `StreakReward` L2482 | `streak_rewards` | `id`, `user_id`, `streak_day`, `reward_type`, `reward_amount`, `awarded_at`, `created_at` |
| `WeeklyQuest` L2520 | `weekly_quests` | `id`, `slug`, `name`, `description`, `category`, `week_number`, `year`, `target_count`, `xp_reward`, `badge_slug`, `is_recurring`, `is_active`, `created_at` |
| `UserWeeklyQuest` L2572 | `user_weekly_quests` | `id`, `user_id`, `quest_id`, `week_start_date`, `current_count`, `is_completed`, `completed_at`, `xp_awarded`, `created_at` |
| `LessonCache` L2623 | `lesson_cache` | `id`, `user_id`, `lesson_id`, `cached_at`, `cache_version`, `file_size_bytes`, `is_valid`, `expires_at` |
| `AuditLog` L2667 | `audit_logs` | `id`, `user_id`, `action`, `resource_type`, `resource_id`, `old_value`, `new_value`, `ip_address`, `user_agent`, `created_at` |
| `UserSession` L2711 | `user_sessions` | `id`, `user_id`, `session_id`, `started_at`, `last_active_at`, `ended_at`, `device_type`, `platform`, `app_version`, `is_active` |
| `PasswordResetToken` L2756 | `password_reset_tokens` | `id`, `user_id`, `token_hash`, `created_at`, `expires_at`, `used_at`, `ip_address`, `user_agent` |
| `AbuseReport` L2787 | `abuse_reports` | `id`, `reporter_id`, `reported_user_id`, `content_type`, `content_id`, `reason`, `description`, `evidence_urls`, `status`, `priority`, `assigned_to_id`, `resolution_notes`, `resolved_at`, `created_at` |
| `CrashReport` L2858 | `crash_reports` | `id`, `user_id`, `session_id`, `error_type`, `error_message`, `stack_trace`, `platform`, `app_version`, `device_model`, `os_version`, `additional_data`, `created_at`, `is_resolved`, `resolved_by_id`, `resolved_at` |
| `AppVersion` L2917 | `app_versions` | `id`, `platform`, `version`, `version_code`, `min_required_version`, `is_current`, `force_update`, `release_notes`, `download_url`, `released_at`, `created_at` |
| `UserHearts` L2978 | `user_hearts` | `id`, `user_id`, `current_hearts`, `max_hearts`, `last_heart_lost_at`, `hearts_refill_at`, `unlimited_until`, `streak_freezes`, `updated_at`, `created_at` |
| `HeartTransaction` L3029 | `heart_transactions` | `id`, `user_id`, `user_hearts_id`, `amount`, `reason`, `balance_after`, `metadata_json`, `created_at` |
| `GuestPreview` L3073 | `guest_previews` | `id`, `session_id`, `preview_lesson_id`, `started_at`, `completed_at`, `converted_to_user_id`, `device_info`, `created_at` |
| `UserContentInteraction` L3129 | `user_content_interactions` | `id`, `user_id`, `content_type`, `content_id`, `interaction_type`, `duration_seconds`, `metadata_json`, `created_at` |
| `SpacedRepetitionCard` L3179 | `spaced_repetition_cards` | `id`, `user_id`, `motif_id`, `ease_factor`, `interval_days`, `repetitions`, `next_review_at`, `last_reviewed_at`, `review_history`, `created_at`, `updated_at` |
| `AIConversation` L3244 | `ai_conversations` | `id`, `user_id`, `title`, `context_type`, `context_id`, `is_active`, `message_count`, `created_at`, `updated_at` |
| `AIMessage` L3301 | `ai_messages` | `id`, `conversation_id`, `role`, `content`, `tokens_used`, `created_at` |
| `UserLearningPath` L3343 | `user_learning_paths` | `id`, `user_id`, `path_date`, `recommended_lessons`, `recommended_reviews`, `recommended_quizzes`, `estimated_time_minutes`, `completed_items`, `is_completed`, `generated_at`, `completed_at` |
| `UserFollow` L3399 | `user_follows` | `id`, `follower_id`, `following_id`, `created_at` |
| `FriendRequest` L3432 | `friend_requests` | `id`, `from_user_id`, `to_user_id`, `status`, `created_at`, `responded_at` |
| `UserShare` L3487 | `user_shares` | `id`, `user_id`, `share_type`, `content_id`, `caption`, `visibility`, `share_url`, `view_count`, `created_at` |
| `StudentProgressSnapshot` L3531 | `student_progress_snapshots` | `id`, `student_id`, `classroom_id`, `snapshot_date`, `lessons_completed`, `quizzes_passed`, `average_quiz_score`, `motifs_discovered`, `current_streak`, `xp_earned`, `time_spent_minutes`, `created_at` |
| `PushNotification` L3593 | `push_notifications` | `id`, `user_id`, `title`, `body`, `notification_type`, `data_payload`, `status`, `scheduled_for`, `sent_at`, `delivered_at`, `error_message`, `created_at` |
| `EmailTemplate` L3657 | `email_templates` | `id`, `key`, `name`, `subject_template`, `body_html`, `body_text`, `is_active`, `created_at`, `updated_at` |
| `ScheduledEmail` L3717 | `scheduled_emails` | `id`, `user_id`, `template_id`, `scheduled_for`, `status`, `context_data`, `sent_at`, `error_message`, `created_at` |
| `FeatureFlag` L3781 | `feature_flags` | `id`, `key`, `name`, `description`, `is_enabled`, `rollout_percentage`, `user_whitelist`, `user_blacklist`, `rules`, `created_by_id`, `created_at`, `updated_at` |
| `Experiment` L3833 | `experiments` | `id`, `key`, `name`, `description`, `variants`, `target_audience`, `is_active`, `start_date`, `end_date`, `created_by_id`, `created_at` |
| `UserExperimentAssignment` L3885 | `user_experiment_assignments` | `id`, `user_id`, `experiment_id`, `variant_key`, `assigned_at` |
| `ExperimentEvent` L3926 | `experiment_events` | `id`, `experiment_id`, `user_id`, `assignment_id`, `event_type`, `event_name`, `event_value`, `metadata_json`, `created_at` |
| `ExperimentMetricEvent` L3979 | `experiment_metric_events` | `id`, `experiment_id`, `user_id`, `variant`, `metric_name`, `metric_value`, `metadata_json`, `created_at` |
| `UserLeaderboardSettings` L4024 | `user_leaderboard_settings` | `id`, `user_id`, `show_on_global`, `show_real_name`, `preferred_leaderboard`, `created_at`, `updated_at` |
| `UserLeague` L4066 | `user_leagues` | `id`, `user_id`, `tier`, `weekly_xp`, `week_start`, `week_end`, `rank_in_tier`, `promoted`, `demoted`, `created_at`, `updated_at` |
| `RevokedRefreshToken` L4120 | `revoked_refresh_tokens` | `jti`, `user_id`, `revoked_at`, `expires_at` |
| `HistoryQuestionType` L4143 | `history_question_types` | `id`, `key`, `label_vi`, `label_en`, `sort_order` |

### Endpoint source anchors: `backend/routers/rbpc.py`

| Method | Path decorator | Handler@line |
|---|---|---|
| `GET` | `/api/v1/rbpc/config` | `get_rbpc_config` L352 |
| `GET` | `/api/v1/rbpc/stories` | `list_rbpc_stories` L372 |
| `GET` | `/api/v1/rbpc/stories/{slug}` | `get_rbpc_story_detail` L406 |
| `POST` | `/api/v1/rbpc/cultural-bridge` | `rbpc_cultural_bridge_ask` L505 |
| `GET` | `/api/v1/rbpc/creators/{slug}` | `get_rbpc_creator` L529 |
| `GET` | `/api/v1/rbpc/experiences/{slug}` | `get_rbpc_experience` L558 |
| `POST` | `/api/v1/rbpc/inquiries` | `create_rbpc_inquiry` L586 |
| `GET` | `/api/v1/rbpc/inquiries/status/{opaqueToken}` | `get_inquiry_status_by_token` L746 |
| `GET` | `/api/v1/rbpc/impact` | `get_rbpc_impact_metrics` L782 |
| `GET` | `/api/v1/rbpc/partner/inquiries` | `list_partner_inquiries` L884 |
| `PATCH` | `/api/v1/rbpc/partner/inquiries/{id}` | `update_partner_inquiry_status` L931 |
| `POST` | `/api/v1/rbpc/editor/creators/{id}/consent` | `update_creator_consent` L1013 |

### Endpoint source anchors: `backend/routers/heritage.py`

| Method | Path decorator | Handler@line |
|---|---|---|
| `GET` | `/api/v1/heritage/places` | `list_heritage_places` L258 |
| `GET` | `/api/v1/heritage/search` | `search_heritage_places` L399 |
| `GET` | `/api/v1/heritage/places/{slug}` | `get_heritage_place_detail` L494 |
| `GET` | `/api/v1/heritage/places/{slug}/detail` | `get_heritage_place_detail` L494 |
| `GET` | `/api/v1/heritage/places/{slug}/media` | `get_heritage_place_media` L537 |
| `GET` | `/api/v1/heritage/places/{slug}/3d` | `get_heritage_place_3d_models` L578 |

### Endpoint source anchors: `backend/routers/history_learning.py`

| Method | Path decorator | Handler@line |
|---|---|---|
| `POST` | `/api/v1/history/questions/{question_id}/grade` | `grade_history_question` L75 |
| `GET` | `/api/v1/history/questions` | `list_history_questions` L105 |
| `GET` | `/api/v1/history/questions/{question_id}` | `get_history_question` L138 |
| `POST` | `/api/v1/history/questions` | `create_history_question` L153 |
| `GET` | `/api/v1/history/skills/{user_id}` | `get_history_skills` L218 |

### Endpoint source anchors: `backend/routers/history.py`

| Method | Path decorator | Handler@line |
|---|---|---|
| `GET` | `/api/v1/history/entities` | `list_history_entities` L67 |
| `GET` | `/api/v1/history/entities/by-slug/{slug}` | `get_history_entity_by_slug` L89 |
| `GET` | `/api/v1/history/entities/{entity_id}` | `get_history_entity` L97 |
| `GET` | `/api/v1/history/entities/{entity_id}/claims` | `list_entity_claims` L108 |
| `GET` | `/api/v1/history/claims/{claim_id}` | `get_history_claim` L133 |
| `GET` | `/api/v1/history/claims/{claim_id}/sources` | `list_claim_sources` L144 |
| `GET` | `/api/v1/history/sources` | `list_history_sources` L152 |
| `GET` | `/api/v1/history/sources/{source_id}` | `get_history_source` L171 |
| `GET` | `/api/v1/history/entities/{entity_id}/relations` | `list_entity_relations` L182 |
| `GET` | `/api/v1/history/entities/{entity_id}/graph` | `entity_knowledge_graph` L195 |
| `GET` | `/api/v1/history/reliefs/{urn_slug}/{relief_slug}/hotspot` | `relief_hotspot` L272 |
| `GET` | `/api/v1/history/events` | `list_history_events` L321 |
| `GET` | `/api/v1/history/entities/{entity_id}/geography` | `get_entity_geography` L362 |
| `GET` | `/api/v1/history/map` | `history_map` L370 |
| `GET` | `/api/v1/history/urns` | `history_urns` L424 |
| `GET` | `/api/v1/history/search` | `search_history` L454 |
| `POST` | `/api/v1/admin/history/entities` | `create_history_entity` L486 |
| `PATCH` | `/api/v1/admin/history/entities/{entity_id}` | `update_history_entity` L506 |
| `POST` | `/api/v1/admin/history/sources` | `create_history_source` L530 |
| `PATCH` | `/api/v1/admin/history/sources/{source_id}` | `update_history_source` L545 |
| `POST` | `/api/v1/admin/history/claims` | `create_history_claim` L566 |
| `PATCH` | `/api/v1/admin/history/claims/{claim_id}` | `update_history_claim` L583 |
| `POST` | `/api/v1/admin/history/claims/{claim_id}/sources` | `attach_claim_source` L604 |
| `POST` | `/api/v1/admin/history/claims/{claim_id}/transition` | `transition_claim_status` L628 |
| `POST` | `/api/v1/admin/history/relations` | `create_history_relation` L666 |
| `DELETE` | `/api/v1/admin/history/relations/{relation_id}` | `delete_history_relation` L696 |
| `PUT` | `/api/v1/admin/history/entities/{entity_id}/geography` | `upsert_history_geography` L708 |
| `POST` | `/api/v1/admin/history/assets` | `create_history_asset` L734 |
| `GET` | `/api/v1/admin/history/audit` | `list_history_audit` L760 |

### Endpoint source anchors: `backend/routers/classrooms.py`

| Method | Path decorator | Handler@line |
|---|---|---|
| `GET` | `/api/v1/classrooms` | `list_classrooms` L519 |
| `POST` | `/api/v1/classrooms` | `create_classroom` L578 |
| `GET` | `/api/v1/classrooms/{classroom_id}` | `get_classroom` L614 |
| `PUT` | `/api/v1/classrooms/{classroom_id}` | `update_classroom` L680 |
| `DELETE` | `/api/v1/classrooms/{classroom_id}` | `delete_classroom` L710 |
| `POST` | `/api/v1/classrooms/{classroom_id}/archive` | `archive_classroom` L733 |
| `POST` | `/api/v1/classrooms/{classroom_id}/unarchive` | `unarchive_classroom` L762 |
| `POST` | `/api/v1/classrooms/join` | `join_classroom` L787 |
| `DELETE` | `/api/v1/classrooms/{classroom_id}/members/{member_id}` | `remove_member` L865 |
| `GET` | `/api/v1/classrooms/enrolled` | `get_enrolled_classrooms` L891 |
| `GET` | `/api/v1/classrooms/{classroom_id}/assignments` | `list_classroom_assignments` L943 |
| `POST` | `/api/v1/classrooms/{classroom_id}/assignments` | `create_assignment` L1012 |
| `PUT` | `/api/v1/classrooms/{classroom_id}/assignments/{assignment_id}` | `update_assignment` L1099 |
| `DELETE` | `/api/v1/classrooms/{classroom_id}/assignments/{assignment_id}` | `delete_assignment` L1169 |
| `GET` | `/api/v1/assignments/mine` | `get_my_assignments` L1193 |
| `POST` | `/api/v1/assignments/{assignment_id}/submit` | `submit_assignment` L1244 |
| `GET` | `/api/v1/classrooms/{classroom_id}/students/{student_id}/progress` | `get_student_progress` L1282 |
| `GET` | `/api/v1/classrooms/{classroom_id}/progress` | `get_class_progress_summary` L1320 |
| `GET` | `/api/v1/classrooms/{classroom_id}/leaderboard` | `get_class_leaderboard` L1350 |
| `GET` | `/api/v1/classrooms/{classroom_id}/export` | `export_class_progress` L1386 |
| `GET` | `/api/v1/classes` | `list_classes_legacy` L1491 |
| `POST` | `/api/v1/classes` | `create_class_legacy` L1540 |
| `GET` | `/api/v1/classes/{class_id}` | `get_class_detail` L1567 |
| `POST` | `/api/v1/classes/{class_id}/members` | `add_class_member` L1656 |
| `DELETE` | `/api/v1/classes/{class_id}/members/{user_id}` | `remove_class_member` L1719 |
| `POST` | `/api/v1/classes/{class_id}/assignments` | `assign_quest_to_class` L1762 |
| `GET` | `/api/v1/admin/experiments/{experiment_id}/assignments` | `get_experiment_assignments` L1817 |

### Endpoint source anchors: `backend/routers/auth.py`

| Method | Path decorator | Handler@line |
|---|---|---|
| `POST` | `/api/v1/auth/register` | `register` L59 |
| `POST` | `/api/v1/auth/login` | `login` L125 |
| `GET` | `/api/v1/auth/me` | `me` L163 |
| `POST` | `/api/v1/auth/refresh` | `refresh_session` L168 |
| `POST` | `/api/v1/auth/logout` | `logout` L238 |
| `POST` | `/api/v1/auth/forgot-password` | `forgot_password` L255 |
| `POST` | `/api/v1/auth/reset-password` | `reset_password` L311 |

### Endpoint source anchors: `backend/routers/ai.py`

| Method | Path decorator | Handler@line |
|---|---|---|
| `GET` | `/api/v1/users/me/ai-jobs` | `list_ai_jobs` L552 |
| `POST` | `/api/v1/users/me/ai-jobs/{job_id}/retry` | `retry_ai_job` L581 |
| `POST` | `/api/v1/ai/tutor` | `ai_tutor` L644 |
| `POST` | `/api/v1/ai/tutor/stream` | `ai_tutor_stream` L705 |
| `POST` | `/api/v1/ai/qa` | `ai_qa` L807 |
| `POST` | `/api/v1/ai/qa/stream` | `ai_qa_stream` L861 |
| `POST` | `/api/v1/ai/summary` | `ai_summary` L929 |
| `POST` | `/api/v1/ai/flashcards` | `ai_flashcards` L982 |
| `POST` | `/api/v1/ai/feedback` | `ai_feedback` L1051 |
| `POST` | `/api/v1/ai/coach` | `ai_coach` L1131 |
| `POST` | `/api/v1/ai/explain` | `ai_explain` L1215 |
| `GET` | `/api/v1/ai/review-plan` | `ai_review_plan` L1261 |
| `GET` | `/api/v1/ai/insights` | `get_learning_insights` L1326 |
| `GET` | `/api/v1/ai/insights/{user_id}` | `get_learning_insights_for_user` L1361 |
| `POST` | `/api/v1/ai/lessons/generate` | `ai_generate_lesson` L1420 |
| `POST` | `/api/v1/ai/quizzes/generate` | `ai_generate_quiz` L1586 |
| `POST` | `/api/v1/ai/diagnostic` | `ai_diagnostic` L1674 |
| `GET` | `/api/v1/ai/conversations` | `list_ai_conversations` L1713 |
| `POST` | `/api/v1/ai/conversations` | `create_ai_conversation` L1782 |
| `GET` | `/api/v1/ai/conversations/{conversation_id}` | `get_ai_conversation` L1832 |
| `POST` | `/api/v1/ai/conversations/{conversation_id}/messages` | `send_message_to_conversation` L1876 |
| `DELETE` | `/api/v1/ai/conversations/{conversation_id}` | `delete_ai_conversation` L1939 |

### Snapshot identity

- ZIP SHA-256 recomputed in V2: `6afbae524382bebfa9675f22a0ea86187a9596ecd5d35bc4727d3a8a80600e31`.
- Raw source root: `luuniensuki-lms-feat-rbpc-cultural-bridge-2026/`.
- Không có `.git` trong snapshot; commit SHA chỉ được coi là doc claim nếu xuất hiện ở file nội bộ, không khẳng định HEAD live.

---

