from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    """Enable WAL so dashboard reads never block on a long-running scrape write.

    In the default rollback-journal mode a long write transaction (e.g. a big
    scrape that stages inserts and scores each job serially before committing)
    holds a lock that makes concurrent reads fail with "database is locked",
    which made the dashboard show 0 jobs until the scrape finished. WAL lets
    readers and the single writer run concurrently; busy_timeout gives writers
    room to wait instead of erroring immediately.
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
