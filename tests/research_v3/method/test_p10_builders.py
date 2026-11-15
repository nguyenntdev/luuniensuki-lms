"""P10 builder tests: determinism, C0/C1/proposed behavior on the real corpus."""
from __future__ import annotations

from research_v3.methods.p10.corpus import build_prerequisite_edges
from research_v3.methods.p10.experiment import run_matrix
from research_v3.methods.p10.registry import build_anchor_registry
from research_v3.methods.p10.spiral_builder import (
    build_linear_playlist,
    build_spiral_dag,
    build_topological_no_bloom,
)


class TestDeterminism:
    def test_proposed_sequence_is_byte_identical_across_runs(self, corpus, anchor_registry):
        edges = build_prerequisite_edges(corpus)
        s1 = build_spiral_dag(corpus, edges, anchor_registry)
        s2 = build_spiral_dag(corpus, edges, anchor_registry)
        assert s1.ordered_object_ids == s2.ordered_object_ids
        assert s1.sha256() == s2.sha256()

    def test_c0_and_c1_deterministic(self, corpus, anchor_registry):
        edges = build_prerequisite_edges(corpus)
        for build in (build_linear_playlist, build_topological_no_bloom):
            if build is build_linear_playlist:
                a = build(corpus, anchor_registry)
                b = build(corpus, anchor_registry)
            else:
                a = build(corpus, edges, anchor_registry)
                b = build(corpus, edges, anchor_registry)
            assert a.ordered_object_ids == b.ordered_object_ids
            assert a.sha256() == b.sha256()

    def test_full_matrix_payload_hash_stable(self):
        p1 = run_matrix(seed=42)
        p2 = run_matrix(seed=42)
        assert p1["payload_sha256"] == p2["payload_sha256"]

    def test_a4_random_order_seeded_is_reproducible(self, corpus, anchor_registry):
        from research_v3.methods.p10.ablations import run_a4_random_order

        s1, _ = run_a4_random_order(corpus, anchor_registry, seed=42)
        s2, _ = run_a4_random_order(corpus, anchor_registry, seed=42)
        assert s1.ordered_object_ids == s2.ordered_object_ids
        # different seed -> (overwhelmingly) different permutation
        s3, _ = run_a4_random_order(corpus, anchor_registry, seed=7)
        assert s3.ordered_object_ids != s1.ordered_object_ids


class TestCorpusScale:
    def test_corpus_is_the_documented_162(self, corpus):
        assert len(corpus) == 162
        assert len({o.object_id for o in corpus}) == 162
        assert len({o.urn_slug for o in corpus}) == 9

    def test_spiral_layers_are_nonempty_and_depth_rises(self, corpus):
        by_layer = {1: 0, 2: 0, 3: 0}
        for obj in corpus:
            by_layer[obj.layer] += 1
        # Every layer non-empty; layer-1 identification work dominates by design
        # (the spiral revisits fewer, deeper objects at higher grades).
        assert all(v > 0 for v in by_layer.values())
        assert by_layer[1] > by_layer[2] > 0
        assert by_layer[3] > 0

    def test_proposed_order_has_no_grade_or_bloom_descent(self, corpus, anchor_registry):
        edges = build_prerequisite_edges(corpus)
        seq = build_spiral_dag(corpus, edges, anchor_registry)
        idx = {o.object_id: o for o in corpus}
        grades = [idx[oid].grade for oid in seq.ordered_object_ids]
        blooms = [idx[oid].bloom_level for oid in seq.ordered_object_ids]
        assert all(a <= b for a, b in zip(grades, grades[1:]))
        assert all(a <= b for a, b in zip(blooms, blooms[1:]))

    def test_prerequisite_edges_cover_all_layers(self, corpus):
        edges = build_prerequisite_edges(corpus)
        kinds = {e.edge_kind for e in edges}
        assert kinds == {"progression", "bridge"}
        assert len(edges) > 0
