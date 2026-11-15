"""P10 provenance & rights tests (P10-T02/T04): hashes, citations, honesty."""
from __future__ import annotations

import pytest

from research_v3.methods.p10.corpus import load_corpus
from research_v3.methods.p10.provenance import collect_source_records, provenance_manifest
from research_v3.methods.p10.registry import build_anchor_registry


class TestProvenance:
    def test_every_corpus_file_is_hashed(self):
        records = collect_source_records()
        motif_records = [r for r in records if r.source_id.startswith("motifs:")]
        assert len(motif_records) == 9
        for rec in motif_records:
            assert len(rec.sha256) == 64
            assert rec.bytes > 0

    def test_curriculum_catalog_is_hashed_and_cited(self):
        records = collect_source_records()
        cat = [r for r in records if r.source_id == "curriculum:gdpt2018_hue_catalog"]
        assert len(cat) == 1
        assert "32/2018" in cat[0].rights_note or "GDPT" in cat[0].rights_note

    def test_manifest_is_deterministic_and_self_hashed(self):
        m1 = provenance_manifest()
        m2 = provenance_manifest()
        assert m1["manifest_sha256"] == m2["manifest_sha256"]
        assert len(m1["manifest_sha256"]) == 64

    def test_no_redistribution_rights_claimed(self):
        m = provenance_manifest()
        assert "no corpus bytes are copied" in m["rights_positions"]["redistribution"]

    def test_dataset_registry_keeps_hue_corpus_blocked(self):
        """The repo's V3 dataset registry must keep hue-heritage-corpus BLOCKED —
        P10 must not inherit rights it does not have."""
        from research_v3.datasets.registry import load_registry

        cards = load_registry()
        hue = [c for c in cards if c.dataset_id == "hue-heritage-corpus"]
        assert hue, "hue-heritage-corpus card missing from registry"
        assert hue[0].status == "BLOCKED"

    def test_corpus_objects_flag_ai_generated(self, corpus):
        """All 162 descriptions are AI-generated repo content — the design must
        carry that flag rather than launder provenance."""
        assert len(corpus) == 162
        assert all(o.is_ai_generated for o in corpus)


class TestAnchorCitations:
    def test_every_anchor_has_nonempty_citation(self):
        for anchor in build_anchor_registry().values():
            assert anchor.source_citation.strip()
            assert anchor.competency_ref.strip()

    def test_ministerial_citation_names_tt32(self):
        from research_v3.methods.p10.registry import CITATION_TT32

        assert "32/2018/TT-BGDĐT" in CITATION_TT32

    def test_needs_review_anchors_cover_all_categories_x_grades(self):
        registry = build_anchor_registry()
        pending = [a for a in registry.values() if a.confidence_status == "needs_expert_review"]
        assert len(pending) == 27  # 9 categories x 3 grades
        for anchor in pending:
            assert anchor.anchor_code.startswith("P10-LOCAL-")
            assert "cần giáo viên" in anchor.source_citation or "chưa thẩm định" in anchor.source_citation
