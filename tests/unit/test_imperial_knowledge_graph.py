"""
Tests for Subagent 12: Knowledge Graph Design and Relational Ontologies
for the Imperial City of Huế.
"""
import json
from pathlib import Path
import pytest

from backend.domain.imperial_knowledge_graph import (
    DEFAULT_KG_PATH,
    ImperialKnowledgeGraph,
)


@pytest.fixture
def kg_dataset():
    assert DEFAULT_KG_PATH.exists(), f"KG file missing at {DEFAULT_KG_PATH}"
    with open(DEFAULT_KG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def graph(kg_dataset):
    return ImperialKnowledgeGraph(kg_dataset)


def test_schema_metadata(kg_dataset):
    assert kg_dataset["schema_version"] == "2.0.0"
    assert kg_dataset["content_scope"] == "IMPERIAL_CITY_HUE_KG"
    assert "ontology" in kg_dataset
    assert "predicates" in kg_dataset["ontology"]
    assert len(kg_dataset["ontology"]["predicates"]) == 9


def test_required_predicates_present(kg_dataset):
    required_predicates = {
        "contains",
        "leads_to",
        "oriented_to",
        "ceremonial_axis",
        "ancestral_veneration",
        "architectural_twin",
        "reconstructed_with",
        "associated_craft",
        "source_grounded_by",
    }
    declared = {p["predicate"] for p in kg_dataset["ontology"]["predicates"]}
    assert required_predicates == declared


def test_all_zones_present(graph):
    expected_zones = {
        "zone-central-ceremonial-axis",
        "zone-ancestral-worship-space",
        "zone-purple-forbidden-city",
        "zone-royal-living-gardens",
    }
    actual_zones = {n.id for n in graph.get_nodes_by_type("zone")}
    assert expected_zones.issubset(actual_zones)
    assert len(actual_zones) == 4


def test_monuments_count_and_scope(graph):
    monuments = graph.get_nodes_by_type("monument")
    assert len(monuments) >= 16

    expected_monuments = {
        "site-ngo-mon",
        "site-cau-trung-dao",
        "site-san-dai-trieu-nghi",
        "site-dien-thai-hoa",
        "site-dai-cung-mon",
        "site-dien-can-chanh",
        "site-dien-kien-trung",
        "site-duyet-thi-duong",
        "site-thai-binh-lau",
        "site-the-to-mieu",
        "site-hien-lam-cac",
        "site-hung-to-mieu",
        "site-trieu-to-mieu",
        "site-dien-phung-tien",
        "site-cung-dien-tho",
        "site-cung-truong-sanh",
    }
    actual_monument_ids = {m.id for m in monuments}
    assert expected_monuments.issubset(actual_monument_ids)


def test_historical_eras(graph):
    eras = graph.get_nodes_by_type("historical_era")
    expected_eras = {
        "era-gia-long",
        "era-minh-mang",
        "era-thieu-tri",
        "era-tu-duc",
        "era-dong-khanh",
        "era-khai-dinh",
        "era-bao-dai",
    }
    actual_eras = {e.id for e in eras}
    assert expected_eras.issubset(actual_eras)


def test_architectural_artifacts(graph):
    artifacts = graph.get_nodes_by_type("artifact")
    expected_artifacts = {
        "art-cuu-dinh",
        "art-ngai-vang",
        "art-cuu-vi-than-cong",
        "art-kim-bao-truyen-quoc",
    }
    actual_artifacts = {a.id for a in artifacts}
    assert expected_artifacts.issubset(actual_artifacts)


def test_primary_sources(graph):
    sources = graph.get_nodes_by_type("source")
    expected_sources = {
        "src-dai-nam-thuc-luc",
        "src-kham-dinh-hoi-dien",
        "src-dai-nam-nhat-thong-chi",
    }
    actual_sources = {s.id for s in sources}
    assert expected_sources.issubset(actual_sources)


def test_craft_guilds(graph):
    guilds = graph.get_nodes_by_type("craft_guild")
    expected_guilds = {
        "guild-duc-dong-phuong-duc",
        "guild-phap-lam-hue",
        "guild-moc-my-nghe-kim-bong",
        "guild-kham-sanh-su-hue",
        "guild-ngoc-hoang-cung-kim-hoan",
    }
    actual_guilds = {g.id for g in guilds}
    assert expected_guilds.issubset(actual_guilds)


def test_graph_integrity_and_no_dangling_edges(graph):
    is_valid, errors = graph.validate_integrity()
    assert is_valid, f"Integrity errors found: {errors}"


def test_ceremonial_axis_trace(graph):
    axis = graph.trace_axis_path("site-ngo-mon")
    slugs = [n.slug for n in axis]
    assert len(slugs) >= 4
    assert slugs[0] == "ngo-mon"
    assert "cau-trung-dao" in slugs
    assert "san-dai-trieu-nghi" in slugs
    assert "dien-thai-hoa" in slugs


def test_source_grounding_helpers(graph):
    grounded_sources = graph.get_grounding_sources_for_node("site-dien-thai-hoa")
    assert len(grounded_sources) >= 1
    source_ids = {s["source_id"] for s in grounded_sources}
    assert "src-dai-nam-thuc-luc" in source_ids


def test_craft_association_helpers(graph):
    thai_hoa_crafts = graph.get_associated_crafts_for_monument("site-dien-thai-hoa")
    assert len(thai_hoa_crafts) >= 2
    guild_ids = {c["guild_id"] for c in thai_hoa_crafts}
    assert "guild-phap-lam-hue" in guild_ids
    assert "guild-moc-my-nghe-kim-bong" in guild_ids


def test_subgraph_k_hop(graph):
    sub = graph.subgraph_k_hop("art-cuu-dinh", k=1)
    assert sub["root_id"] == "art-cuu-dinh"
    node_ids = {n["id"] for n in sub["nodes"]}
    assert "site-the-to-mieu" in node_ids
    assert "guild-duc-dong-phuong-duc" in node_ids
