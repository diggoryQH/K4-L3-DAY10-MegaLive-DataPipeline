from __future__ import annotations

import hashlib
from functools import lru_cache
import math
import os

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=4)
def _load_model(model_name: str) -> SentenceTransformer | None:
    try:
        if os.getenv("ALLOW_MODEL_DOWNLOAD", "").lower() in {"1", "true", "yes"}:
            return SentenceTransformer(model_name)
        return SentenceTransformer(model_name, local_files_only=True)
    except Exception:
        return None


class MiniLMEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = _load_model(model_name)
        self.fallback_dimensions = 384

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self.model is None:
            return [self._hash_embedding(text) for text in texts]
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        if self.model is None:
            return self._hash_embedding(text)
        embedding = self.model.encode([text], normalize_embeddings=True)
        return embedding[0].tolist()

    def _hash_embedding(self, text: str) -> list[float]:
        vector = [0.0] * self.fallback_dimensions
        for token in text.lower().split():
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.fallback_dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
