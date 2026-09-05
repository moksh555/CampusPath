from unittest.mock import MagicMock

from sqlalchemy.dialects import postgresql

from app.modules.auth.repository import upsert_google_user


def test_google_subject_is_the_conflict_key():
    db = MagicMock()
    result = upsert_google_user(db, {"sub": "stable-id", "email": "s@example.test"})
    statement = db.scalar.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())
    assert "ON CONFLICT (google_subject) DO UPDATE" in str(compiled)
    assert compiled.params["name"] == "Student"
    assert compiled.params["google_subject"] == "stable-id"
    assert result is db.scalar.return_value
