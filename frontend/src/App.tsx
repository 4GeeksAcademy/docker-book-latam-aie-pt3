import { useBooks } from "./hooks/useBooks";
import BookCard from "./components/BookCard";

function Spinner() {
  return (
    <div className="flex flex-col items-center justify-center py-24 gap-6">
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 border-4 border-slate-700 rounded-full" />
        <div className="absolute inset-0 border-4 border-transparent border-t-indigo-500 rounded-full animate-spin" />
      </div>
      <p className="text-slate-400 text-lg animate-pulse">
        Cargando libros...
      </p>
    </div>
  );
}

function ErrorCard({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="max-w-md mx-auto mt-16 p-8 bg-red-900/20 border border-red-800/40 rounded-2xl text-center">
      <div className="text-5xl mb-4">⚠️</div>
      <h2 className="text-xl font-bold text-red-300 mb-2">
        Error al cargar
      </h2>
      <p className="text-red-400/80 mb-6 text-sm">{message}</p>
      <button
        onClick={onRetry}
        className="px-6 py-2.5 bg-red-700 hover:bg-red-600 text-white font-medium rounded-xl transition-colors duration-200 cursor-pointer"
      >
        Intentar de nuevo
      </button>
    </div>
  );
}

export default function App() {
  const { books, loading, error, retry } = useBooks();

  return (
    <div className="min-h-svh flex flex-col bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950">
      {/* Header */}
      <header className="bg-gradient-to-r from-indigo-900/80 via-purple-900/80 to-slate-900/80 backdrop-blur-md border-b border-slate-700/50 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex items-center gap-3">
          <span className="text-3xl">📚</span>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Mini Biblioteca
            </h1>
            <p className="text-xs text-slate-400">
              {loading
                ? "Cargando…"
                : `${books.length} libro${books.length !== 1 ? "s" : ""} disponible${books.length !== 1 ? "s" : ""}`}
            </p>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {loading && <Spinner />}

        {error && <ErrorCard message={error} onRetry={retry} />}

        {!loading && !error && books.length === 0 && (
          <div className="text-center py-24">
            <p className="text-slate-500 text-lg">
              No hay libros disponibles en este momento.
            </p>
          </div>
        )}

        {!loading && !error && books.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {books.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-6 text-center">
        <p className="text-sm text-slate-600">
          📚 Mini Biblioteca · FastAPI + React ·{" "}
          {new Date().getFullYear()}
        </p>
      </footer>
    </div>
  );
}