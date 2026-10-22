"""
Generate Mock Call-site Registry for W00-A03 (V5-T003).
Scans frontend, mobile, and backend call-sites where mock data, hardcoded fallbacks,
or skeleton placeholders are present, mapping them to target endpoints and risk levels.
"""

import json
import os
import re
from pathlib import Path

ROOT_DIR = Path("/home/clue/Documents/luuniensuki-lms")
ARTIFACT_PATH = ROOT_DIR / "artifacts/implementation/W00/W00_A03_mock_callsite_registry.json"

SCAN_SPECS = [
    {
        "file": "frontend/src/lib/rbpc/inquiries.ts",
        "patterns": [
            ("SEED_PARTNER_INQUIRIES", "SEED_PARTNER_INQUIRIES preloaded dataset", "GAP-003", "P0", "/api/v1/rbpc/inquiries"),
            ("provide resilient simulated result", "submitInquiryToApi fallback fabricated success", "GAP-001", "P0", "/api/v1/rbpc/inquiries"),
            ("matchedSeed = SEED_PARTNER_INQUIRIES.find", "fetchInquiryStatusByToken fallback seed matching", "GAP-002", "P0", "/api/v1/rbpc/inquiries/track/{token}"),
            ("updatePartnerInquiryStatusApi", "updatePartnerInquiryStatusApi silent fallback", "GAP-004", "P0", "/api/v1/rbpc/inquiries/{id}/status"),
        ]
    },
    {
        "file": "frontend/src/app/rbpc/partner/page.tsx",
        "patterns": [
            ("SEED_PARTNER_INQUIRIES", "Dashboard preloads SEED_PARTNER_INQUIRIES fallback", "GAP-005", "P0", "/api/v1/rbpc/inquiries")
        ]
    },
    {
        "file": "frontend/src/lib/imperial/map-api.ts",
        "patterns": [
            ("FALLBACK_ACTIVE_MAP_RESPONSE", "Active map fallback returns local object when API unavailable", "GAP-011", "P1", "/api/v1/imperial/map/active"),
            ("FALLBACK_ZONES", "Fallback zones returns local array on error", "GAP-011", "P1", "/api/v1/imperial/zones"),
            ("FALLBACK_SITES", "Fallback sites returns local site catalog", "GAP-011", "P1", "/api/v1/imperial/sites"),
            ("FALLBACK_ANNOTATIONS", "Fallback annotations on error", "GAP-006", "P0", "/api/v1/imperial/annotations"),
            ("saveAnnotationsToApi", "Annotation mutations fall back to local simulated response", "GAP-006", "P0", "/api/v1/imperial/annotations"),
            ("exportImperialData", "Publish/export fallback returning local data", "GAP-014", "P1", "/api/v1/imperial/export")
        ]
    },
    {
        "file": "frontend/src/lib/imperial/submissions-api.ts",
        "patterns": [
            ("INITIAL_STUDENT_SUBMISSIONS", "Mock student work and grades seeded into localStorage", "GAP-007", "P0", "/api/v1/classrooms/{id}/submissions"),
            ("SUBMISSIONS_STORAGE_KEY", "Client-side localStorage as grade authority", "GAP-013", "P1", "/api/v1/classrooms/{id}/grades")
        ]
    },
    {
        "file": "frontend/src/lib/imperial/v51-api.ts",
        "patterns": [
            ("FALLBACK_ART_DETAILS", "Art details static fallback array", "GAP-016", "P1", "/api/v1/imperial/art-details"),
            ("FALLBACK_LEARNING_MEDIA", "Learning media static fallback array", "GAP-016", "P1", "/api/v1/imperial/media")
        ]
    },
    {
        "file": "mobile/lib/routing/app_router.dart",
        "patterns": [
            ("QuestsPlaceholder", "Quests placeholder widget on active route", "GAP-010", "P1", "mobile feature: quests"),
            ("QuestDetailPlaceholder", "Quest detail placeholder widget on active route", "GAP-010", "P1", "mobile feature: quest_detail"),
            ("ExplorePlaceholder", "Explore placeholder definition in app_router.dart", "GAP-010", "P1", "mobile feature: explore"),
            ("CollectionPlaceholder", "Collection placeholder definition in app_router.dart", "GAP-010", "P1", "mobile feature: collection"),
            ("AchievementsPlaceholder", "Achievements placeholder definition", "GAP-010", "P1", "mobile feature: achievements"),
            ("ProfilePlaceholder", "Profile placeholder definition", "GAP-010", "P1", "mobile feature: profile"),
            ("UrnViewerPlaceholder", "Urn viewer placeholder definition", "GAP-010", "P1", "mobile feature: urn_viewer"),
            ("MotifDetailPlaceholder", "Motif detail placeholder definition", "GAP-010", "P1", "mobile feature: motif_detail"),
            ("LessonPlaceholder", "Lesson placeholder definition", "GAP-010", "P1", "mobile feature: lesson"),
            ("QuizPlaceholder", "Quiz placeholder definition", "GAP-010", "P1", "mobile feature: quiz"),
            ("SettingsPlaceholder", "Settings placeholder definition", "GAP-010", "P1", "mobile feature: settings")
        ]
    },
    {
        "file": "mobile/lib/features/practice/presentation/providers/practice_provider.dart",
        "patterns": [
            ("MockQuizData.mockQuestions", "Practice provider serves MockQuizData instead of backend review API", "GAP-010", "P1", "/api/v1/review/due")
        ]
    },
    {
        "file": "mobile/lib/features/notifications/presentation/providers/notifications_provider.dart",
        "patterns": [
            ("MockNotifications.items", "Notifications provider loads hardcoded MockNotifications", "GAP-010", "P1", "/api/v1/notifications")
        ]
    },
    {
        "file": "mobile/lib/features/social/presentation/providers/friends_provider.dart",
        "patterns": [
            ("addMockFriends", "Friends notifier exposes addMockFriends injecting synthetic friends", "GAP-010", "P1", "/api/v1/social/friends")
        ]
    }
]

