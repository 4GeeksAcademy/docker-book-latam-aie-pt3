import type { Book } from "../types";

const PLACEHOLDER = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300' viewBox='0 0 100 100'%3E%3Crect fill='%23334155' width='100' height='100'/%3E%3Ctext x='50' y='60' text-anchor='middle' fill='%2394a3b8' font-size='40'%3E📖%3C/text%3E%3C/svg%3E";

interface BookCardProps {
  book: Book;
}

export default function BookCard({ book }: BookCardProps) {
  return (
    <article className="group bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl hover:border-indigo-500/40 transition-all duration-300 hover:-translate-y-1 flex flex-col">
      {/* Imagen */}
      <div className="aspect-[4/3] overflow-hidden bg-slate-700">
        <img
          src={book.cover_url || PLACEHOLDER}
          alt={`Portada de ${book.title}`}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
          onError={(e) => {
            (e.currentTarget as HTMLImageElement).src = PLACEHOLDER;
          }}
        />
      </div>

      {/* Contenido */}
      <div className="p-5 flex flex-col gap-2 flex-1">
        <h2 className="text-lg font-bold text-white leading-tight line-clamp-2">
          {book.title}
        </h2>

        <p className="text-sm text-slate-400">
          <span className="text-indigo-400 font-medium">{book.author}</span>
          {" · "}
          <span>{book.year}</span>
        </p>

        {book.genre && (
          <span className="self-start text-xs font-medium text-emerald-300 bg-emerald-900/40 px-2.5 py-0.5 rounded-full border border-emerald-700/40">
            {book.genre}
          </span>
        )}

        <p className="mt-1 text-sm text-slate-400 leading-relaxed line-clamp-3 flex-1">
          {book.description}
        </p>
      </div>
    </article>
  );
}