# Onboarding Implementation Visual Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                   P0-ACT-01 ONBOARDING FEATURE                      │
│                        Implementation Map                            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  DATABASE LAYER (PostgreSQL)                                        │
├─────────────────────────────────────────────────────────────────────┤
│  Table: users                                                       │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  + onboarding_goal: VARCHAR(50) NULL                          │ │
│  │  + onboarding_completed: BOOLEAN DEFAULT false                │ │
│  │  + onboarding_completed_at: TIMESTAMP WITH TIME ZONE NULL     │ │
│  └───────────────────────────────────────────────────────────────┘ │
│  Migration: 0012_onboarding_fields.py                               │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│  MODEL LAYER (SQLAlchemy 2.0)                                       │
├─────────────────────────────────────────────────────────────────────┤
│  File: backend/models.py                                            │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  class User(Base):                                            │ │
│  │    onboarding_goal: Mapped[Optional[str]]                     │ │
│  │    onboarding_completed: Mapped[bool]                         │ │
│  │    onboarding_completed_at: Mapped[Optional[datetime]]        │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│  SCHEMA LAYER (Pydantic)                                            │
├─────────────────────────────────────────────────────────────────────┤
│  File: backend/schemas.py                                           │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  OnboardingGoalIn         - Request to save goal              │ │
│  │  OnboardingStatusOut       - Response with status             │ │
│  │  OnboardingCompleteIn      - Request to complete              │ │
│  │  OnboardingCompleteOut     - Response after completion        │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│  API LAYER (FastAPI)                                                │
├─────────────────────────────────────────────────────────────────────┤
│  File: backend/main.py                                              │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  POST /api/v1/onboarding/goals      [save goal]               │ │
│  │  GET  /api/v1/onboarding/status     [get status]              │ │
│  │  POST /api/v1/onboarding/complete   [mark complete]           │ │
│  └───────────────────────────────────────────────────────────────┘ │
│  Authentication: JWT (Required)                                     │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│  CLIENT LAYER (Frontend/Mobile)                                     │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │   Web (Next.js)  │  │  Mobile (Flutter)│  │   Admin Panel    │ │
│  │   - Onboarding   │  │  - Onboarding    │  │  - View user     │ │
│  │     screens      │  │    screens       │  │    onboarding    │ │
│  │   - Goal select  │  │  - Goal select   │  │    status        │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════

USER FLOW DIAGRAM

┌─────────────┐
│   User      │
│  Registers  │
│  or Logs In │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  GET /api/v1/onboarding/status      │
│  Check if onboarding complete       │
└──────┬──────────────────────────────┘
       │
       ├─── If completed ──────────┐
       │                           │
       │                           ▼
       │                    ┌──────────────┐
       │                    │  Redirect to │
       │                    │   Main App   │
       │                    └──────────────┘
       │
       └─── If not complete ───┐
                                │
                                ▼
                    ┌──────────────────────┐
                    │   Show Onboarding    │
                    │   Screen 1: Welcome  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Screen 2-3: Goal    │
                    │  Selection (Prompts) │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────────────────┐
                    │  POST /api/v1/onboarding/goals   │
                    │  Save: learn_culture, pass_exam, │
                    │  curiosity, professional, hobby  │
                    └──────────┬───────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Screen 4: Tutorial  │
                    │  or Final Steps      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌────────────────────────────────┐
                    │  POST /api/v1/onboarding/      │
                    │        complete                │
                    └──────────┬─────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Redirect to Main    │
                    │  App (Dashboard)     │
                    └──────────────────────┘

═══════════════════════════════════════════════════════════════════════

VALID GOAL OPTIONS

┌─────────────────┬──────────────────────────────────────────────────┐
│ Goal Value      │ Description                                      │
├─────────────────┼──────────────────────────────────────────────────┤
│ learn_culture   │ Learn about Vietnamese culture and history       │
│ pass_exam       │ Pass exams or assessments                        │
│ curiosity       │ General curiosity and exploration                │
│ professional    │ Professional development                         │
│ hobby           │ Personal hobby/interest                          │
└─────────────────┴──────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════

FILE STRUCTURE

luuniensuki-lms/
├── backend/
│   ├── models.py                    [MODIFIED] User model + 3 fields
│   ├── schemas.py                   [MODIFIED] + 4 schemas
│   └── main.py                      [MODIFIED] + 3 endpoints
│
├── migrations/
│   └── versions/
│       └── 0012_onboarding_fields.py  [NEW] Migration file
│
└── docs/ (Documentation)
    ├── P0-ACT-01_ONBOARDING_IMPLEMENTATION.md
    ├── ONBOARDING_API_REFERENCE.md
    ├── ONBOARDING_TESTING_CHECKLIST.md
    └── ONBOARDING_README.md

═══════════════════════════════════════════════════════════════════════

DEPLOYMENT STEPS

1. ✅ Code Review
   └─ Verify all files modified correctly

2. 🗄️ Database Migration
   └─ alembic upgrade head

3. 🔄 Restart Services
   └─ docker-compose restart backend

4. 🧪 Test Endpoints
   └─ Run API tests from checklist

5. 📱 Frontend Integration
   └─ Build onboarding UI

6. 📊 Monitor
   └─ Check logs and analytics

═══════════════════════════════════════════════════════════════════════

