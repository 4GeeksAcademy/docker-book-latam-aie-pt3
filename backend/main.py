from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from database import get_session, init_db
from models import Book, BookPublic
from seed import run_seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa tablas y hace seed si la BD está vacía al arrancar."""
    init_db()
    run_seed()
    yield


app = FastAPI(
    title="📚 Mini App Biblioteca",
    description="API simple de una biblioteca de libros (FastAPI + SQLModel + SQLite).",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS abierto a todos los orígenes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["raiz"])
async def root():
    """Bienvenida y lista de endpoints disponibles."""
    return {
        "app": "📚 Mini App Biblioteca",
        "mensaje": "API de libros de ejemplo",
        "endpoints": {
            "GET /": "Información de la API",
            "GET /books": "Lista todos los libros",
            "GET /books/{id}": "Detalle de un libro por id",
        },
    }


@app.get("/books", response_model=List[BookPublic], tags=["libros"])
def list_books(session: Session = Depends(get_session)):
    """Devuelve todos los libros de la biblioteca."""
    books = session.exec(select(Book).order_by(Book.title)).all()
    return books


@app.get("/books/{book_id}", response_model=BookPublic, tags=["libros"])
def get_book(book_id: int, session: Session = Depends(get_session)):
    """Devuelve un libro por su id o error 404 si no existe."""
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return book