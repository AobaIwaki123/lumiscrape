"""PostgreSQL client for storing and upserting canonical event records."""

import os
from collections.abc import Sequence

import psycopg

from core.exceptions import DatabaseError
from core.schemas import EventSchedule


class PostgresClient:
    """Handles persistence of canonical data models into PostgreSQL."""

    def __init__(self, dsn: str | None = None) -> None:
        self.dsn: str = (
            dsn
            or os.getenv("DATABASE_URL")
            or "postgresql://lumiscrape:lumiscrape@localhost:5432/lumiscrape"
        )

    def init_tables(self) -> None:
        """Creates table schemas if they do not exist."""
        query = """
        CREATE TABLE IF NOT EXISTS event_schedules (
            id SERIAL PRIMARY KEY,
            site_id VARCHAR(64) NOT NULL,
            source_url TEXT NOT NULL,
            title TEXT NOT NULL,
            start_at TIMESTAMPTZ NOT NULL,
            end_at TIMESTAMPTZ,
            venue TEXT,
            description TEXT,
            raw_payload_key TEXT,
            extracted_via VARCHAR(32) NOT NULL DEFAULT 'mechanical',
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_event_source UNIQUE (site_id, source_url, start_at)
        );
        """
        try:
            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                conn.commit()
        except Exception as e:
            raise DatabaseError(f"Failed to initialize database tables: {e}") from e

    def upsert_events(self, events: Sequence[EventSchedule]) -> int:
        """Upserts canonical event records into PostgreSQL."""
        if not events:
            return 0

        query = """
        INSERT INTO event_schedules (
            site_id, source_url, title, start_at, end_at, venue, description, raw_payload_key, extracted_via, updated_at
        ) VALUES (
            %(site_id)s, %(source_url)s, %(title)s, %(start_at)s, %(end_at)s, %(venue)s, %(description)s, %(raw_payload_key)s, %(extracted_via)s, CURRENT_TIMESTAMP
        )
        ON CONFLICT (site_id, source_url, start_at) DO UPDATE SET
            title = EXCLUDED.title,
            end_at = EXCLUDED.end_at,
            venue = EXCLUDED.venue,
            description = EXCLUDED.description,
            raw_payload_key = EXCLUDED.raw_payload_key,
            extracted_via = EXCLUDED.extracted_via,
            updated_at = CURRENT_TIMESTAMP;
        """
        try:
            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    for event in events:
                        params = {
                            "site_id": event.site_id,
                            "source_url": str(event.source_url),
                            "title": event.title,
                            "start_at": event.start_at,
                            "end_at": event.end_at,
                            "venue": event.venue,
                            "description": event.description,
                            "raw_payload_key": event.raw_payload_key,
                            "extracted_via": event.extracted_via,
                        }
                        cur.execute(query, params)
                conn.commit()
            return len(events)
        except Exception as e:
            raise DatabaseError(f"Failed to upsert events to PostgreSQL: {e}") from e
