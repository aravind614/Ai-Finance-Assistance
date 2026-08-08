import os
import io
import math
import re
import pypdf
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

class LightweightEmbeddings(Embeddings):
    """
    Lightweight, fast pure-Python embedding model.
    Generates 384-dimensional normalized feature vectors for semantic matching
    without requiring PyTorch, TensorFlow, Transformers, or heavy ML frameworks.
    """
    def __init__(self, dim: int = 384):
        self.dim = dim

    def _text_to_vector(self, text: str) -> list[float]:
        text = text.lower()
        words = re.findall(r'\w+', text)
        vec = [0.0] * self.dim
        if not words:
            return vec

        for word in words:
            h = hash(word) % self.dim
            vec[h] += 1.0
            for i in range(len(word) - 2):
                ngram = word[i:i+3]
                h_ng = hash(ngram) % self.dim
                vec[h_ng] += 0.5

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._text_to_vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._text_to_vector(text)

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "financial_reports"

# Initialize embeddings model
embeddings = LightweightEmbeddings()


def get_vectorstore():
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )


def extract_pdf_text_from_bytes(file_bytes: bytes, filename: str) -> tuple[str, int, int]:
    """
    Extract text from PDF bytes.
    Returns (extracted_text, total_pages, total_characters).
    """
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    total_pages = len(reader.pages)
    text_pages = []

    for idx, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if not page_text or len(page_text.strip()) < 10:
            # Fallback to layout extraction mode if available
            try:
                page_text = page.extract_text(extraction_mode="layout") or ""
            except Exception:
                page_text = ""
        if page_text:
            text_pages.append(page_text)

    full_text = "\n\n".join(text_pages)
    return full_text, total_pages, len(full_text)


def ingest_document(text: str, filename: str) -> dict:
    """
    Split text into chunks and save them into the vector store.
    Returns diagnostic stats dict: filename, num_chunks, char_count.
    """
    if not text.strip():
        return {"filename": filename, "num_chunks": 0, "char_count": 0}

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = text_splitter.split_text(text)

    # Create metadata for each chunk
    metadatas = [{"source": filename} for _ in chunks]

    db = get_vectorstore()
    db.add_texts(texts=chunks, metadatas=metadatas)

    return {
        "filename": filename,
        "num_chunks": len(chunks),
        "char_count": len(text)
    }


def query_documents(query: str, k: int = 5) -> list[dict]:
    """
    Query ChromaDB for relevant chunks.
    Includes fallback search for financial terms to maximize recall.
    """
    db = get_vectorstore()
    try:
        if not db._collection or db._collection.count() == 0:
            return []

        # Perform primary similarity search
        docs = db.similarity_search(query, k=k)

        # If primary query returned no docs, try searching simplified query keywords
        if not docs:
            # Clean search term (e.g. "Microsoft revenue" -> "revenue")
            keywords = [w for w in query.split() if len(w) > 3 and w.lower() not in ["what", "was", "were", "the", "from", "with", "that", "this", "about"]]
            if keywords:
                fallback_query = " ".join(keywords)
                docs = db.similarity_search(fallback_query, k=k)

        return [
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in docs
        ]
    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        return []


def get_uploaded_documents() -> list[str]:
    """
    Get a list of unique filenames that have been uploaded and indexed.
    """
    db = get_vectorstore()
    try:
        if not db._collection or db._collection.count() == 0:
            return []

        data = db._collection.get(include=["metadatas"])
        if not data:
            return []

        metadatas = data.get("metadatas") or []
        sources = set()
        for meta in metadatas:
            if meta and "source" in meta:
                sources.add(meta["source"])
        return sorted(list(sources))
    except Exception:
        return []


def clear_knowledge_base():
    """
    Reset Chroma database collection.
    """
    db = get_vectorstore()
    try:
        db.delete_collection()
    except Exception:
        pass

    if os.path.exists(CHROMA_DIR):
        import shutil
        try:
            shutil.rmtree(CHROMA_DIR)
        except Exception:
            pass
