# -*- coding: utf-8 -*-
"""Unit and integration tests for STTT Imperial City extended historical sources & claims.

Validates:
1. Integrity of JSON files:
   - data/imperial/historical_sources_extended.json
   - data/imperial/monument_claims_matrix.json
2. Exhaustive bibliography of verified primary dynastic chronicles and archival repositories:
   - Đại Nam Thực Lục Chính Biên (Tiền biên, Đệ nhất kỷ, Đệ nhị kỷ, Đệ tam kỷ, Đệ tứ kỷ)
   - Khâm Định Đại Nam Hội Điển Sự Lệ (HĐSL)
   - Đại Nam Nhất Thống Chí (ĐNNTC)
   - EFEO & Albert Kahn archives
   - UNESCO World Heritage Dossier #678 (1993)
3. Full coverage across all 16 monuments in Đại Nội Huế:
   - Each monument has at least 2 verified primary source citations
4. Zero forbidden legacy terms across all source records.
5. Idempotent seeding execution into database session.
"""
from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

from backend.base_model import Base
from backend.history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
)
from scripts.imperial.audit_no_legacy_content import (
    FORBIDDEN_TERMS,
    scan_file_for_violations,
)
from scripts.imperial.seed_extended_sources import (
    CONTENT_SCOPE_IMPERIAL,
    seed_extended_sources,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCES_FILE = REPO_ROOT / "data" / "imperial" / "historical_sources_extended.json"
CLAIMS_FILE = REPO_ROOT / "data" / "imperial" / "monument_claims_matrix.json"
SITES_FILE = REPO_ROOT / "data" / "imperial" / "zones_and_sites.json"

EXPECTED_16_MONUMENTS = (
    "ngo-mon",
    "cau-trung-dao",
    "san-dai-trieu-nghi",
    "dien-thai-hoa",
    "the-to-mieu",
    "hien-lam-cac",
    "hung-to-mieu",
    "trieu-to-mieu",
    "dai-cung-mon",
    "dien-can-chanh",
    "dien-kien-trung",
    "duyet-thi-duong",
    "thai-binh-lau",
    "cung-dien-tho",
    "cung-truong-sanh",
    "dien-phung-tien",
)

VALID_CONFIDENCE_LEVELS = {"verified", "probable", "disputed"}
VALID_EVIDENCE_TYPES = {"chính sử", "thư tịch cổ", "ảnh tư liệu", "kết quả khảo cổ học"}


# --------------------------------------------------------------------------- #
# 1. JSON Files Integrity & Content Scope Tests
# --------------------------------------------------------------------------- #
class TestExtendedSourcesJSONIntegrity:
    """Verifies that extended sources and claims matrix JSON files are well-formed and valid."""

    def test_files_exist(self):
        assert SOURCES_FILE.exists(), f"Missing {SOURCES_FILE}"
        assert CLAIMS_FILE.exists(), f"Missing {CLAIMS_FILE}"
        assert SITES_FILE.exists(), f"Missing {SITES_FILE}"

    def test_content_scope_integrity(self):
        sources_data = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
        claims_data = json.loads(CLAIMS_FILE.read_text(encoding="utf-8"))

        assert sources_data.get("content_scope") == CONTENT_SCOPE_IMPERIAL
        assert claims_data.get("content_scope") == CONTENT_SCOPE_IMPERIAL

    def test_sources_bibliography_structure(self):
        sources_data = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
        bibliography = sources_data.get("bibliography", [])
        assert len(bibliography) >= 10, "Bibliography should contain at least 10 authoritative sources"

        seen_ids = set()
        seen_uuids = set()

        for item in bibliography:
            # Identifier checks
            src_id = item.get("id")
            assert src_id and isinstance(src_id, str), f"Invalid source id in {item}"
            assert src_id not in seen_ids, f"Duplicate source id: {src_id}"
            seen_ids.add(src_id)

            uuid_str = item.get("uuid")
            assert uuid_str, f"Source {src_id} missing uuid"
            parsed_uuid = UUID(uuid_str)
            assert str(parsed_uuid) not in seen_uuids, f"Duplicate source uuid: {uuid_str}"
            seen_uuids.add(str(parsed_uuid))

            # Required bibliographic fields
            assert item.get("title"), f"Source {src_id} missing title"
            assert item.get("source_type"), f"Source {src_id} missing source_type"
            assert item.get("citation_text"), f"Source {src_id} missing citation_text"
            assert item.get("rights_status"), f"Source {src_id} missing rights_status"
            assert item.get("verification_status") == "verified"


# --------------------------------------------------------------------------- #
# 2. Required Dynastic Chronicles & Repositories Coverage
# --------------------------------------------------------------------------- #
class TestRequiredBibliographyChronicles:
    """Ensures ĐNTL across reigns, HĐSL, ĐNNTC, EFEO, Albert Kahn, and UNESCO are present."""

    @pytest.fixture
    def bibliography(self) -> list[dict]:
        data = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
        return data.get("bibliography", [])

    def test_dai_nam_thuc_luc_reigns_present(self, bibliography):
        titles_and_subtitles = [
            f"{s.get('title', '')} {s.get('subtitle', '')}" for s in bibliography
        ]
        combined_text = " ".join(titles_and_subtitles)

        # Tiền biên & 4 Kỷ Đệ nhất (Gia Long), Đệ nhị (Minh Mạng), Đệ tam (Thiệu Trị), Đệ tứ (Tự Đức)
        assert "Tiền Biên" in combined_text or "Tiền biên" in combined_text
        assert "Đệ nhất kỷ" in combined_text or "Gia Long" in combined_text
        assert "Đệ nhị kỷ" in combined_text or "Minh Mạng" in combined_text
        assert "Đệ tam kỷ" in combined_text or "Thiệu Trị" in combined_text
        assert "Đệ tứ kỷ" in combined_text or "Tự Đức" in combined_text

    def test_kham_dinh_hoi_dien_su_le_present(self, bibliography):
        found = any(
            "Khâm Định Đại Nam Hội Điển Sự Lệ" in s.get("title", "")
            for s in bibliography
        )
        assert found, "Khâm Định Đại Nam Hội Điển Sự Lệ must be present in bibliography"

    def test_dai_nam_nhat_thong_chi_present(self, bibliography):
        found = any(
            "Đại Nam Nhất Thống Chí" in s.get("title", "")
            for s in bibliography
        )
        assert found, "Đại Nam Nhất Thống Chí must be present in bibliography"

    def test_efeo_and_albert_kahn_present(self, bibliography):
        has_efeo = any(
            "EFEO" in s.get("title", "") or "Viễn Đông Bác Cổ" in s.get("title", "")
            for s in bibliography
        )
        has_kahn = any(
            "Albert Kahn" in s.get("title", "") for s in bibliography
        )
        assert has_efeo, "EFEO photographic archives must be present"
        assert has_kahn, "Albert Kahn Autochrome collection must be present"

    def test_unesco_dossier_present(self, bibliography):
        found = any(
            "UNESCO" in s.get("title", "") or "678" in str(s.get("short_code", "")) or "678" in str(s.get("volume", ""))
            for s in bibliography
        )
        assert found, "UNESCO World Heritage Dossier #678 must be present"

    def test_dong_khanh_dia_du_chi_present(self, bibliography):
        found = any(
            "Đồng Khánh Địa Dư Chí" in s.get("title", "")
            for s in bibliography
        )
        assert found, "Đồng Khánh Địa Dư Chí must be present in bibliography"

    def test_bavh_present(self, bibliography):
        found = any(
            "BAVH" in s.get("title", "") or "Đô Thành Hiếu Cổ" in s.get("title", "") or s.get("short_code") == "BAVH"
            for s in bibliography
        )
        assert found, "Bulletin des Amis du Vieux Hué (BAVH) must be present in bibliography"


# --------------------------------------------------------------------------- #
# 3. Monument Claims Matrix & Citation Rules
# --------------------------------------------------------------------------- #
class TestMonumentClaimsMatrix:
    """Verifies all 16 monuments have at least 2 verified primary source citations."""

    @pytest.fixture
    def claims_data(self) -> dict:
        return json.loads(CLAIMS_FILE.read_text(encoding="utf-8"))

    @pytest.fixture
    def sources_data(self) -> dict:
        return json.loads(SOURCES_FILE.read_text(encoding="utf-8"))

    def test_all_16_monuments_represented(self, claims_data):
        claims = claims_data.get("claims", [])
        monument_slugs = {c["monument_slug"] for c in claims}

        for req_slug in EXPECTED_16_MONUMENTS:
            assert req_slug in monument_slugs, f"Missing claims for required monument '{req_slug}'"

    def test_each_monument_has_at_least_two_verified_citations(self, claims_data, sources_data):
        claims = claims_data.get("claims", [])
        valid_source_ids = {s["id"] for s in sources_data.get("bibliography", [])}

        claims_by_site: dict[str, list[dict]] = {slug: [] for slug in EXPECTED_16_MONUMENTS}
        for c in claims:
            slug = c.get("monument_slug")
            if slug in claims_by_site:
                claims_by_site[slug].append(c)

        for slug, site_claims in claims_by_site.items():
            assert len(site_claims) >= 2, f"Monument '{slug}' has fewer than 2 total claims ({len(site_claims)})"

            verified_primary_citations = []
            for c in site_claims:
                # Field presence checks
                assert c.get("claim_id"), f"Missing claim_id in {c}"
                assert c.get("statement_vi"), f"Missing statement_vi in {c.get('claim_id')}"
                assert c.get("confidence") in VALID_CONFIDENCE_LEVELS, f"Invalid confidence in {c.get('claim_id')}"
                assert c.get("evidence_type") in VALID_EVIDENCE_TYPES, f"Invalid evidence_type in {c.get('claim_id')}"
                assert c.get("source_id") in valid_source_ids, (
                    f"Claim {c.get('claim_id')} references unknown source_id '{c.get('source_id')}'"
                )
                assert c.get("volume"), f"Claim {c.get('claim_id')} missing volume"
                assert c.get("page_locator"), f"Claim {c.get('claim_id')} missing page_locator"

                if (
                    c.get("confidence") == "verified"
                    and c.get("evidence_type") in VALID_EVIDENCE_TYPES
                ):
                    verified_primary_citations.append(c)

            assert len(verified_primary_citations) >= 2, (
                f"Monument '{slug}' has {len(verified_primary_citations)} verified primary citations, expected >= 2"
            )

    def test_destructions_1947_1968_covered(self, claims_data):
        claims = claims_data.get("claims", [])
        c_1947 = [c for c in claims if "1947" in c.get("statement_vi", "") or "1947" in c.get("uncertainty_notes", "")]
        c_1968 = [c for c in claims if "1968" in c.get("statement_vi", "") or "1968" in c.get("uncertainty_notes", "")]
        assert len(c_1947) >= 3, f"Expected at least 3 claims covering 1947 destructions, got {len(c_1947)}"
        assert len(c_1968) >= 3, f"Expected at least 3 claims covering 1968 destructions, got {len(c_1968)}"

    def test_modern_restorations_covered(self, claims_data):
        claims = claims_data.get("claims", [])
        modern_years = ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]
        c_modern = [
            c for c in claims
            if any(y in (c.get("statement_vi", "") + " " + c.get("uncertainty_notes", "")) for y in modern_years)
        ]
        assert len(c_modern) >= 5, f"Expected at least 5 claims covering modern restorations (2020-2026), got {len(c_modern)}"


