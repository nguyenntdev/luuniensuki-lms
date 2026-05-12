# Documentation Index

File này là bản đồ tài liệu của dự án. Mục tiêu là giúp người mới hoặc contributor tìm đúng tài liệu theo nhu cầu: kỹ thuật, kiến trúc, proposal, business, UI/UX, planning và hướng nghiên cứu khoa học.

## Đọc Nhanh Theo Vai Trò

| Vai trò | Nên đọc |
| --- | --- |
| Developer mới | [Architecture](ARCHITECTURE.md), [Backend Implementation](implementation/03_Backend_Implementation.md), [Auth System](implementation/06_Auth_System.md) |
| Frontend/UI engineer | [Frontend 3D Logic](implementation/04_Frontend_3D_Logic.md), [UX Roadmap](plan/24_UX_Roadmap_Seamless_Learning.md), [3D Interactivity](plan/25_UX_3D_Interactivity_Modernization.md) |
| DevOps | [Production Checklist](PRODUCTION_CHECKLIST.md), [Deployment Checklist](DEPLOYMENT_CHECKLIST.md), [Secrets](SECRETS.md), [GitHub Actions](GITHUB_ACTIONS_SETUP.md) |
| Product/Business | [Learner Journey](curriculum/LMS_CURRICULUM_USER_JOURNEY.md), [Roadmap](plan/00_Roadmap.md), [Execution Plan](plan/13_Execution_Plan_Detailed.md) |
| Research/Innovation | [EdTech Research Innovations](EDTECH_RESEARCH_INNOVATIONS_2026.md), [Research Breakthrough Features](RESEARCH_BREAKTHROUGH_FEATURES_2026.md), [Learner Experience Improvements](LEARNER_EXPERIENCE_IMPROVEMENTS_2026.md) |

## Technical

- [Architecture](ARCHITECTURE.md) - kiến trúc hiện tại, Rust gateway, FastAPI fallback, migration strategy.
- [System Design Architecture](architecture/SYSTEM_DESIGN_ARCHITECTURE.md) - thiết kế hệ thống cấp cao.
- [Architecture Spec](architecture/01_Architecture_Spec.md) - spec kiến trúc ban đầu.
- [Backend Implementation](implementation/03_Backend_Implementation.md) - triển khai backend.
- [Frontend 3D Logic](implementation/04_Frontend_3D_Logic.md) - logic frontend và 3D.
- [Auth System](implementation/06_Auth_System.md) - xác thực và phân quyền.
- [API Docs and Dev Setup](plan/12_API_Docs_and_Dev_Setup.md) - tài liệu API và setup dev.

## Architecture

- [Architecture](ARCHITECTURE.md) - tài liệu canonical hiện tại.
- [System Design Architecture](architecture/SYSTEM_DESIGN_ARCHITECTURE.md) - tổng quan system design.
- [Mobile Architecture Overview](plan/mobile/01_Architecture_Overview.md) - kiến trúc mobile.
- [Mobile API Integration](plan/mobile/02_API_Integration.md) - tích hợp mobile/API.

## Proposal Và Planning

- [Plan Index](plan/00_Index.md) - mục lục kế hoạch cũ.
- [Roadmap](plan/00_Roadmap.md) - roadmap tổng quan.
- [Execution Plan Detailed](plan/13_Execution_Plan_Detailed.md) - kế hoạch triển khai chi tiết.
- [Backend API Backlog](plan/01_Backend_API_Backlog.md) - backlog API.
- [Testing and QA](plan/08_Testing_and_QA.md) - test và QA.
- [CI/CD](plan/09_CICD.md) - CI/CD.
- [Observability](plan/10_Observability.md) - logging, metrics, monitoring.
- [Admin Panel](plan/11_Admin_Panel.md) - admin workflows.

## Rust Migration

