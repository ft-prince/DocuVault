from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "documents"

    def ready(self):
        import documents.signals  # noqa: F401 — register auto-index signal

        # On startup, any document stuck in 'processing' means the server was
        # killed mid-index (daemon thread was interrupted). Reset them to
        # 'pending' and re-queue them so they get indexed on this run.
        self._requeue_stuck_documents()

    @staticmethod
    def _requeue_stuck_documents():
        """
        Reset documents stuck in 'processing' from a previous interrupted run
        and add them back to the indexing queue.
        """
        try:
            from documents.models import DocumentEmbedding
            from documents.signals import _ensure_worker, _index_queue

            stuck = DocumentEmbedding.objects.filter(
                index_status='processing'
            ).select_related('document')

            count = stuck.count()
            if not count:
                return

            # Reset to pending so the atomic claim in _index_in_background works
            stuck.update(index_status='pending')

            _ensure_worker()
            for emb in stuck:
                if emb.document_id:
                    _index_queue.put(emb.document_id)

            import logging
            logging.getLogger(__name__).info(
                f"[RAG] Re-queued {count} document(s) interrupted by previous shutdown."
            )

        except Exception as exc:
            # Never crash on startup — just log and continue
            import logging
            logging.getLogger(__name__).warning(
                f"[RAG] Could not re-queue stuck documents: {exc}"
            )
