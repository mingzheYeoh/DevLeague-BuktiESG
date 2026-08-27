"""Argon2 password hashing.

The only module that ever sees a plaintext password. Everything else in the
codebase handles the hash, so a stack trace, a log line or a debugger session
anywhere but here cannot expose a credential.

Argon2id rather than bcrypt: it is the current password-hashing competition
winner and is memory-hard, which is what makes GPU-parallel cracking expensive
rather than merely slow. The library's defaults are deliberately not tuned
here - a hand-picked cost parameter is a guess that ages badly, while the
library's default moves with the library.
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()

#: A real argon2 hash of a value no one holds. `verify_password` against this
#: costs what a genuine verification costs, which is how the login path spends
#: the same time on an address that has no account as on one that does. Without
#: it, response time alone answers "is this email registered?".
DUMMY_HASH = _hasher.hash("bukti-esg-dummy-password-not-a-credential")


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, stored_hash: str) -> bool:
    """True when `plain` produced `stored_hash`.

    Every failure is False, never an exception. A malformed hash is a data
    problem, and turning it into a 500 would let an attacker distinguish
    accounts with broken rows from accounts that merely rejected the password.
    """
    try:
        return _hasher.verify(stored_hash, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
