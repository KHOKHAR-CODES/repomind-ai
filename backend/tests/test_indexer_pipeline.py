import tempfile
import unittest
from pathlib import Path
from app.services.indexer import Indexer

class FakeEmbedder:
    def __init__(self): self.calls=[]
    def embed(self, texts, batch_size=64):
        self.calls.append((len(texts), batch_size))
        return [[0.1, 0.2, 0.3] for _ in texts]

class FakeStore:
    def __init__(self): self.batches=[]; self.pruned=None; self.metadata=[]
    def add_chunks(self, chunks, embeddings, metadata):
        self.batches.append((len(chunks), len(embeddings), len(metadata)))
        self.metadata.extend(metadata)
        return [f"{m['file_path']}:{m['start_line']}" for m in metadata]
    def prune_repo(self, user_id, repo_id, keep_ids): self.pruned=(user_id,repo_id,list(keep_ids))

class IndexerTests(unittest.TestCase):
    def test_bulk_embedding_persistence_and_actual_file_count(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for n in range(150):
                (root / f"module_{n}.py").write_text(f"def f{n}():\n    return {n}\n", encoding="utf-8")
            embedder=FakeEmbedder(); store=FakeStore()
            stats=Indexer(vector_store=store, embedder=embedder).index_repository(
                str(root), user_id=3, repo_id=7, repo_name="demo", repo_url="https://github.com/x/demo"
            )
            self.assertEqual(stats.file_count,150)
            self.assertEqual(stats.chunk_count,150)
            self.assertTrue(embedder.calls)
            self.assertTrue(all(size == 64 for _,size in embedder.calls))
            self.assertTrue(all(a == b == c and a <= 300 for a,b,c in store.batches))
            self.assertTrue(all(m["language"] == "python" for m in store.metadata))
            self.assertEqual(store.pruned[:2],(3,7))
            self.assertEqual(len(store.pruned[2]),stats.chunk_count)

if __name__ == "__main__":
    unittest.main()
