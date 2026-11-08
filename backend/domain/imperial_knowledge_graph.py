"""Imperial City of Huế Relational Knowledge Graph Helper Utilities.

Provides high-performance querying, topological validation, and traversal helpers
for the unified knowledge graph of Hoàng Thành & Tử Cấm Thành (Hue, Vietnam).
"""
from __future__ import annotations

import json
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


DEFAULT_KG_PATH = Path(__file__).parent.parent.parent / "data" / "imperial" / "imperial_city_knowledge_graph.json"


@dataclass(frozen=True)
class KnowledgeNode:
    id: str
    slug: str
    entity_type: str
    name_vi: str
    name_en: str
    name_han_nom: Optional[str]
    short_description_vi: str
    short_description_en: str
    attributes: Dict[str, Any]


@dataclass(frozen=True)
class KnowledgeEdge:
    id: str
    source: str
    target: str
    predicate: str
    predicate_category: str
    epistemic_certainty: str
    source_grounding: Optional[Dict[str, str]]
    description_vi: str
    description_en: str


class ImperialKnowledgeGraph:
    """In-memory indexing and querying engine for the Huế Imperial Knowledge Graph."""

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._nodes_by_slug: Dict[str, KnowledgeNode] = {}
        self._edges: Dict[str, KnowledgeEdge] = {}
        self._out_edges: Dict[str, List[KnowledgeEdge]] = defaultdict(list)
        self._in_edges: Dict[str, List[KnowledgeEdge]] = defaultdict(list)
        self._metadata: Dict[str, Any] = {}
        self._predicates: Dict[str, Any] = {}

        if data:
            self._load_from_dict(data)

    @classmethod
    def load_from_file(cls, path: Optional[Path] = None) -> "ImperialKnowledgeGraph":
        file_path = path or DEFAULT_KG_PATH
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data)

    def _load_from_dict(self, data: Dict[str, Any]) -> None:
        self._metadata = {
            "schema_version": data.get("schema_version"),
            "authority": data.get("authority"),
            "content_scope": data.get("content_scope"),
            "title": data.get("title"),
        }
        for pred in data.get("ontology", {}).get("predicates", []):
            self._predicates[pred["predicate"]] = pred

        for node_dict in data.get("nodes", []):
            node = KnowledgeNode(
                id=node_dict["id"],
                slug=node_dict["slug"],
                entity_type=node_dict["entity_type"],
                name_vi=node_dict["name_vi"],
                name_en=node_dict["name_en"],
                name_han_nom=node_dict.get("name_han_nom"),
                short_description_vi=node_dict.get("short_description_vi", ""),
                short_description_en=node_dict.get("short_description_en", ""),
                attributes=node_dict.get("attributes", {}),
            )
            self._nodes[node.id] = node
            self._nodes_by_slug[node.slug] = node

        for edge_dict in data.get("edges", []):
            edge = KnowledgeEdge(
                id=edge_dict["id"],
                source=edge_dict["source"],
                target=edge_dict["target"],
                predicate=edge_dict["predicate"],
                predicate_category=edge_dict.get("predicate_category", ""),
                epistemic_certainty=edge_dict.get("epistemic_certainty", "high"),
                source_grounding=edge_dict.get("source_grounding"),
                description_vi=edge_dict.get("description_vi", ""),
                description_en=edge_dict.get("description_en", ""),
            )
            self._edges[edge.id] = edge
            self._out_edges[edge.source].append(edge)
            self._in_edges[edge.target].append(edge)

    @property
    def total_nodes(self) -> int:
        return len(self._nodes)

    @property
    def total_edges(self) -> int:
        return len(self._edges)

    def get_node(self, node_id_or_slug: str) -> Optional[KnowledgeNode]:
        return self._nodes.get(node_id_or_slug) or self._nodes_by_slug.get(node_id_or_slug)

    def get_nodes_by_type(self, entity_type: str) -> List[KnowledgeNode]:
        return [node for node in self._nodes.values() if node.entity_type == entity_type]

    def get_outgoing_edges(self, node_id_or_slug: str, predicate: Optional[str] = None) -> List[KnowledgeEdge]:
        node = self.get_node(node_id_or_slug)
        if not node:
            return []
        edges = self._out_edges.get(node.id, [])
        if predicate:
            edges = [e for e in edges if e.predicate == predicate]
        return edges

    def get_incoming_edges(self, node_id_or_slug: str, predicate: Optional[str] = None) -> List[KnowledgeEdge]:
        node = self.get_node(node_id_or_slug)
        if not node:
            return []
        edges = self._in_edges.get(node.id, [])
        if predicate:
            edges = [e for e in edges if e.predicate == predicate]
        return edges

    def get_neighbors(
        self,
        node_id_or_slug: str,
        predicate: Optional[str] = None,
        direction: str = "both",
    ) -> List[Tuple[KnowledgeNode, KnowledgeEdge]]:
        """Returns adjacent nodes and connecting edges."""
        node = self.get_node(node_id_or_slug)
        if not node:
            return []
        results: List[Tuple[KnowledgeNode, KnowledgeEdge]] = []

        if direction in ("out", "both"):
            for e in self.get_outgoing_edges(node.id, predicate):
                target_node = self._nodes.get(e.target)
                if target_node:
                    results.append((target_node, e))

        if direction in ("in", "both"):
            for e in self.get_incoming_edges(node.id, predicate):
                source_node = self._nodes.get(e.source)
                if source_node:
                    results.append((source_node, e))

        return results

    def trace_axis_path(self, start_slug: str = "site-ngo-mon") -> List[KnowledgeNode]:
        """Traces the ceremonial or linear sequence from start_slug using 'leads_to' or 'ceremonial_axis'."""
        start = self.get_node(start_slug)
        if not start:
            return []

        path = [start]
        curr = start
        visited = {curr.id}

        while True:
            forward_edges = [
                e for e in self.get_outgoing_edges(curr.id)
                if e.predicate in ("leads_to", "ceremonial_axis") and e.target not in visited
            ]
            if not forward_edges:
                break
            next_edge = forward_edges[0]
            curr = self._nodes[next_edge.target]
            visited.add(curr.id)
            path.append(curr)

        return path

    def get_grounding_sources_for_node(self, node_id_or_slug: str) -> List[Dict[str, Any]]:
        """Finds all primary historical sources grounding this node directly or via attached edges."""
        node = self.get_node(node_id_or_slug)
        if not node:
            return []

        sources: List[Dict[str, Any]] = []
        # Direct edge: source_grounded_by
        for e in self.get_outgoing_edges(node.id, "source_grounded_by"):
            src_node = self._nodes.get(e.target)
            if src_node:
                sources.append({
                    "source_id": src_node.id,
                    "title": src_node.name_vi,
                    "title_han_nom": src_node.name_han_nom,
                    "source_grounding": e.source_grounding,
                    "edge_description": e.description_vi,
                })
        return sources

    def get_associated_crafts_for_monument(self, monument_slug: str) -> List[Dict[str, Any]]:
        """Finds craft guilds linked via associated_craft or reconstructed_with."""
        node = self.get_node(monument_slug)
        if not node:
            return []
        crafts = []
        for e in self.get_outgoing_edges(node.id):
            if e.predicate in ("associated_craft", "reconstructed_with"):
                target_node = self._nodes.get(e.target)
                if target_node:
                    crafts.append({
                        "guild_id": target_node.id,
                        "guild_name_vi": target_node.name_vi,
                        "guild_name_en": target_node.name_en,
                        "predicate": e.predicate,
                        "craft_details": target_node.attributes,
                        "description": e.description_vi,
                    })
        return crafts

    def subgraph_k_hop(self, root_id_or_slug: str, k: int = 1) -> Dict[str, Any]:
        """Extracts a k-hop subgraph centered at the root node."""
        root = self.get_node(root_id_or_slug)
        if not root:
            return {"nodes": [], "edges": []}

        visited_nodes: Set[str] = {root.id}
        collected_edges: Dict[str, KnowledgeEdge] = {}
        queue: deque[Tuple[str, int]] = deque([(root.id, 0)])

        while queue:
            curr_id, depth = queue.popleft()
            if depth >= k:
                continue

            for edge in self._out_edges.get(curr_id, []):
                collected_edges[edge.id] = edge
                if edge.target not in visited_nodes:
                    visited_nodes.add(edge.target)
                    queue.append((edge.target, depth + 1))

            for edge in self._in_edges.get(curr_id, []):
                collected_edges[edge.id] = edge
                if edge.source not in visited_nodes:
                    visited_nodes.add(edge.source)
                    queue.append((edge.source, depth + 1))

        nodes = [self._nodes[nid] for nid in visited_nodes if nid in self._nodes]
        return {
            "root_id": root.id,
            "nodes": [
                {
                    "id": n.id,
                    "slug": n.slug,
                    "entity_type": n.entity_type,
                    "name_vi": n.name_vi,
                    "name_en": n.name_en,
                    "name_han_nom": n.name_han_nom,
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "predicate": e.predicate,
                    "epistemic_certainty": e.epistemic_certainty,
                    "description_vi": e.description_vi,
                }
                for e in collected_edges.values()
            ],
        }

    def validate_integrity(self) -> Tuple[bool, List[str]]:
        """Validates topological integrity of the graph (no dangling edges, valid predicates)."""
        errors = []
        for edge_id, edge in self._edges.items():
            if edge.source not in self._nodes:
                errors.append(f"Edge {edge_id}: source {edge.source} not in nodes")
            if edge.target not in self._nodes:
                errors.append(f"Edge {edge_id}: target {edge.target} not in nodes")
            if edge.predicate not in self._predicates:
                errors.append(f"Edge {edge_id}: predicate '{edge.predicate}' not in ontology")

        return (len(errors) == 0, errors)
