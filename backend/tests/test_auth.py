from app.core.security import verify_password, get_hash

def test_bcrypt_hash_and_verify():
    pw = "my-secret"
    h = get_hash(pw)
    assert verify_password(pw, h)
    assert not verify_password("other", h)
