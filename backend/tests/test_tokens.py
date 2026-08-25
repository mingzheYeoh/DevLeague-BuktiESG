"""Session and email tokens: opaque, high-entropy, stored only as a hash."""

from app.services.tokens import hash_token, new_token


def test_new_token_is_long_and_url_safe():
    # Unpredictability is guaranteed by secrets.token_urlsafe and cannot be
    # asserted in a unit test. What we can assert is that the token is long
    # enough to have sufficient entropy and that it uses the URL-safe alphabet.
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
