"""Diagnostic: check ChromaDB retrieval for 'The Last Signal' story."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from documents.rag_views import get_rag_chatbot

print("Loading chatbot...")
chatbot = get_rag_chatbot()
vs = chatbot.vector_store

print(f"\nTotal chunks in ChromaDB: {vs.collection.count()}")

# Check what sources are in ChromaDB
print("\n=== SOURCES IN CHROMADB (sample 20) ===")
result = vs.collection.get(limit=200, include=['metadatas'])
sources = set()
for m in result['metadatas']:
    src = m.get('source', m.get('title', 'unknown'))
    sources.add(os.path.basename(str(src)))
for s in sorted(sources):
    print(f"  {s}")

print("\n=== RETRIEVAL TEST: Mara / observatory ===")
queries = [
    "Dr Mara Osei profession observatory radio",
    "signal observatory astronomer",
    "Mara",
    "last signal story",
]
for q in queries:
    docs, metas, sims = chatbot.retriever.retrieve(q, n_results=3, use_hybrid=True)
    print(f"\nQuery: {q!r}  -> {len(docs)} results")
    for d, m, s in zip(docs, metas, sims):
        print(f"  sim={s:.4f} | {str(m.get('source',''))[-45:]}")
        print(f"  {d[:120]!r}")

print("\n=== THRESHOLD CHECK ===")
docs, metas, sims = chatbot.retriever.retrieve("Mara observatory radio", n_results=10, use_hybrid=False)
print(f"Semantic only: {len(docs)} results")
for d, m, s in zip(docs, metas, sims):
    print(f"  sim={s:.4f} | {str(m.get('source',''))[-45:]}")
    print(f"  {d[:100]!r}")
