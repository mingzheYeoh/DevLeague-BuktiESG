"""Session and email tokens: opaque, high-entropy, stored only as a hash."""

from app.services.tokens import hash_token, new_token, tokens_match


def test_new_token_is_unpredictable_in_length_and_alphabet():
    token = new_token()
    assert len(token) >= 32
    assert token.isalnum() or "-" in token or "_" in token


def test_two_tokens_are_never_equal():
    assert new_token() != new_token()


def test_hash_is_deterministic():
    # Unlike a password hash. Lookup is by hash, so the same token must always
    # produce the same key - there is no row to read a salt from beforehand.
    token = new_token()
    assert hash_token(token) == hash_token(token)


def test_hash_does_not_contain_the_token():
    token = new_token()
    assert token not in hash_token(token)


def test_tokens_match_accepts_the_original():
    token = new_token()
    assert tokens_match(token, hash_token(token)) is True


def test_tokens_match_rejects_another_token():
    assert tokens_match(new_token(), hash_token(new_token())) is False