# --------------------------------------------------------------------------- #
# 4. Zero Forbidden Legacy Terms Across All Records
# --------------------------------------------------------------------------- #
class TestNoForbiddenLegacyTermsInExtendedCorpus:
    """Audit check ensuring zero forbidden legacy terms exist across all files."""

    def test_sources_extended_json_clean(self):
        violations = scan_file_for_violations(SOURCES_FILE)
        assert violations == [], (
            f"Found forbidden terms in {SOURCES_FILE}: "
            + ", ".join(f"{v.matched_term} at line {v.line_number}" for v in violations)
        )

    def test_monument_claims_matrix_json_clean(self):
        violations = scan_file_for_violations(CLAIMS_FILE)
        assert violations == [], (
            f"Found forbidden terms in {CLAIMS_FILE}: "
            + ", ".join(f"{v.matched_term} at line {v.line_number}" for v in violations)
        )

    def test_seed_script_clean(self):
        script_file = REPO_ROOT / "scripts" / "imperial" / "seed_extended_sources.py"
        violations = scan_file_for_violations(script_file)
        assert violations == [], (
            f"Found forbidden terms in {script_file}: "
            + ", ".join(f"{v.matched_term} at line {v.line_number}" for v in violations)
        )

    def test_in_memory_text_scan(self):
        for path in (SOURCES_FILE, CLAIMS_FILE):
            content = path.read_text(encoding="utf-8").lower()
            for term in FORBIDDEN_TERMS:
                assert term not in content, f"Forbidden term '{term}' found in {path.name}"


