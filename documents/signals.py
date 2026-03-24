"""
Auto-indexing signals for RAG system.
Automatically indexes PDF documents into the vector store when they are saved.
"""

import os
import threading
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='documents.Document')
def auto_index_document(sender, instance, created, **kwargs):
    """
    Automatically index a document into the RAG vector store after it is saved.
    Runs in a background daemon thread so it never blocks the HTTP request.
    Only indexes PDFs that have not been indexed yet.
    """
    # Must have a file
    if not instance.file:
        return

    try:
        file_path = instance.file.path
    except Exception:
        return

    # Only PDF files are supported
    if not file_path.lower().endswith('.pdf'):
        return

    # Skip if already indexed (avoid re-indexing on every save)
    try:
        from .models import DocumentEmbedding
        emb = DocumentEmbedding.objects.get(document=instance)
        if emb.is_indexed:
            return
    except Exception:
        pass  # No embedding record yet — we will create one in the thread

    # Start background indexing thread
    thread = threading.Thread(
        target=_index_in_background,
        args=(instance.id,),
        daemon=True,
        name=f"rag-index-{instance.id}",
    )
    thread.start()


def _index_in_background(document_id: int):
    """Index a document in a background thread — called by the signal."""
    try:
        import django
        # Django ORM is safe to use in threads after setup
        from .models import Document, DocumentEmbedding
        from .rag_views import get_rag_chatbot

        document = Document.objects.get(id=document_id)

        if not document.file:
            return

        file_path = document.file.path
        if not file_path.lower().endswith('.pdf'):
            return

        # Get or create the embedding tracking record
        embedding, _ = DocumentEmbedding.objects.get_or_create(document=document)

        # Skip if it was indexed by another thread between signal fire and now
        if embedding.is_indexed:
            return

        embedding.mark_processing()
        logger.info(f"[RAG] Auto-indexing started: {document.title!r}")

        chatbot = get_rag_chatbot()
        chatbot.index_documents(
            pdf_path=file_path,
            extract_tables=chatbot.config.ENABLE_TABLE_EXTRACTION,
            describe_images=chatbot.config.ENABLE_IMAGE_DESCRIPTION,
        )

        stats = chatbot.document_processor.get_processing_stats()
        embedding.mark_completed(
            chunk_count=stats.get('total_pages', 0),
            embedding_model=chatbot.config.EMBEDDING_MODEL,
        )

        logger.info(
            f"[RAG] Auto-indexed {document.title!r} — "
            f"{stats.get('total_pages', 0)} pages, "
            f"{stats.get('tables_extracted', 0)} tables"
        )

    except Exception as exc:
        logger.error(f"[RAG] Auto-indexing failed for document {document_id}: {exc}", exc_info=True)
        try:
            from .models import DocumentEmbedding
            emb = DocumentEmbedding.objects.get(document_id=document_id)
            emb.mark_failed(str(exc))
        except Exception:
            pass
