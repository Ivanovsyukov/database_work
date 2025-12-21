import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';

const initialFilters = Object.freeze({
  title: '',
  author: '',
  genre: '',
  year: '',
});

export default function BookList() {
  const [books, setBooks] = useState([]);
  const [authors, setAuthors] = useState([]);
  const [filters, setFilters] = useState(initialFilters);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  const fetchBooks = useCallback(async (nextFilters) => {
    setLoading(true);
    setMessage('');
    try {
      const params = {};
      if (nextFilters.title.trim()) params.title = nextFilters.title.trim();
      if (nextFilters.author) params.author = nextFilters.author;
      if (nextFilters.genre.trim()) params.genre = nextFilters.genre.trim();
      if (nextFilters.year.trim()) params.year = nextFilters.year.trim();

      const res = await axios.get('/books', { params });
      setBooks(res.data);
    } catch (err) {
      console.error('Ошибка загрузки книг:', err);
      setMessage('Ошибка загрузки книг');
      setBooks([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAuthors = useCallback(async () => {
    try {
      const res = await axios.get('/authors');
      setAuthors(res.data);
    } catch (err) {
      console.error('Ошибка загрузки авторов:', err);
    }
  }, []);

  useEffect(() => {
    fetchAuthors();
    fetchBooks(initialFilters);
  }, [fetchAuthors, fetchBooks]);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  const applyFilters = (e) => {
    e.preventDefault();
    fetchBooks(filters);
  };

  const resetFilters = () => {
    setFilters(initialFilters);
    fetchBooks(initialFilters);
  };

  if (loading) return <p>Загрузка...</p>;

  return (
    <div>
      <h2>Каталог книг</h2>

      <form onSubmit={applyFilters} style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <input
            name="title"
            placeholder="Название"
            value={filters.title}
            onChange={handleFilterChange}
          />
          <select name="author" value={filters.author} onChange={handleFilterChange}>
            <option value="">Автор (любой)</option>
            {authors.map((a) => (
              <option key={a.id} value={a.id}>
                {a.last_name} {a.first_name}
              </option>
            ))}
          </select>
          <input
            name="genre"
            placeholder="Жанр"
            value={filters.genre}
            onChange={handleFilterChange}
          />
          <input
            name="year"
            placeholder="Год"
            value={filters.year}
            onChange={handleFilterChange}
          />
          <button type="submit">Поиск</button>
          <button type="button" onClick={resetFilters}>
            Сброс
          </button>
        </div>
      </form>

      {message && <p style={{ color: 'red' }}>{message}</p>}

      {books.length === 0 ? (
        <p>Нет книг</p>
      ) : (
        <table border="1" cellPadding="8" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th>Название</th>
              <th>ISBN</th>
              <th>Год</th>
              <th>Жанр</th>
              <th>Издательство</th>
              <th>Копии (всего)</th>
              <th>Доступно</th>
            </tr>
          </thead>
          <tbody>
            {books.map(book => (
              <tr key={book.id}>
                <td><strong>{book.title}</strong></td>
                <td>{book.isbn}</td>
                <td>{book.publication_year}</td>
                <td>{book.genre || '-'}</td>
                <td>{book.publisher?.name || '-'}</td>
                <td>{book.total_copies}</td>  {/* ← новое поле */}
                <td>{book.available_copies}</td> {/* ← новое поле */}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
