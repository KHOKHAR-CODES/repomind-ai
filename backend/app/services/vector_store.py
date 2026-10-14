import hashlib

import chromadb


def _make_ids(metadata_list):
    return [hashlib.md5((
        str(metadata.get("user_id", "")) + "_" + str(metadata.get("repository_id", "")) + "_" +
        str(metadata.get("file_path", "")) + "_" + str(metadata.get("start_line", 0))
    ).encode("utf-8")).hexdigest() for metadata in metadata_list]

class VectorStore:
    def __init__(self, path="./data/chroma_db"):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name="repo_chunks")

    def add_chunks(self, chunks, embeddings, metadata_list):
        if not chunks:
            return []
        if not (len(chunks) == len(embeddings) == len(metadata_list)):
            raise ValueError("chunks, embeddings and metadata must have the same length")
        ids = _make_ids(metadata_list)
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=[chunk["content"] for chunk in chunks],
            metadatas=metadata_list,
        )
        return ids

    def prune_repo(self, user_id, repo_id, keep_ids):
        """Remove stale chunks after a complete successful reindex; deletes are bounded."""
        where = {"$and": [{"user_id": int(user_id)}, {"repository_id": int(repo_id)}]}
        existing = self.collection.get(where=where, include=["metadatas"])
        current_ids = existing.get("ids") or []
        keep = set(keep_ids or [])
        stale = [item for item in current_ids if item not in keep]
        for start in range(0, len(stale), 500):
            self.collection.delete(ids=stale[start:start + 500])
        return len(stale)

    def query_chunks(self, query_embedding, user_id, repo_id, top_k=5):
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"$and": [{"user_id": user_id}, {"repository_id": repo_id}]},
        )
        return results

    def delete_repo(self, user_id, repo_id):
        self.collection.delete(where={"$and": [{"user_id": user_id}, {"repository_id": repo_id}]})