# --------------------------------------------------------------------------- #
# 5. Seeding Idempotency Integration Test
# --------------------------------------------------------------------------- #
class TestSeedExtendedSourcesExecution:
    """Verifies that seed_extended_sources executes cleanly and idempotently."""

    @pytest.fixture
    def test_session(self):
        """Create an in-memory SQLite database session with required tables."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(
            engine,
            tables=[
                HistoricalSource.__table__,
                HistoricalEntity.__table__,
                HistoricalClaim.__table__,
                HistoricalClaimSource.__table__,
            ],
        )
        SessionLocal = sessionmaker(bind=engine)
        with SessionLocal() as session:
            yield session

    def test_idempotent_seeding(self, test_session: Session):
        sources_data = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
        claims_data = json.loads(CLAIMS_FILE.read_text(encoding="utf-8"))

        # Run 1: initial seed
        stats1 = seed_extended_sources(
            session=test_session,
            sources_data=sources_data,
            claims_data=claims_data,
            dry_run=False,
        )
        assert stats1["sources_seeded"] >= 10
        assert stats1["entities_seeded"] == 16
        assert stats1["claims_seeded"] >= 48
        assert stats1["claim_sources_seeded"] >= 48

        # Run 2: idempotent re-seed (must not crash, must not duplicate rows)
        stats2 = seed_extended_sources(
            session=test_session,
            sources_data=sources_data,
            claims_data=claims_data,
            dry_run=False,
        )
        assert stats2["sources_seeded"] == stats1["sources_seeded"]
        assert stats2["entities_seeded"] == stats1["entities_seeded"]
        assert stats2["claims_seeded"] == stats1["claims_seeded"]
        assert stats2["claim_sources_seeded"] == stats1["claim_sources_seeded"]

        # Verify database record counts
        sources_count = test_session.query(HistoricalSource).count()
        entities_count = test_session.query(HistoricalEntity).count()
        claims_count = test_session.query(HistoricalClaim).count()
        bindings_count = test_session.query(HistoricalClaimSource).count()

        assert sources_count == stats1["sources_seeded"]
        assert entities_count == 16
        assert claims_count == stats1["claims_seeded"]
        assert bindings_count == stats1["claim_sources_seeded"]

        # Verify content_scope on all seeded entities
        sample_source = test_session.query(HistoricalSource).first()
        assert sample_source.content_scope == CONTENT_SCOPE_IMPERIAL

        sample_claim = test_session.query(HistoricalClaim).first()
        assert sample_claim.content_scope == CONTENT_SCOPE_IMPERIAL
