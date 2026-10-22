from typing import Optional

from sqlmodel import Field, SQLModel


class Book(SQLModel, table=True):
    """Modelo de tabla SQLite para un libro."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    author: str
    year: int
    genre: str = Field(default="")
    cover_url: str = Field(default="")
    description: str = Field(default="")


class BookPublic(SQLModel):
    """Esquema de respuesta (serializado) sin dependencia de BD."""

    id: int
    title: str
    author: str
    year: int
    genre: str = ""
    cover_url: str = ""
    description: str = ""