"""Opaque tokens for sessions, email verification, reset and invitations.

Two properties, and they pull in different directions from password hashing:

  * Unpredictable. A token is the credential; guessing one is impersonation.
    `secrets.token_urlsafe` draws from the OS CSPRNG, not `random`.
  * Deterministically hashed. Lookup is *by* the hash - there is no row to read
    a per-token salt from before hashing. That rules out argon2 here, and it is
    safe for the same reason it is unsafe for passwords: a 256-bit random token
    has no dictionary to attack, so the slow-hash defence buys nothing.

SHA-256 rather than a password hash is therefore a deliberate difference from
`services/passwords.py`, not an inconsistency.
"""

from __future__ import annotations

import hashlib
import secrets

#: 32 bytes of entropy, URL-safe so it can travel in an email link unescaped.
_TOKEN_BYTES = 32


def new_token() -> str:
    return secrets.token_urlsafe(_TOKEN_BYTES)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
