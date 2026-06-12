# Documentation Index

Bản đồ tài liệu của **Lưu Niên Sử Kí LMS**. Phần đầu là tài liệu **Engineering / Ops** (đã được rà soát cho khớp codebase hiện tại). Phần sau liên kết tới tài liệu **Product & Research** (do nhóm nội dung/nghiên cứu sở hữu — chỉ liên kết, không chỉnh sửa ở đây).

## Đọc Nhanh Theo Vai Trò

| Vai trò | Nên đọc |
| --- | --- |
| Developer mới | [Architecture](ARCHITECTURE.md), [Backend Implementation](implementation/03_Backend_Implementation.md), [Auth System](implementation/06_Auth_System.md) |
| Frontend/3D engineer | [Frontend 3D Logic](implementation/04_Frontend_3D_Logic.md), [Architecture](ARCHITECTURE.md) |
| DevOps / SRE | [Production Checklist](PRODUCTION_CHECKLIST.md), [Deployment Guide](DEPLOYMENT_CUUDINH.md), [Secrets](SECRETS.md), [GitHub Actions](GITHUB_ACTIONS_SETUP.md) |
| Bảo mật | [Architecture — Security](ARCHITECTURE.md#kiến-trúc-bảo-mật-security-hardening), [Secrets](SECRETS.md) |
| AI / Live classroom | [AI Teacher LiveKit Plan](implementation/08_AI_TEACHER_LIVEKIT_3D_PLAN.md), [AI Teacher Prod Runbook](implementation/09_AI_TEACHER_LIVEKIT_PROD_RUNBOOK.md) |

---

## Engineering — Kiến Trúc & Triển Khai

Tài liệu canonical, đã đối chiếu với code hiện tại (FastAPI đã modular hoá, Rust gateway, frontend TypeScript, security hardening).

- [Architecture](ARCHITECTURE.md) — kiến trúc tổng thể: package backend Python đã modular hoá, Rust axum gateway + fallback, frontend Next.js/TS, và kiến trúc bảo mật.
- [Secrets Management](SECRETS.md) — secret bắt buộc cho cả hai backend và cơ chế fail-closed (Python `config.py` + Rust `config.rs`).
- [Production Checklist](PRODUCTION_CHECKLIST.md) — checklist deploy production hợp nhất (đã gộp checklist QA/deploy cũ).
- [Deployment Guide](DEPLOYMENT_CUUDINH.md) — hướng dẫn deploy VPS từng bước (Docker Compose prod + override, Certbot).
- [GitHub Actions Setup](GITHUB_ACTIONS_SETUP.md) — cấu hình CI (`ci.yml`) và CD (`deploy.yml`).

### Implementation Guides

- [Backend Implementation](implementation/03_Backend_Implementation.md)
- [Frontend & 3D Logic](implementation/04_Frontend_3D_Logic.md)
- [Auth System](implementation/06_Auth_System.md)
- [AI Teacher LiveKit 3D Plan](implementation/08_AI_TEACHER_LIVEKIT_3D_PLAN.md)
- [AI Teacher LiveKit Prod Runbook](implementation/09_AI_TEACHER_LIVEKIT_PROD_RUNBOOK.md)

### Architecture Specs (lịch sử)

- [Master Architecture Spec](architecture/01_Architecture_Spec.md) — spec sản phẩm + schema DB nền tảng (v1.0, có trước backend Rust; tham chiếu lịch sử). Nguồn canonical hiện tại là [ARCHITECTURE.md](ARCHITECTURE.md).
- [Content Seed](architecture/02_Content_Seed.md) — quy ước seed nội dung.

---

## Rust Backend Migration

Các plan migration sang Rust (theo từng phase). Nguồn tổng hợp: [Full Rust Backend Migration Ledger](plan/full-rust-backend-migration-ledger.md).

- [Rust Backend Refactor Plan](plan/2026-05-12-rust-backend-refactor-plan.md)
- [Rust Gateway Migration Plan](plan/2026-05-12-rust-gateway-migration-plan.md)
- [Rust Native Auth Guard Plan](plan/2026-05-12-rust-native-auth-guard-plan.md)
- [Rust Native Ranks Plan](plan/2026-05-12-rust-native-ranks-plan.md)
- [Rust Content Ratings Plan](plan/2026-05-12-rust-content-ratings-plan.md)
- [Rust DB Foundation Plan](plan/2026-05-13-rust-db-foundation-plan.md)
- [Rust PostgreSQL SCRAM Client Plan](plan/2026-05-13-rust-postgres-scram-client-plan.md)
- [Rust Native Tags Plan](plan/2026-05-13-rust-native-tags-plan.md)
- [Rust Native Badges Plan](plan/2026-05-13-rust-native-badges-plan.md)
- [Rust Native User Streak Plan](plan/2026-05-14-rust-native-user-streak-plan.md)

---

## Product & Research

> Các tài liệu dưới đây thuộc sở hữu của nhóm nội dung/nghiên cứu. Mục này chỉ liên kết để tiện tra cứu — không chỉnh sửa từ luồng engineering.

- [EdTech Research Innovations 2026](EDTECH_RESEARCH_INNOVATIONS_2026.md)
- [Feature Proposals 2026](FEATURE_PROPOSALS_2026_NEW.md)
- [Learner Experience Improvements 2026](LEARNER_EXPERIENCE_IMPROVEMENTS_2026.md)
- [Research Breakthrough Features 2026](RESEARCH_BREAKTHROUGH_FEATURES_2026.md)
- [Conference Paper Match Analysis](CONFERENCE_PAPER_MATCH_ANALYSIS.md)

### Curriculum, Content & Planning (subfolders)

- `curriculum/` — hành trình học tập & curriculum, ví dụ [Learner Journey](curriculum/LMS_CURRICULUM_USER_JOURNEY.md).
- `content/` — schema & dữ liệu nội dung, ví dụ [Enriched JSON Schema](content/ENRICHED_JSON_SCHEMA.md).
- `plan/` — roadmap, backlog, gamification, UX, mobile và các phase plan (gồm `plan/mobile/`).

---

## Quy Ước Cập Nhật Docs

- Khi thay đổi kiến trúc production, cập nhật [ARCHITECTURE.md](ARCHITECTURE.md) (nguồn canonical).
- Khi đổi secret bắt buộc hoặc validator, cập nhật [SECRETS.md](SECRETS.md).
- Khi đổi quy trình deploy hoặc CI/CD, cập nhật [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md), [DEPLOYMENT_CUUDINH.md](DEPLOYMENT_CUUDINH.md), [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md).
- Khi thêm phase migration Rust, thêm file trong `docs/plan/` và link ở mục Rust Backend Migration.
- Khi tài liệu cũ sai hoặc trùng, ưu tiên sửa hoặc xoá bản superseded thay vì để nhiều nguồn mâu thuẫn.
