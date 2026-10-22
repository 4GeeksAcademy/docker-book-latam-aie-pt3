from sqlmodel import Session, select

from database import engine, init_db
from models import Book

# 10 libros clásicos variados (distintos géneros, épocas y autores)
SEED_BOOKS = [
    Book(
        title="Cien años de soledad",
        author="Gabriel García Márquez",
        year=1967,
        genre="Realismo mágico",
        cover_url="https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400&q=80",
        description="La saga de la familia Buendía en el mítico pueblo de Macondo, un hito de la literatura latinoamericana.",
    ),
    Book(
        title="Don Quijote de la Mancha",
        author="Miguel de Cervantes",
        year=1605,
        genre="Novela",
        cover_url="https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400&q=80",
        description="Las aventuras del ingenioso hidalgo y su fiel escudero Sancho Panza en busca de molinos y justicia.",
    ),
    Book(
        title="Orgullo y prejuicio",
        author="Jane Austen",
        year=1813,
        genre="Romance",
        cover_url="https://images.unsplash.com/photo-1474932430478-367dbb6832c1?w=400&q=80",
        description="Elizabeth Bennet y el señor Darcy navegan entre el orgullo, los prejuicios y el amor en la Inglaterra georgiana.",
    ),
    Book(
        title="1984",
        author="George Orwell",
        year=1949,
        genre="Distopía",
        cover_url="https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400&q=80",
        description="Winston Smith se rebela contra el Gran Hermano en un mundo de vigilancia total y control absoluto.",
    ),
    Book(
        title="Matar a un ruiseñor",
        author="Harper Lee",
        year=1960,
        genre="Drama",
        cover_url="https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=400&q=80",
        description="A través de los ojos de Scout Finch, el sur de Estados Unidos enfrenta racismo, justicia y compasión.",
    ),
    Book(
        title="El principito",
        author="Antoine de Saint-Exupéry",
        year=1943,
        genre="Fábula",
        cover_url="https://images.unsplash.com/photo-1519681393784-d120267933ba?w=400&q=80",
        description="Un pequeño príncipe viaja de planeta en planeta descubriendo lo esencial, que es invisible a los ojos.",
    ),
    Book(
        title="Frankenstein",
        author="Mary Shelley",
        year=1818,
        genre="Terror",
        cover_url="https://images.unsplash.com/photo-1506461883276-594a12b11cf3?w=400&q=80",
        description="El científico Victor Frankenstein da vida a una criatura que lo persigue en una historia gótica fundacional.",
    ),
    Book(
        title="Orgullo y prejuicio y zombis",
        author="Seth Grahame-Smith",
        year=2009,
        genre="Parodia",
        cover_url="https://images.unsplash.com/photo-1519682337058-a94d519337bc?w=400&q=80",
        description="Inspirado en Austen: Elizabeth Bennet ahora es una experta en artes marciales que lucha contra zombis.",
    ),
    Book(
        title="El nombre del viento",
        author="Patrick Rothfuss",
        year=2007,
        genre="Fantasía",
        cover_url="https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&q=80",
        description="Kvothe, leyenda y música, narra su vida desde la pobreza hasta el dominio de la magia y el nombre del viento.",
    ),
    Book(
        title="Fundación",
        author="Isaac Asimov",
        year=1951,
        genre="Ciencia ficción",
        cover_url="https://images.unsplash.com/photo-1518744386442-2d48ac47a7eb?w=400&q=80",
        description="Hari Seldon funda una institución oculta para acortar la caída del Imperio Galáctico mediante la psicohistoria.",
    ),
]


def run_seed() -> None:
    """Si la BD está vacía, inserta los 10 libros de ejemplo."""
    init_db()
    with Session(engine) as session:
        existing = session.exec(select(Book)).first()
        if existing is not None:
            print("📚 La base de datos ya tiene libros, no se realiza el seed.")
            return

        session.add_all(SEED_BOOKS)
        session.commit()
        print(f"🌱 Seed completado: {len(SEED_BOOKS)} libros insertados.")


if __name__ == "__main__":
    init_db()
    run_seed()