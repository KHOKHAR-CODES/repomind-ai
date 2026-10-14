from app.services.vector_store import VectorStore

def test_filter_by_repo_and_user():
    store = VectorStore(path="./data/test_chroma_filter")
    # Dummy insertion followed by filtered query
    chunks = [{"content": "test chunk"}]
    embeddings = [[0.5]*384]
    meta = [{"user_id": 42, "repository_id": 7, "repo_name": "x", "repo_url": "", "file_path": "a.py", "start_line": 1, "end_line": 1, "commit_hash": "h"}]
    store.add_chunks(chunks, embeddings, meta)
    result = store.query_chunks([0.5]*384, 42, 7, top_k=1)
    assert len(result.get("ids", [[]])[0]) == 1
