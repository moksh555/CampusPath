"""Consolidate cell answers into chats and replace per-cell jobs with session jobs."""

from alembic import op
from sqlalchemy import inspect, text

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    connection.execute(
        text(
            "ALTER TABLE platform.chats ADD COLUMN IF NOT EXISTS research_results JSONB NOT NULL DEFAULT '{}'"
        )
    )
    connection.execute(
        text(
            "ALTER TABLE platform.chats ADD COLUMN IF NOT EXISTS research_revision INTEGER NOT NULL DEFAULT 0"
        )
    )
    tables = set(inspect(connection).get_table_names(schema="platform"))
    if "cells" in tables:
        connection.execute(
            text("""
            WITH rows AS (
                SELECT r.chat_id, r.id AS row_id,
                    jsonb_object_agg(c.column_id::text, jsonb_build_object(
                        'id', c.id::text, 'column_id', c.column_id::text,
                        'value', c.value, 'status', CASE WHEN c.status IN ('queued','running') THEN 'stale' ELSE c.status END,
                        'sources', c.sources::jsonb, 'researched_at', c.researched_at,
                        'error_code', NULL, 'error_message', NULL
                    )) AS cells
                FROM platform.cells c JOIN platform.college_rows r ON r.id=c.college_row_id
                GROUP BY r.chat_id, r.id
            ), sessions AS (
                SELECT chat_id, jsonb_object_agg(row_id::text, cells) AS document FROM rows GROUP BY chat_id
            )
            UPDATE platform.chats c SET research_results=s.document,
                research_revision=c.research_revision+1 FROM sessions s WHERE c.id=s.chat_id
        """)
        )
    columns = {
        column["name"]
        for column in inspect(connection).get_columns(
            "research_jobs", schema="platform"
        )
    }
    if "cell_id" in columns:
        connection.execute(
            text("""CREATE TABLE platform.session_jobs_migration (
            id UUID PRIMARY KEY, chat_id UUID NOT NULL UNIQUE REFERENCES platform.chats(id) ON DELETE CASCADE,
            revision INTEGER NOT NULL, payload JSON NOT NULL, status VARCHAR NOT NULL,
            attempts INTEGER NOT NULL, lease_until TIMESTAMPTZ, error_code VARCHAR(32)
        )""")
        )
        connection.execute(
            text("""INSERT INTO platform.session_jobs_migration
            (id, chat_id, revision, payload, status, attempts)
            SELECT min(j.id::text)::uuid, r.chat_id, max(ch.research_revision), '{}', 'superseded', 0
            FROM platform.research_jobs j JOIN platform.cells c ON c.id=j.cell_id
            JOIN platform.college_rows r ON r.id=c.college_row_id
            JOIN platform.chats ch ON ch.id=r.chat_id GROUP BY r.chat_id""")
        )
        connection.execute(text("DROP TABLE platform.research_jobs"))
        connection.execute(
            text("ALTER TABLE platform.session_jobs_migration RENAME TO research_jobs")
        )
        connection.execute(
            text(
                "CREATE INDEX ix_platform_research_jobs_status ON platform.research_jobs(status)"
            )
        )
    if "cells" in tables:
        connection.execute(text("DROP TABLE platform.cells"))


def downgrade():
    raise RuntimeError("Restore a database backup to undo session result consolidation")
