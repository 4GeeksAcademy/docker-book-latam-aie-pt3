import { useState, useEffect, useCallback } from "react";
import type { Book } from "../types";

interface UseBooksResult {
  books: Book[];
  loading: boolean;
  error: string | null;
  retry: () => void;
}

export function useBooks(): UseBooksResult {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBooks = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/books");

      if (!res.ok) {
        if (res.status === 404) throw new Error("Recurso no encontrado (404)");
        if (res.status >= 500)
          throw new Error(`Error interno del servidor (${res.status})`);
        throw new Error(`Error HTTP ${res.status}`);
      }

      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error("Formato de respuesta inválido");
      }

      const data: unknown = await res.json();

      if (!Array.isArray(data)) {
        throw new Error("Formato de datos inesperado");
      }

      setBooks(data as Book[]);
    } catch (err) {
      const message =
        err instanceof TypeError && err.message === "Failed to fetch"
          ? "No se pudo conectar al servidor. Verifica que el backend esté corriendo."
          : err instanceof Error
            ? err.message
            : "Ocurrió un error inesperado";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBooks();
  }, [fetchBooks]);

  return { books, loading, error, retry: fetchBooks };
}