// frontend/src/components/BookManagement.jsx
import { useState, useEffect } from 'react';
import axios from 'axios';
import PublisherAutocomplete from './PublisherAutocomplete';

export default function BookManagement() {
  const [bookData, setBookData] = useState({
    title: '',
    isbn: '',
    publication_year: new Date().getFullYear(),
    genre: '',
    publisher_id: null
  });
  const [message, setMessage] = useState('');

  const handlePublisherSelect = (pubId, pubName) => {
    setBookData({ ...bookData, publisher_id: pubId });
  };

  const handleAddNewPublisher = async (name) => {
    try {
      const res = await axios.post('http://localhost:8000/api/publishers/', { name });
      setBookData({ ...bookData, publisher_id: res.data.id });
      setMessage(`✅ Издательство "${name}" создано.`);
    } catch (err) {
      setMessage('❌ Ошибка создания издательства: ' + (err.response?.data?.name || 'сервер'));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!bookData.publisher_id) {
      setMessage('Выберите или создайте издательство');
      return;
    }
    try {
      await axios.post('http://localhost:8000/api/books/', bookData);
      setMessage('✅ Книга добавлена!');
      setBookData({
        title: '',
        isbn: '',
        publication_year: new Date().getFullYear(),
        genre: '',
        publisher_id: null
      });
    } catch (err) {
      setMessage('❌ Ошибка: ' + JSON.stringify(err.response?.data));
    }
  };

  return (
    <div>
      <h2>Добавить новую книгу</h2>
      <form onSubmit={handleSubmit}>
        <input
          placeholder="Название"
          value={bookData.title}
          onChange={(e) => setBookData({ ...bookData, title: e.target.value })}
          required
        />
        <input
          placeholder="ISBN (13 цифр)"
          value={bookData.isbn}
          onChange={(e) => setBookData({ ...bookData, isbn: e.target.value })}
          required
        />
        <input
          type="number"
          placeholder="Год издания"
          value={bookData.publication_year}
          onChange={(e) => setBookData({ ...bookData, publication_year: parseInt(e.target.value) })}
          required
        />
        <input
          placeholder="Жанр"
          value={bookData.genre}
          onChange={(e) => setBookData({ ...bookData, genre: e.target.value })}
        />

        <div style={{ margin: '10px 0' }}>
          <label>Издательство:</label>
          <PublisherAutocomplete
            value={bookData.publisher_id}
            onChange={handlePublisherSelect}
            onNewPublisher={handleAddNewPublisher}
          />
        </div>

        <button type="submit">Добавить книгу</button>
        {message && (
          <p style={{ marginTop: '10px', color: message.startsWith('✅') ? 'green' : 'red' }}>
            {message}
          </p>
        )}
      </form>
    </div>
  );
}