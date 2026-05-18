"""
Embedding Service for Luuniensuki LMS.

This module provides utilities for generating and managing embeddings for RAG documents.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest, urlopen
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import EmbeddingJob, RagDocument, RagSettings

logger = logging.getLogger(__name__)


def _embedding_url() -> str:
    """Get the embedding API URL."""
    return settings.embedding_base_url


def _get_rag_settings(session: Session) -> RagSettings:
    """Get or create RAG settings."""
    rag_settings = session.execute(select(RagSettings)).scalar_one_or_none()
    if not rag_settings:
        rag_settings = RagSettings()
        session.add(rag_settings)
        session.commit()
        session.refresh(rag_settings)
    return rag_settings


def call_embedding(text: str) -> Optional[list[float]]:
    """
    Generate embedding for a given text using the configured embedding API.
    
    Args:
        text: The text to generate embedding for
        
    Returns:
        List of floats representing the embedding vector, or None if failed
    """
    if not settings.embedding_api_key or not text:
        return None

    payload = {"model": settings.embedding_model, "input": text}
    data = json.dumps(payload).encode("utf-8")
    request = UrlRequest(
        _embedding_url(),
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.embedding_api_key}",
        },
    )

    try:
        with urlopen(request, timeout=settings.embedding_timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        logger.warning("Embedding request failed: %s", exc)
        return None
    except URLError as exc:
        logger.warning("Embedding request failed: %s", exc)
        return None

    if not body:
        return None

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        logger.warning("Failed to decode embedding response")
        return None

    data_list = payload.get("data") or []
    if not data_list:
        return None
    embedding = data_list[0].get("embedding")
    if not isinstance(embedding, list):
        return None

    result: list[float] = []
    for value in embedding:
        try:
            result.append(float(value))
        except (TypeError, ValueError):
            continue
    return result or None


def update_document_embedding(
    session: Session, 
    doc: RagDocument, 
    force: bool = False
) -> bool:
    """
    Update embedding for a single document.
    
    Args:
        session: Database session
        doc: The RAG document to update
        force: If True, update even if embedding exists
        
    Returns:
        True if embedding was updated, False otherwise
    """
    rag_settings = _get_rag_settings(session)
    if not rag_settings.embedding_enabled:
        return False
    if not settings.embedding_api_key:
        return False
    
    # Skip if already has embedding and force is False
    if not force and doc.embedding and doc.embedding_model == settings.embedding_model:
        return False
    
    embedding = call_embedding(doc.content or doc.title)
    if not embedding:
        return False
    
    doc.embedding = embedding
    doc.embedding_model = settings.embedding_model
    doc.embedding_updated_at = datetime.now(timezone.utc)
    return True


def rebuild_all_embeddings(
    session: Session,
    job: EmbeddingJob,
    force: bool = False
) -> dict:
    """
    Rebuild embeddings for all active RAG documents.
    
    Args:
        session: Database session
        job: The embedding job tracking this rebuild
        force: If True, rebuild all embeddings even if they exist
        
    Returns:
        Dictionary with total, updated, and skipped counts
    """
    # Update job status
    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    session.commit()
    
    try:
        # Get all active documents
        docs = (
            session.execute(
                select(RagDocument)
                .where(RagDocument.is_active == True)
                .order_by(RagDocument.updated_at.desc())
            )
            .scalars()
            .all()
        )
        
        job.total_documents = len(docs)
        session.commit()
        
        updated = 0
        skipped = 0
        
        for doc in docs:
            try:
                if update_document_embedding(session, doc, force=force):
                    updated += 1
                else:
                    skipped += 1
                
                job.processed_documents += 1
                session.commit()
                
            except Exception as e:
                skipped += 1
                logger.warning(
                    "Failed to rebuild embedding for RAG document %s: %s",
                    doc.id,
                    str(e),
                    exc_info=True,
                )
        
        # Mark job as completed
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        session.commit()
        
        return {
            "total": job.total_documents,
            "updated": updated,
            "skipped": skipped,
        }
        
    except Exception as e:
        # Mark job as failed
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.now(timezone.utc)
        session.commit()
        
        logger.error("Failed to rebuild embeddings: %s", str(e), exc_info=True)
        raise


def get_job_by_id(session: Session, job_id: UUID) -> Optional[EmbeddingJob]:
    """
    Get an embedding job by ID.
    
    Args:
        session: Database session
        job_id: The job UUID
        
    Returns:
        The embedding job or None if not found
    """
    return session.execute(
        select(EmbeddingJob).where(EmbeddingJob.id == job_id)
    ).scalar_one_or_none()


def get_latest_job(session: Session) -> Optional[EmbeddingJob]:
    """
    Get the most recent embedding job.
    
    Args:
        session: Database session
        
    Returns:
        The latest embedding job or None if no jobs exist
    """
    return session.execute(
        select(EmbeddingJob).order_by(EmbeddingJob.created_at.desc())
    ).scalars().first()

