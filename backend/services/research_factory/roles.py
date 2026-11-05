# -*- coding: utf-8 -*-
"""Phase subagent role registry for AI Research Factory.

Maps phases P00 to P11 to their exact 10 subagent roles per specifications:
LUU_NIEN_V6_MODULAR_IMPLEMENTATION_SPECS/03_AI_FACTORY/PHASE_P00..P11_TEN_RESEARCH_AGENTS.md
"""
from __future__ import annotations

from typing import Dict, List, NamedTuple


class SubagentRoleSpec(NamedTuple):
    slot: int
    code: str
    role_name: str
    default_provider: str = "gemini"
    estimated_tokens: int = 4000


PHASE_ROLES_REGISTRY: Dict[str, List[SubagentRoleSpec]] = {
    "P00": [
        SubagentRoleSpec(1, "P00-A01", "Inventory auditor", "gemini", 4000),
        SubagentRoleSpec(2, "P00-A02", "Scope owner", "gemini", 4000),
        SubagentRoleSpec(3, "P00-A03", "Question designer", "gemini", 4000),
        SubagentRoleSpec(4, "P00-A04", "Taxonomy specialist", "gemini", 4000),
        SubagentRoleSpec(5, "P00-A05", "Han-Nom risk mapper", "gemini", 4000),
        SubagentRoleSpec(6, "P00-A06", "Geography risk mapper", "gemini", 4000),
        SubagentRoleSpec(7, "P00-A07", "Legal source planner", "gemini", 4000),
        SubagentRoleSpec(8, "P00-A08", "Teaching objectives planner", "gemini", 4000),
        SubagentRoleSpec(9, "P00-A09", "Coverage and cost estimator", "gemini", 4000),
        SubagentRoleSpec(10, "P00-A10", "Run-manifest verifier", "gemini", 4000),
    ],
    "P01": [
        SubagentRoleSpec(1, "P01-A01", "Official heritage registry scout", "gemini", 5000),
        SubagentRoleSpec(2, "P01-A02", "Dynastic chronicles scout", "gemini", 5000),
        SubagentRoleSpec(3, "P01-A03", "Royal document scout", "gemini", 5000),
        SubagentRoleSpec(4, "P01-A04", "Museum catalogue scout", "gemini", 5000),
        SubagentRoleSpec(5, "P01-A05", "Peer-reviewed literature scout", "gemini", 5000),
        SubagentRoleSpec(6, "P01-A06", "Historical maps scout", "gemini", 5000),
        SubagentRoleSpec(7, "P01-A07", "Han-Nom editions scout", "gemini", 5000),
        SubagentRoleSpec(8, "P01-A08", "Image and 3D rights scout", "gemini", 5000),
        SubagentRoleSpec(9, "P01-A09", "Open scholarly metadata scout", "gemini", 5000),
        SubagentRoleSpec(10, "P01-A10", "Contrarian/coverage scout", "gemini", 5000),
    ],
    "P02": [
        SubagentRoleSpec(1, "P02-A01", "Bibliography verifier", "gemini", 4500),
        SubagentRoleSpec(2, "P02-A02", "Canonical URL resolver", "gemini", 4500),
        SubagentRoleSpec(3, "P02-A03", "Authority verifier", "gemini", 4500),
        SubagentRoleSpec(4, "P02-A04", "Duplicate lineage analyzer", "gemini", 4500),
        SubagentRoleSpec(5, "P02-A05", "License analyst", "gemini", 4500),
        SubagentRoleSpec(6, "P02-A06", "Access negotiator", "gemini", 4500),
        SubagentRoleSpec(7, "P02-A07", "Fetch planner", "gemini", 4500),
        SubagentRoleSpec(8, "P02-A08", "Malware/document sanitiser", "gemini", 4500),
        SubagentRoleSpec(9, "P02-A09", "Asset hash controller", "gemini", 4500),
        SubagentRoleSpec(10, "P02-A10", "Acquisition QA auditor", "gemini", 4500),
    ],
    "P03": [
        SubagentRoleSpec(1, "P03-A01", "Document structure parser", "ocr", 6000),
        SubagentRoleSpec(2, "P03-A02", "Printed Vietnamese OCR", "ocr", 6000),
        SubagentRoleSpec(3, "P03-A03", "English and romanized OCR", "ocr", 6000),
        SubagentRoleSpec(4, "P03-A04", "Han glyph detection", "ocr", 6000),
        SubagentRoleSpec(5, "P03-A05", "Han-Nom transcription proposer", "gemini", 6000),
        SubagentRoleSpec(6, "P03-A06", "Edition collation assistant", "gemini", 5000),
        SubagentRoleSpec(7, "P03-A07", "Layout locator mapper", "ocr", 5000),
        SubagentRoleSpec(8, "P03-A08", "Figure and caption extractor", "ocr", 5000),
        SubagentRoleSpec(9, "P03-A09", "OCR quality checker", "gemini", 5000),
        SubagentRoleSpec(10, "P03-A10", "Extraction integrity auditor", "gemini", 5000),
    ],
    "P04": [
        SubagentRoleSpec(1, "P04-A01", "Relief identity evidence finder", "gemini", 5000),
        SubagentRoleSpec(2, "P04-A02", "Chronology finder", "gemini", 5000),
        SubagentRoleSpec(3, "P04-A03", "Geography finder", "gemini", 5000),
        SubagentRoleSpec(4, "P04-A04", "Iconography finder", "gemini", 5000),
        SubagentRoleSpec(5, "P04-A05", "Material and manufacture finder", "gemini", 5000),
        SubagentRoleSpec(6, "P04-A06", "Han-Nom passage binder", "gemini", 5000),
        SubagentRoleSpec(7, "P04-A07", "Citation and quote validator", "gemini", 5000),
        SubagentRoleSpec(8, "P04-A08", "Atomic claim decomposer", "gemini", 5000),
        SubagentRoleSpec(9, "P04-A09", "Negative evidence analyst", "gemini", 5000),
        SubagentRoleSpec(10, "P04-A10", "Evidence binder auditor", "gemini", 5000),
    ],
    "P05": [
        SubagentRoleSpec(1, "P05-A01", "Primary source triangulator", "gemini", 6000),
        SubagentRoleSpec(2, "P05-A02", "Secondary scholarship triangulator", "gemini", 6000),
        SubagentRoleSpec(3, "P05-A03", "Chronology consistency solver", "gemini", 5000),
        SubagentRoleSpec(4, "P05-A04", "Entity and alias linker", "gemini", 5000),
        SubagentRoleSpec(5, "P05-A05", "Geography temporal mapper", "gemini", 5000),
        SubagentRoleSpec(6, "P05-A06", "Translation meaning checker", "gemini", 5000),
        SubagentRoleSpec(7, "P05-A07", "Independence/derivation graph analyst", "gemini", 5000),
        SubagentRoleSpec(8, "P05-A08", "Counterclaim searcher", "gemini", 5000),
        SubagentRoleSpec(9, "P05-A09", "Evidence strength assessor", "gemini", 5000),
        SubagentRoleSpec(10, "P05-A10", "Contradiction board auditor", "gemini", 5000),
    ],
    "P06": [
        SubagentRoleSpec(1, "P06-A01", "Object and inventory synthesizer", "gemini", 6000),
        SubagentRoleSpec(2, "P06-A02", "Context historian", "gemini", 6000),
        SubagentRoleSpec(3, "P06-A03", "Chronology narrative planner", "gemini", 6000),
        SubagentRoleSpec(4, "P06-A04", "Iconographic interpreter", "gemini", 6000),
        SubagentRoleSpec(5, "P06-A05", "Heritage geography interpreter", "gemini", 6000),
        SubagentRoleSpec(6, "P06-A06", "Material and technique synthesizer", "gemini", 6000),
        SubagentRoleSpec(7, "P06-A07", "Source conflict summarizer", "gemini", 6000),
        SubagentRoleSpec(8, "P06-A08", "Bibliography and citations compiler", "gemini", 6000),
        SubagentRoleSpec(9, "P06-A09", "Pedagogical claim selector", "gemini", 6000),
        SubagentRoleSpec(10, "P06-A10", "Dossier completeness auditor", "gemini", 6000),
    ],
    "P07": [
        SubagentRoleSpec(1, "P07-A01", "Vietnamese long-form historian writer", "gemini", 8000),
        SubagentRoleSpec(2, "P07-A02", "English historical writer", "gemini", 8000),
        SubagentRoleSpec(3, "P07-A03", "Short museum label writer", "gemini", 5000),
        SubagentRoleSpec(4, "P07-A04", "Han-Nom editorial note writer", "gemini", 5000),
        SubagentRoleSpec(5, "P07-A05", "3D/AR narration writer", "gemini", 6000),
        SubagentRoleSpec(6, "P07-A06", "Timeline/map article writer", "gemini", 6000),
        SubagentRoleSpec(7, "P07-A07", "Source-based ELLO lesson author", "gemini", 7000),
        SubagentRoleSpec(8, "P07-A08", "Assessment/rubric author", "gemini", 6000),
        SubagentRoleSpec(9, "P07-A09", "Accessibility and reading-level writer", "gemini", 5000),
        SubagentRoleSpec(10, "P07-A10", "Citation editor and content assembler", "gemini", 8000),
    ],
    "P08": [
        SubagentRoleSpec(1, "P08-A01", "Sentence-to-claim verifier", "gemini", 6000),
        SubagentRoleSpec(2, "P08-A02", "Exact-citation and locator checker", "gemini", 6000),
        SubagentRoleSpec(3, "P08-A03", "Historical accuracy red-teamer", "gemini", 6000),
        SubagentRoleSpec(4, "P08-A04", "Han-Nom and translation red-teamer", "gemini", 6000),
        SubagentRoleSpec(5, "P08-A05", "Contradiction/dispute red-teamer", "gemini", 6000),
        SubagentRoleSpec(6, "P08-A06", "Copyright and rights red-teamer", "gemini", 6000),
        SubagentRoleSpec(7, "P08-A07", "Prompt injection security red-teamer", "gemini", 6000),
        SubagentRoleSpec(8, "P08-A08", "Pedagogical validity reviewer", "gemini", 6000),
        SubagentRoleSpec(9, "P08-A09", "Accessibility multilingual reviewer", "gemini", 5000),
        SubagentRoleSpec(10, "P08-A10", "Independent gate aggregator", "gemini", 6000),
    ],
    "P09": [
        SubagentRoleSpec(1, "P09-A01", "Historical expert packet preparer", "gemini", 5000),
        SubagentRoleSpec(2, "P09-A02", "Han-Nom expert packet preparer", "gemini", 5000),
        SubagentRoleSpec(3, "P09-A03", "Museum/heritage curator packet preparer", "gemini", 5000),
        SubagentRoleSpec(4, "P09-A04", "Translation reviewer packet preparer", "gemini", 5000),
        SubagentRoleSpec(5, "P09-A05", "Legal/permissions packet preparer", "gemini", 5000),
        SubagentRoleSpec(6, "P09-A06", "Teacher reviewer packet preparer", "gemini", 5000),
        SubagentRoleSpec(7, "P09-A07", "Accessibility reviewer packet preparer", "gemini", 5000),
        SubagentRoleSpec(8, "P09-A08", "Research integrity packet preparer", "gemini", 5000),
        SubagentRoleSpec(9, "P09-A09", "Editorial conflicts coordinator", "gemini", 5000),
        SubagentRoleSpec(10, "P09-A10", "Human-signoff verifier", "gemini", 5000),
    ],
    "P10": [
        SubagentRoleSpec(1, "P10-A01", "Content release manifest builder", "gemini", 6000),
        SubagentRoleSpec(2, "P10-A02", "Relief encyclopedia exporter", "gemini", 6000),
        SubagentRoleSpec(3, "P10-A03", "Historical graph synchronizer", "gemini", 5000),
        SubagentRoleSpec(4, "P10-A04", "LMS/ELLO packager", "gemini", 5000),
        SubagentRoleSpec(5, "P10-A05", "Media/hotspot integrator", "gemini", 5000),
        SubagentRoleSpec(6, "P10-A06", "Search/embedding index builder", "gemini", 5000),
        SubagentRoleSpec(7, "P10-A07", "History Tutor retrieval updater", "gemini", 5000),
        SubagentRoleSpec(8, "P10-A08", "Accessibility build verifier", "gemini", 5000),
        SubagentRoleSpec(9, "P10-A09", "Export/API compatibility checker", "gemini", 5000),
        SubagentRoleSpec(10, "P10-A10", "Atomic publish coordinator", "gemini", 6000),
    ],
    "P11": [
        SubagentRoleSpec(1, "P11-A01", "Source link availability watcher", "gemini", 4000),
        SubagentRoleSpec(2, "P11-A02", "Rights expiration watcher", "gemini", 4000),
        SubagentRoleSpec(3, "P11-A03", "New scholarship watcher", "gemini", 4000),
        SubagentRoleSpec(4, "P11-A04", "Official catalog corrections watcher", "gemini", 4000),
        SubagentRoleSpec(5, "P11-A05", "Source edition monitor", "gemini", 4000),
        SubagentRoleSpec(6, "P11-A06", "AI quality drift evaluator", "gemini", 4000),
        SubagentRoleSpec(7, "P11-A07", "User correction triager", "gemini", 4000),
        SubagentRoleSpec(8, "P11-A08", "Analytics and coverage auditor", "gemini", 4000),
        SubagentRoleSpec(9, "P11-A09", "Paper evidence export assistant", "gemini", 4000),
        SubagentRoleSpec(10, "P11-A10", "Reprocessing scheduler & rollback auditor", "gemini", 4000),
    ],
}


def get_roles_for_phase(phase_code: str) -> List[SubagentRoleSpec]:
    """Retrieves the strictly ordered 10-role specification for a given phase."""
    phase = phase_code.upper()
    if phase not in PHASE_ROLES_REGISTRY:
        raise ValueError(f"Unknown phase code: {phase_code}. Valid phases: {list(PHASE_ROLES_REGISTRY.keys())}")
    roles = PHASE_ROLES_REGISTRY[phase]
    if len(roles) != 10:
        raise ValueError(f"Phase {phase} has {len(roles)} roles; must have exactly 10 roles.")
    return roles
