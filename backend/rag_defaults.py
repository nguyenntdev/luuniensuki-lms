"""
RAG Settings Default Values and Constants.

This module defines default values for RAG (Retrieval Augmented Generation) settings.
These defaults are used when creating new settings or resetting to defaults.
"""

from typing import Final

# =============================================================================
# RAG Settings Default Values
# =============================================================================

RAG_DEFAULT_SYSTEM_INSTRUCTION: Final[str] = """You are a helpful assistant for the Lưu Niên Sử Kí (Cửu Đỉnh Chronicles) learning platform.

Your role is to help learners understand Vietnamese history and culture through the lens of the nine dynastic urns (Cửu Đỉnh).

Guidelines:
- Provide clear, accurate information based on the provided context
- Use simple, accessible language appropriate for learners
- Connect historical concepts to the specific motifs and urns being studied
- Encourage curiosity and deeper exploration
- When uncertain, acknowledge limitations rather than speculating
- Relate information back to the learning objectives when relevant"""

RAG_DEFAULT_PROMPT_PREFIX: Final[str] = """Based on the following context from the Cửu Đỉnh learning materials:

{context}

Please answer the following question:"""

RAG_DEFAULT_MODEL_OVERRIDE: Final[str | None] = None
RAG_DEFAULT_TEMPERATURE: Final[float] = 0.7
RAG_DEFAULT_MAX_DOCUMENTS: Final[int] = 6
RAG_DEFAULT_EMBEDDING_ENABLED: Final[bool] = True
RAG_DEFAULT_HYBRID_ALPHA: Final[float] = 0.6

# =============================================================================
# Validation Constants
# =============================================================================

RAG_SYSTEM_INSTRUCTION_MAX_LENGTH: Final[int] = 5000
RAG_PROMPT_PREFIX_MAX_LENGTH: Final[int] = 2000
RAG_MODEL_OVERRIDE_MAX_LENGTH: Final[int] = 100
RAG_TEMPERATURE_MIN: Final[float] = 0.0
RAG_TEMPERATURE_MAX: Final[float] = 2.0
RAG_MAX_DOCUMENTS_MIN: Final[int] = 1
RAG_MAX_DOCUMENTS_MAX: Final[int] = 20
RAG_HYBRID_ALPHA_MIN: Final[float] = 0.0
RAG_HYBRID_ALPHA_MAX: Final[float] = 1.0


def get_rag_defaults() -> dict:
    """
    Get a dictionary of default RAG settings.
    
    Returns:
        Dictionary with all default RAG setting values.
    """
    return {
        "system_instruction": RAG_DEFAULT_SYSTEM_INSTRUCTION,
        "prompt_prefix": RAG_DEFAULT_PROMPT_PREFIX,
        "model_override": RAG_DEFAULT_MODEL_OVERRIDE,
        "temperature": RAG_DEFAULT_TEMPERATURE,
        "max_documents": RAG_DEFAULT_MAX_DOCUMENTS,
        "embedding_enabled": RAG_DEFAULT_EMBEDDING_ENABLED,
        "hybrid_alpha": RAG_DEFAULT_HYBRID_ALPHA,
    }

