"""Comprehensive diagnostic and repair script for repomind-ai indexing failures."""
import os, sys, textwrap, traceback

def report():
    print("="*60)
    print("REPOMIND-AI INDEXING FAILURE DIAGNOSIS")
    print("="*60)
    # 1. Source of error
    print("\n1. ERROR SOURCE")
    print("   File: backend/app/api/repositories.py")
    print("   Line: 58 (inside _index try/except)")
    print("   Message: 'Repository clone or indexing failed...'")
    print("   Trigger: ANY exception in clone_or_pull() OR RepositoryProcessor.process()")

    # 2. Dependency check
    print("\n2. DEPENDENCY STATUS (tested from this session)")
    deps = {
        "python": True,
        "git": (os.system("git --version >nul 2>&1") == 0) if os.name == 'nt' else (os.system("git --version >/dev/null 2>&1") == 0),
        "fastapi": False, "sqlalchemy": False, "pydantic": False,
        "chromadb": False, "fastembed": False, "langchain": False,
        "gitpython": False,
    }
    try:
        import fastapi; deps["fastapi"] = True
    except ImportError: pass
    try:
        import sqlalchemy; deps["sqlalchemy"] = True
    except ImportError: pass
    try:
        import pydantic; deps["pydantic"] = True
    except ImportError: pass
    try:
        import chromadb; deps["chromadb"] = True
    except ImportError: pass
    try:
        import fastembed; deps["fastembed"] = True
    except ImportError: pass
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter; deps["langchain"] = True
    except ImportError: pass
    try:
        import git; deps["gitpython"] = True
    except ImportError: pass
    for k, v in deps.items():
        status = "OK" if v else "MISSING"
        print(f"   {k:12} -> {status}")

    # 3. Config / env check
    print("\n3. CONFIG / ENV")
    env_path = r"d:\python\Usama-Rasheed\lec_26\repomind-ai\backend\.env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            lines = f.read().splitlines()
        for l in lines:
            if l.startswith("EMBEDDING_MODEL="):
                val = l.split("=", 1)[1]
                correct = "sentence-transformers/all-MiniLM-L6-v2"
                ok = val == correct
                print(f"   EMBEDDING_MODEL={val}")
                print(f"   Expected: {correct}")
                print(f"   Status: {'CORRECT' if ok else 'WRONG -> causes ValueError in FastEmbed'}")
            if l.startswith("CHROMA_DB_PATH="):
                val = l.split("=", 1)[1]
                print(f"   CHROMA_DB_PATH={val}")
            if l.startswith("REPOS_PATH="):
                val = l.split("=", 1)[1]
                print(f"   REPOS_PATH={val}")
    else:
        print("   .env file NOT FOUND at expected path")

    # 4. Data dirs
    print("\n4. DATA DIRECTORIES")
    base = r"d:\python\Usama-Rasheed\lec_26\repomind-ai\backend"
    for sub in ["data/repos", "data/chroma_db"]:
        p = os.path.join(base, sub)
        exists = os.path.isdir(p)
        writable = os.access(p, os.W_OK) if exists else False
        print(f"   {sub}: exist={exists}, writable={writable}")

    # 5. Model test (fastembed)
    print("\n5. FASTEMBED MODEL TEST")
    try:
        from fastembed import TextEmbedding
        for name in ["all-MiniLM-L6-v2", "sentence-transformers/all-MiniLM-L6-v2"]:
            try:
                m = TextEmbedding(name)
                v = list(m.embed(["test"]))
                ok = len(v) > 0 and len(v[0]) > 0
                print(f"   name='{name}' -> OK (dims={len(v[0])})")
            except Exception as e:
                print(f"   name='{name}' -> FAIL: {str(e)[:80]}")
    except Exception as e:
        print(f"   FastEmbed import failed: {e}")

    # 6. GitHub clone test (brief)
    print("\n6. GIT CLONE TEST (public repo, 5 sec timeout)")
    import tempfile, subprocess, shutil
    test_dir = tempfile.mkdtemp(prefix="repo_test_")
    try:
        cmd = ["git", "clone", "--depth", "1", "--branch", "main", "https://github.com/KHOKHAR-CODES/PYTHON-CODES", test_dir]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        print(f"   returncode={res.returncode}")
        if res.returncode != 0:
            print(f"   stderr: {res.stderr[:200]}")
        else:
            print("   Clone OK")
    except Exception as e:
        print(f"   Exception: {e}")
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

    # 7. Fix instructions
    print("\n7. REQUIRED FIXES")
    fixes = [
        "Fix .env EMBEDDING_MODEL: change 'all-MiniLM-L6-v2' to 'sentence-transformers/all-MiniLM-L6-v2'",
        "Create missing directories: backend/data/repos and backend/data/chroma_db",
        "Install all requirements: pip install -r backend/requirements.txt (inside venv)",
        "Verify repo URL is public HTTPS github.com/owner/repo and branch exists (default main)",
        "Check backend logs (console / uvicorn) for exact exception trace when error occurs",
    ]
    for i, f in enumerate(fixes, 1):
        print(f"   {i}. {f}")

    print("\n" + "="*60)
    print("END DIAGNOSIS")
    print("="*60)

if __name__ == "__main__":
    report()
