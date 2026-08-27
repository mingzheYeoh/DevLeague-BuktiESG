"""Password hashing. The one place a plaintext password may be seen."""

from app.services.passwords import hash_password, verify_password


def test_hash_then_verify_accepts_the_same_password():
    stored = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", stored) is True


def test_verify_rejects_a_different_password():
    stored = hash_password("correct horse battery staple")
    assert verify_password("Correct Horse Battery Staple", stored) is False


def test_the_hash_does_not_contain_the_password():
    stored = hash_password("hunter2")
    assert "hunter2" not in stored


def test_two_hashes_of_one_password_differ():
    # A per-hash salt. Equal hashes would mean equal passwords are visible to
    # anyone who reads the table, which is half of what hashing is for.
    assert hash_password("same") != hash_password("same")


def test_verify_against_a_malformed_hash_is_false_not_an_exception():
    # Reached if a row is corrupted or hand-edited. A 500 here would tell an
    # attacker which accounts have broken hashes.
    assert verify_password("anything", "not-a-hash") is False

