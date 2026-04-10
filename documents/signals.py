"""
Auto-indexing signals for RAG system.
Supports PDF, TXT, MD, DOCX — indexes into ChromaDB on document save.
"""

import os
import threading
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

# All file types the indexer can handle
SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.md', '.text', '.docx', '.doc'}


@receiver(post_save, sender='documents.Document')
def auto_index_document(sender, instance, created, **kwargs):
    """
    Automatically index any supported document into the RAG vector store.
    Runs in a daemon background thread — never blocks the HTTP request.
    """
    if not instance.file:
        return

    try:
        file_path = instance.file.path
    except Exception:
        return

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        logger.debug(f"[RAG] Skipping unsupported file type: {ext}")
        return

    # Skip if already successfully indexed
    try:
        from .models import DocumentEmbedding
        emb = DocumentEmbedding.objects.get(document=instance)
        if emb.is_indexed:
            return
    except Exception:
        pass  # No record yet — thread will create one

    thread = threading.Thread(
        target=_index_in_background,
        args=(instance.id,),
        daemon=True,
        name=f"rag-index-{instance.id}",
    )
    thread.start()


def _load_text_file(file_path: str, document):
    """
    Load a plain-text / markdown file as a list of LangChain Document objects.
    Each ~500-word block becomes one document to give the chunker good material.
    """
    from langchain_core.documents import Document as LCDoc

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as fh:
        raw = fh.read()

    if not raw.strip():
        return []

    # Split on double newlines (paragraphs), re-join into ~500-word pages
    paragraphs = [p.strip() for p in raw.split('\n\n') if p.strip()]
    pages, current, word_count = [], [], 0
    for para in paragraphs:
        words = len(para.split())
        if word_count + words > 500 and current:
            pages.append('\n\n'.join(current))
            current, word_count = [], 0
        current.append(para)
        word_count += words
    if current:
        pages.append('\n\n'.join(current))

    docs = []
    for i, page_text in enumerate(pages, 1):
        docs.append(LCDoc(
            page_content=page_text,
            metadata={
                'source': file_path,
                'title': getattr(document, 'title', os.path.basename(file_path)),
                'page': i,
                'content_type': 'text',
                'file_type': os.path.splitext(file_path)[1].lower().lstrip('.'),
            }
        ))
    return docs


def _load_docx_file(file_path: str, document):
    """Load a .docx file as LangChain Document objects (paragraph-by-paragraph)."""
    try:
        from docx import Document as DocxDoc
        from langchain_core.documents import Document as LCDoc
    except ImportError:
        logger.warning("[RAG] python-docx not installed — cannot index .docx files. "
                       "Run: pip install python-docx")
        return []

    docx = DocxDoc(file_path)
    paragraphs = [p.text.strip() for p in docx.paragraphs if p.text.strip()]
    if not paragraphs:
        return []

    pages, current, word_count = [], [], 0
    for para in paragraphs:
        words = len(para.split())
        if word_count + words > 500 and current:
            pages.append('\n\n'.join(current))
            current, word_count = [], 0
        current.append(para)
        word_count += words
    if current:
        pages.append('\n\n'.join(current))

    docs = []
    for i, page_text in enumerate(pages, 1):
        docs.append(LCDoc(
            page_content=page_text,
            metadata={
                'source': file_path,
                'title': getattr(document, 'title', os.path.basename(file_path)),
                'page': i,
                'content_type': 'text',
                'file_type': 'docx',
            }
        ))
    return docs


def _index_in_background(document_id: int):
    """Index one document in a background thread. Called by the post_save signal."""
    try:
        from .models import Document, DocumentEmbedding
        from .rag_views import get_rag_chatbot

        document = Document.objects.get(id=document_id)
        if not document.file:
            return

        file_path = document.file.path
        ext = os.path.splitext(file_path)[1].lower()

        if ext not in SUPPORTED_EXTENSIONS:
            return

        embedding, _ = DocumentEmbedding.objects.get_or_create(document=document)
        if embedding.is_indexed:
            return

        embedding.mark_processing()
        logger.info(f"[RAG] Indexing started ({ext}): {document.title!r}")

        # get_rag_chatbot() is lock-protected: if initialization is still in
        # progress on another thread this call blocks until it completes,
        # so index_documents() is never called on an uninitialized system.
        chatbot = get_rag_chatbot()

        # ── Route by file type ──────────────────────────────────────────
        if ext == '.pdf':
            chatbot.index_documents(
                pdf_path=file_path,
                extract_tables=chatbot.config.ENABLE_TABLE_EXTRACTION,
                describe_images=chatbot.config.ENABLE_IMAGE_DESCRIPTION,
            )
            stats = chatbot.document_processor.get_processing_stats()
            chunk_count = stats.get('total_pages', 0)

        elif ext in {'.txt', '.md', '.text'}:
            lc_docs = _load_text_file(file_path, document)
            if not lc_docs:
                embedding.mark_failed("File appears to be empty")
                return
            chatbot.index_documents(documents=lc_docs)
            chunk_count = len(lc_docs)

        elif ext in {'.docx', '.doc'}:
            lc_docs = _load_docx_file(file_path, document)
            if not lc_docs:
                embedding.mark_failed("Could not extract text from .docx")
                return
            chatbot.index_documents(documents=lc_docs)
            chunk_count = len(lc_docs)

        else:
            embedding.mark_failed(f"Unsupported extension: {ext}")
            return

        embedding.mark_completed(
            chunk_count=chunk_count,
            embedding_model=chatbot.config.EMBEDDING_MODEL,
        )
        logger.info(f"[RAG] Indexed {document.title!r} — {chunk_count} chunks ({ext})")

    except Exception as exc:
        logger.error(f"[RAG] Indexing failed for document {document_id}: {exc}", exc_info=True)
        try:
            from .models import DocumentEmbedding
            emb = DocumentEmbedding.objects.get(document_id=document_id)
            emb.mark_failed(str(exc))
        except Exception:
            pass
