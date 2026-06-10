"""Vector store abstraction: Weaviate, Pinecone, or local Chroma."""

from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from src.config import settings
from src.llm.vertex_client import vertex_client


class VectorStore:
    def __init__(self) -> None:
        self.provider = settings.vector_db_provider
        self._client = None
        self._collection = None
        self._init_store()

    def _init_store(self) -> None:
        if self.provider == "weaviate":
            self._init_weaviate()
        elif self.provider == "pinecone":
            self._init_pinecone()
        else:
            self._init_chroma()

    def _init_chroma(self) -> None:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        self._client = chromadb.PersistentClient(
            path=str(settings.chroma_persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name="retail_design_chunks",
            metadata={"hnsw:space": "cosine"},
        )

    def _init_weaviate(self) -> None:
        import weaviate
        from weaviate.classes.config import Configure, Property, DataType

        auth = None
        if settings.weaviate_api_key:
            import weaviate.classes as wvc

            auth = wvc.init.Auth.api_key(settings.weaviate_api_key)

        self._client = weaviate.connect_to_custom(
            http_host=settings.weaviate_url.replace("https://", "").replace("http://", "").split(":")[0],
            http_port=8080,
            http_secure=settings.weaviate_url.startswith("https"),
            grpc_port=50051,
            auth_credentials=auth,
        )
        class_name = settings.weaviate_class_name
        if not self._client.collections.exists(class_name):
            self._client.collections.create(
                name=class_name,
                vectorizer_config=Configure.Vectorizer.none(),
                properties=[
                    Property(name="text", data_type=DataType.TEXT),
                    Property(name="source_document", data_type=DataType.TEXT),
                    Property(name="filename", data_type=DataType.TEXT),
                    Property(name="chunk_index", data_type=DataType.INT),
                ],
            )
        self._collection = self._client.collections.get(class_name)

    def _init_pinecone(self) -> None:
        from pinecone import Pinecone, ServerlessSpec

        pc = Pinecone(api_key=settings.pinecone_api_key)
        if settings.pinecone_index_name not in [i.name for i in pc.list_indexes()]:
            pc.create_index(
                name=settings.pinecone_index_name,
                dimension=768,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=settings.pinecone_environment),
            )
        self._index = pc.Index(settings.pinecone_index_name)

    def upsert_chunks(self, chunks: list[dict]) -> int:
        if not chunks:
            return 0
        texts = [c["text"] for c in chunks]
        vectors = vertex_client.embed_documents(texts)
        if self.provider == "chroma":
            ids = [str(uuid4()) for _ in chunks]
            self._collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=vectors,
                metadatas=[c["metadata"] for c in chunks],
            )
        elif self.provider == "weaviate":
            with self._collection.batch.dynamic() as batch:
                for c, vec in zip(chunks, vectors):
                    batch.add_object(
                        properties={
                            "text": c["text"],
                            **c["metadata"],
                        },
                        vector=vec,
                    )
        elif self.provider == "pinecone":
            records = []
            for c, vec in zip(chunks, vectors):
                rid = str(uuid4())
                meta = {**c["metadata"], "text": c["text"][:1000]}
                records.append({"id": rid, "values": vec, "metadata": meta})
            self._index.upsert(vectors=records)
        return len(chunks)

    def query(self, query_text: str, top_k: int = 8) -> list[dict[str, Any]]:
        qvec = vertex_client.embed_query(query_text)
        if self.provider == "chroma":
            res = self._collection.query(
                query_embeddings=[qvec],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
            out = []
            for doc, meta, dist in zip(
                res["documents"][0],
                res["metadatas"][0],
                res["distances"][0],
            ):
                out.append({"text": doc, "metadata": meta, "score": 1 - dist})
            return out
        if self.provider == "weaviate":
            from weaviate.classes.query import MetadataQuery

            response = self._collection.query.near_vector(
                near_vector=qvec,
                limit=top_k,
                return_metadata=MetadataQuery(distance=True),
            )
            return [
                {
                    "text": obj.properties.get("text", ""),
                    "metadata": {
                        k: obj.properties.get(k)
                        for k in ("source_document", "filename", "chunk_index")
                    },
                    "score": 1 - (obj.metadata.distance or 0),
                }
                for obj in response.objects
            ]
        if self.provider == "pinecone":
            res = self._index.query(vector=qvec, top_k=top_k, include_metadata=True)
            return [
                {
                    "text": m.metadata.get("text", ""),
                    "metadata": {k: m.metadata.get(k) for k in ("source_document", "filename", "chunk_index")},
                    "score": m.score,
                }
                for m in res.matches
            ]
        return []

    def count(self) -> int:
        if self.provider == "chroma":
            return self._collection.count()
        return -1


_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
