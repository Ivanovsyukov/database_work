import { useEffect, useState } from 'react';
import axios from 'axios';

export default function BookList() {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('http://localhost:8000/api/books')
      .then(res => {
        setBooks(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Ошибка загрузки книг:', err);
        setLoading(false);
      });
  }, []);

  if (loading) return <p>Загрузка...</p>;

  return (
    <div>
      <h2>Каталог книг</h2>
      {books.length === 0 ? (
        <p>Нет книг</p>
      ) : (
        <ul>
          {books.map(book => (
            <li key={book.id}>
              <strong>{book.title}</strong> ({book.isbn}) — {book.publication_year}
              {book.genre && ` — ${book.genre}`}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}