def scan_files():
    registry_items = []
    
    for spec in SCAN_SPECS:
        file_rel = spec["file"]
        file_path = ROOT_DIR / file_rel
        if not file_path.exists():
            continue
            
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
        for term, desc, gap_id, priority, target_endpoint in spec["patterns"]:
            matches = []
            for idx, line in enumerate(lines, start=1):
                if term in line:
                    matches.append(idx)
            
            if matches:
                registry_items.append({
                    "gap_id": gap_id,
                    "priority": priority,
                    "file_path": file_rel,
                    "line_numbers": matches,
                    "target_term": term,
                    "description": desc,
                    "target_backend_endpoint": target_endpoint,
                    "status": "FLAGGED_FOR_ELIMINATION"
                })
                
    artifact = {
        "version": "v6.0-w00",
        "baseline_source_sha": "54da2beb71f3df70e1f00b215ae0fb1a850eb263",
        "summary": {
            "total_callsites": len(registry_items),
            "p0_count": sum(1 for item in registry_items if item["priority"] == "P0"),
            "p1_count": sum(1 for item in registry_items if item["priority"] == "P1"),
            "p2_count": sum(1 for item in registry_items if item["priority"] == "P2"),
        },
        "registry": registry_items,
        "policy": {
            "production_mock_success_allowed": False,
            "demo_mode_isolation_required": True,
            "offline_outbox_required_for_mutations": True
        }
    }
    
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_PATH, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)
        
    print(f"Wrote {len(registry_items)} mock call-sites to {ARTIFACT_PATH}")
    print(f"P0: {artifact['summary']['p0_count']}, P1: {artifact['summary']['p1_count']}")

if __name__ == "__main__":
    scan_files()
