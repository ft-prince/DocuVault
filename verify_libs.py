
import sys
import time

print("1. Starting imports...")
start = time.time()

try:
    import fitz
    print(f"   [OK] fitz imported ({time.time() - start:.2f}s)")
except ImportError as e:
    print(f"   [FAIL] fitz: {e}")

try:
    import chromadb
    print(f"   [OK] chromadb imported ({time.time() - start:.2f}s)")
except ImportError as e:
    print(f"   [FAIL] chromadb: {e}")

try:
    from sentence_transformers import SentenceTransformer
    print(f"   [OK] sentence_transformers imported ({time.time() - start:.2f}s)")
except ImportError as e:
    print(f"   [FAIL] sentence_transformers: {e}")

print("2. Testing PyMuPDF (fitz)...")
try:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((10, 10), "Hello World")
    text = page.get_text()
    print(f"   [OK] Created and read PDF: {text.strip()}")
except Exception as e:
    print(f"   [FAIL] PyMuPDF test: {e}")

print("3. Testing Embedding Model (might download)...")
try:
    model_name = "all-MiniLM-L6-v2"
    print(f"   Loading {model_name}...")
    model = SentenceTransformer(model_name)
    emb = model.encode("test")
    print(f"   [OK] Generated embedding: shape {emb.shape}")
except Exception as e:
    print(f"   [FAIL] Embedding test: {e}")

print("4. Testing ChromaDB...")
try:
    client = chromadb.Client()
    collection = client.create_collection("test_collection")
    collection.add(
        documents=["This is a test"],
        metadatas=[{"source": "test"}],
        ids=["id1"]
    )
    results = collection.query(query_texts=["test"], n_results=1)
    print(f"   [OK] ChromaDB query result: {results['documents'][0][0]}")
except Exception as e:
    print(f"   [FAIL] ChromaDB test: {e}")

print("Done.")
