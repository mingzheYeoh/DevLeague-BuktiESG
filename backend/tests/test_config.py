"""Where configuration is read from, and how `database_url` is arrived at.

`app/config.py` had no tests, and the two defects below were both silent.

`env_file=".env"` is resolved against the *current working directory*, so the
backend only ever read its configuration when launched from `backend/`. From
anywhere else it read nothing, fell through to the SQLite default, and started
normally against an empty local file. Nothing said so. Measured before the fix:

    from / :        sqlite:///./buktiesg_dev.db
    from backend/ : postgresql+psycopg://buktiesg:...

The second defect was the same password written twice - once as
`POSTGRES_PASSWORD` for docker-compose, once inside `backend/.env`'s
`DATABASE_URL`. Changing one left the other disagreeing, and the symptom was
an authentication failure that named neither file.
"""

from __future__ import annotations

from pathlib import Path

from app.config import Settings


def test_the_env_file_is_read_from_the_repository_root_not_the_working_directory(
    monkeypatch, tmp_path
):
    """The regression itself: a decoy `.env` in the CWD must be ignored.

    Written this way rather than as an assertion about the configured path
    because the path is the mechanism, not the behaviour. Under the old
    `env_file=".env"` this reads the decoy and fails; under an anchored path
    the CWD is irrelevant, which is the whole point.
    """
    (tmp_path / ".env").write_text("POSTGRES_PASSWORD=decoy-must-not-be-read\n")
    monkeypatch.chdir(tmp_path)

    assert Settings().postgres_password != "decoy-must-not-be-read"


def test_the_configured_env_file_sits_beside_docker_compose():
    """Both readers, one file. Compose reads the `.env` next to
    `docker-compose.yml`; this pins that the app reads the same one."""
    env_file = Path(Settings.model_config["env_file"])

    assert env_file.is_absolute()
    assert (env_file.parent / "docker-compose.yml").exists()


def test_the_password_alone_is_enough_to_reach_the_compose_database():
    """`DATABASE_URL` is derived, so the password is written in one place.

    127.0.0.1 rather than `localhost` on purpose - Compose binds the IPv4
    loopback only, and on Windows `localhost` resolves to ::1 first and stalls
    until that attempt times out.
    """
    settings = Settings(_env_file=None, postgres_password="s3cret")

    assert settings.database_url == (
        "postgresql+psycopg://buktiesg:s3cret@127.0.0.1:5432/buktiesg"
    )


def test_a_password_with_url_punctuation_is_escaped():
    """Built by interpolation, so it has to be escaped. An unescaped `@` moves
    the host boundary and the driver reports a hostname nobody configured."""
    settings = Settings(_env_file=None, postgres_password="p@ss/word")

    assert "p%40ss%2Fword" in settings.database_url
    assert settings.database_url.endswith("@127.0.0.1:5432/buktiesg")


def test_an_explicit_database_url_wins_over_the_password():
    """CI's migration job sets `DATABASE_URL` to reach its own service
    container, and an OS environment variable beats the file. Deriving must
    never overwrite something that was stated."""
    settings = Settings(
        _env_file=None,
        postgres_password="ignored",
        database_url="postgresql+psycopg://someone@elsewhere:5432/other",
    )

    assert settings.database_url == "postgresql+psycopg://someone@elsewhere:5432/other"


def test_with_nothing_configured_it_still_boots_on_sqlite():
    """The emergency fallback, kept deliberately: the app boots without Docker.
    `backend/README.md` records why it is not a supported way to run this -
    no enforced foreign keys, no row locking, and the migrations cannot build
    it."""
    settings = Settings(_env_file=None, postgres_password=None)

    assert settings.database_url == "sqlite:///./buktiesg_dev.db"
