from sqlmodel import create_engine, SQLModel, text

from .utils import get_env_variable


def build_connection_string(user: str, host: str) -> str:
    """
    Build a PostgreSQL connection string from individual components.

    Args:
        user: PostgreSQL username
        host: PostgreSQL host (can include port/database or be full connection details)

    Returns:
        Complete PostgreSQL connection string
    """
    password = get_env_variable("PGPASSWORD", "")

    # If host already contains full connection details (starts with ep- for Neon), use it directly
    # Otherwise, construct the basic connection string
    if host.startswith("ep-") or "?" in host:
        # Full host with parameters provided
        return f"postgresql://{user}:{password}@{host}"
    else:
        # Simple host:port/database format
        return f"postgresql://{user}:{password}@{host}"


def setup_db(connection_string: str) -> None:
    """
    Initialize database by installing extensions and creating all required tables.

    This is idempotent - existing extensions/tables are not modified or recreated.

    Args:
        connection_string: Database connection string (postgresql:// or duckdb://).
    """
    engine = create_engine(connection_string, echo=True)

    if connection_string.startswith("postgresql://"):
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()

    # Create all tables
    SQLModel.metadata.create_all(engine)
