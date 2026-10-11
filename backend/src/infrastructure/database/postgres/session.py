from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def create_db_engine(database_url: str, *, echo: bool = False) -> Engine:
    # One engine (and its connection pool) per process; created at startup.
    # pool_pre_ping drops connections the server closed while they sat idle in the pool.
    return create_engine(database_url, echo=echo, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    # expire_on_commit=False keeps loaded attributes readable after the request's
    # commit, so mapping to a domain entity never triggers a surprise reload.
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
