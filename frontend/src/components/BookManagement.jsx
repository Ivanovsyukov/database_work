// frontend/src/components/BookManagement.jsx
import { useState } from 'react';
import axios from 'axios';
import PublisherAutocomplete from './PublisherAutocomplete';
import BookAutocomplete from './BookAutocomplete';

export default function BookManagement() {
  const [newBookData, setNewBookData] = useState({
    title: '',
    isbn: '',
    publication_year: new Date().getFullYear(),
    genre: '',
    publisher_id: null,
  });
  const [message, setMessage] = useState('');

  const [editBookId, setEditBookId] = useState(null);
  const [editBookData, setEditBookData] = useState(null);
  const [editMessage, setEditMessage] = useState('');

  const handleNewPublisherSelect = (pubId) => {
    setNewBookData((prev) => ({ ...prev, publisher_id: pubId }));
  };

  const createPublisher = async (name) => {
    const res = await axios.post('/publishers', { name });
    return res.data;
  };

  const handleAddNewPublisherForCreate = async (name) => {
    try {
      const pub = await createPublisher(name);
      setNewBookData((prev) => ({ ...prev, publisher_id: pub.id }));
      setMessage(`OK: Издательство "${name}" создано`);
    } catch (err) {
      setMessage('Ошибка создания издательства: ' + (err.response?.data?.name || 'сервер'));
    }
  };

  const handleCreateBook = async (e) => {
    e.preventDefault();
    if (!newBookData.publisher_id) {
      setMessage('Выберите или создайте издательство');
      return;
    }
    try {
      await axios.post('/books', newBookData);
      setMessage('OK: Книга добавлена');
      setNewBookData({
        title: '',
        isbn: '',
        publication_year: new Date().getFullYear(),
        genre: '',
        publisher_id: null,
      });
    } catch (err) {
      setMessage('Ошибка: ' + JSON.stringify(err.response?.data));
    }
  };

  const handleEditSelect = async (bookId) => {
    setEditBookId(bookId || null);
    setEditMessage('');

    if (!bookId) {
      setEditBookData(null);
      return;
    }

    try {
      const res = await axios.get(`/books/${bookId}`);
      const b = res.data;
      setEditBookData({
        title: b.title || '',
        isbn: b.isbn || '',
        publication_year: b.publication_year || new Date().getFullYear(),
        genre: b.genre || '',
        publisher_id: b.publisher?.id || null,
        publisher_name: b.publisher?.name || '',
      });
    } catch (err) {
      console.error(err);
      setEditMessage('Ошибка: не удалось загрузить книгу');
      setEditBookData(null);
    }
  };

  const handleEditPublisherSelect = (pubId, pubName) => {
    setEditBookData((prev) => ({
      ...prev,
      publisher_id: pubId,
      publisher_name: pubName,
    }));
  };

  const handleAddNewPublisherForEdit = async (name) => {
    try {
      const pub = await createPublisher(name);
      setEditBookData((prev) => ({ ...prev, publisher_id: pub.id, publisher_name: pub.name }));
      setEditMessage(`OK: Издательство "${name}" создано`);
    } catch (err) {
      setEditMessage('Ошибка создания издательства: ' + (err.response?.data?.name || 'сервер'));
    }
  };

  const handleUpdateBook = async (e) => {
    e.preventDefault();
    if (!editBookId || !editBookData) return;

    setEditMessage('');

    if (!editBookData.publisher_id) {
      setEditMessage('Ошибка: выберите или создайте издательство');
      return;
    }

    try {
      await axios.put(`/books/${editBookId}`, {
        title: editBookData.title,
        isbn: editBookData.isbn,
        publication_year: editBookData.publication_year,
        genre: editBookData.genre,
        publisher_id: editBookData.publisher_id,
      });
      setEditMessage('OK: Книга обновлена');
    } catch (err) {
      setEditMessage('Ошибка: ' + JSON.stringify(err.response?.data || err.message));
    }
  };

  return (
    <div>
      <h2>Добавить новую книгу</h2>
      <form onSubmit={handleCreateBook} style={{ maxWidth: '520px' }}>
        <input
          placeholder="Название"
          value={newBookData.title}
          onChange={(e) => setNewBookData((prev) => ({ ...prev, title: e.target.value }))}
          required
          style={{ width: '100%', padding: '8px', margin: '6px 0' }}
        />
        <input
          placeholder="ISBN (13 цифр)"
          value={newBookData.isbn}
          onChange={(e) => setNewBookData((prev) => ({ ...prev, isbn: e.target.value }))}
          required
          style={{ width: '100%', padding: '8px', margin: '6px 0' }}
        />
        <input
          type="number"
          placeholder="Год издания"
          value={newBookData.publication_year}
          onChange={(e) =>
            setNewBookData((prev) => ({ ...prev, publication_year: Number(e.target.value) }))
          }
          required
          style={{ width: '100%', padding: '8px', margin: '6px 0' }}
        />
        <input
          placeholder="Жанр"
          value={newBookData.genre}
          onChange={(e) => setNewBookData((prev) => ({ ...prev, genre: e.target.value }))}
          style={{ width: '100%', padding: '8px', margin: '6px 0' }}
        />

        <div style={{ margin: '10px 0' }}>
          <label>Издательство:</label>
          <PublisherAutocomplete
            value={newBookData.publisher_id}
            onChange={handleNewPublisherSelect}
            onNewPublisher={handleAddNewPublisherForCreate}
          />
        </div>

        <button type="submit">Добавить книгу</button>
        {message && (
          <p style={{ marginTop: '10px', color: message.startsWith('OK:') ? 'green' : 'red' }}>
            {message}
          </p>
        )}
      </form>

      <hr style={{ margin: '20px 0' }} />

      <h2>Редактировать книгу</h2>
      <div style={{ marginBottom: '12px', maxWidth: '520px' }}>
        <label>Книга:</label>
        <BookAutocomplete
          value={editBookId}
          onChange={handleEditSelect}
          placeholder="Введите название книги..."
        />
      </div>

      {editBookData && (
        <form onSubmit={handleUpdateBook} style={{ maxWidth: '520px' }}>
          <input
            placeholder="Название"
            value={editBookData.title}
            onChange={(e) => setEditBookData((prev) => ({ ...prev, title: e.target.value }))}
            required
            style={{ width: '100%', padding: '8px', margin: '6px 0' }}
          />
          <input
            placeholder="ISBN (13 цифр)"
            value={editBookData.isbn}
            onChange={(e) => setEditBookData((prev) => ({ ...prev, isbn: e.target.value }))}
            required
            style={{ width: '100%', padding: '8px', margin: '6px 0' }}
          />
          <input
            type="number"
            placeholder="Год издания"
            value={editBookData.publication_year}
            onChange={(e) =>
              setEditBookData((prev) => ({ ...prev, publication_year: Number(e.target.value) }))
            }
            required
            style={{ width: '100%', padding: '8px', margin: '6px 0' }}
          />
          <input
            placeholder="Жанр"
            value={editBookData.genre}
            onChange={(e) => setEditBookData((prev) => ({ ...prev, genre: e.target.value }))}
            style={{ width: '100%', padding: '8px', margin: '6px 0' }}
          />

          <div style={{ margin: '10px 0' }}>
            <label>Издательство:</label>
            <PublisherAutocomplete
              value={editBookData.publisher_id}
              selectedName={editBookData.publisher_name}
              onChange={handleEditPublisherSelect}
              onNewPublisher={handleAddNewPublisherForEdit}
            />
          </div>

          <button type="submit">Сохранить изменения</button>
          {editMessage && (
            <p style={{ marginTop: '10px', color: editMessage.startsWith('OK:') ? 'green' : 'red' }}>
              {editMessage}
            </p>
          )}
        </form>
      )}

      {!editBookData && editMessage && (
        <p style={{ marginTop: '10px', color: editMessage.startsWith('OK:') ? 'green' : 'red' }}>
          {editMessage}
        </p>
      )}
    </div>
  );
}

