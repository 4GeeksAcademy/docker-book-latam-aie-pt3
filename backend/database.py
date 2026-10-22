from pathlib import Path
import os

from sqlmodel import SQLModel, create_engine, Session

# En local conserva backend/books.db; Docker Compose la cambia a /data/books.db.
BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'books.db'}")

# check_same_thread=False permite que FastAPI use la conexión desde múltiples hilos
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def init_db() -> None:
    """Crea todas las tablas si no existen."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependencia de inyección para obtener una sesión de BD por request."""
    with Session(engine) as session:
        yield session