- [Rust Backend Refactor Plan](plan/2026-05-12-rust-backend-refactor-plan.md)
- [Rust Gateway Migration Plan](plan/2026-05-12-rust-gateway-migration-plan.md)
- [Rust Gateway Stability Plan](plan/2026-05-12-rust-gateway-stability-plan.md)
- [Rust Native Auth Guard Plan](plan/2026-05-12-rust-native-auth-guard-plan.md)
- [Rust Native Ranks Plan](plan/2026-05-12-rust-native-ranks-plan.md)
- [Rust Content Ratings Plan](plan/2026-05-12-rust-content-ratings-plan.md)

## Business Và Product

- [Learner Journey](curriculum/LMS_CURRICULUM_USER_JOURNEY.md) - hành trình học tập và curriculum.
- [Gamification](plan/03_Gamification.md) - rank, badge, streak, quest.
- [Quiz System](plan/02_Quiz_System.md) - quiz và đánh giá.
- [Data and Seeding](plan/06_Data_and_Seeding.md) - dữ liệu nội dung và seed.

## UI/UX

- [Frontend Roadmap](plan/04_Frontend_Roadmap.md)
- [UX Roadmap Seamless Learning](plan/24_UX_Roadmap_Seamless_Learning.md)
- [UX 3D Interactivity Modernization](plan/25_UX_3D_Interactivity_Modernization.md)
- [Learner Experience Improvements 2026](LEARNER_EXPERIENCE_IMPROVEMENTS_2026.md)
- [3D Assets Integration](plan/05_3D_Assets_Integration.md)

## Scientific Research

Nhóm tài liệu này định hướng cách sản phẩm dùng nghiên cứu khoa học học tập, AI, gamification và di sản số.

- [EdTech Research Innovations 2026](EDTECH_RESEARCH_INNOVATIONS_2026.md)
- [Research Breakthrough Features 2026](RESEARCH_BREAKTHROUGH_FEATURES_2026.md)
- [Learner Experience Improvements 2026](LEARNER_EXPERIENCE_IMPROVEMENTS_2026.md)

Hướng nghiên cứu nên ưu tiên:

- retrieval-augmented learning cho tri thức di sản
- adaptive learning dựa trên mastery và spaced repetition
- embodied/3D learning cho hiện vật lịch sử
- learning analytics cho retention, engagement và misconception detection
- AI tutor evaluation: correctness, grounding, safety, feedback quality
- cultural heritage digitization: provenance, explainability, source citation

## Deployment Và Operations

- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md)
- [Production Checklist](PRODUCTION_CHECKLIST.md)
- [Deployment Cuudinh](DEPLOYMENT_CUUDINH.md)
- [Secrets](SECRETS.md)
- [GitHub Actions Setup](GITHUB_ACTIONS_SETUP.md)
- [Deployment Guide](implementation/07_Deployment_Guide.md)

## Content Và Data

- [Content Seed](architecture/02_Content_Seed.md)
- [Enriched JSON Schema](content/ENRICHED_JSON_SCHEMA.md)
- [Data and Seeding](plan/06_Data_and_Seeding.md)
- [DB Migrations Alembic](plan/07_DB_Migrations_Alembic.md)

## Mobile

- [Mobile Index](plan/mobile/00_Mobile_Index.md)
- [Mobile Architecture Overview](plan/mobile/01_Architecture_Overview.md)
- [Mobile API Integration](plan/mobile/02_API_Integration.md)
- [Mobile MVP Checklist](plan/mobile/22_Checklist_MVP.md)

## Quy Ước Cập Nhật Docs

- Khi thay đổi kiến trúc production, cập nhật [Architecture](ARCHITECTURE.md).
- Khi thêm phase migration Rust, thêm file trong `docs/plan/`.
- Khi thêm tài liệu lớn, link vào file index này.
- Khi tài liệu cũ sai hoặc trùng, ưu tiên sửa hoặc đánh dấu superseded thay vì để nhiều nguồn mâu thuẫn.
