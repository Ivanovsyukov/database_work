// frontend/src/components/CopyManagement.jsx
import { useState } from 'react';
import axios from 'axios';
import BookAutocomplete from './BookAutocomplete';

export default function CopyManagement() {
  const [selectedBookId, setSelectedBookId] = useState(null);
  const [barcode, setBarcode] = useState('');
  const [message, setMessage] = useState('');

  const handleBookSelect = (bookId) => {
    setSelectedBookId(bookId);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedBookId || !barcode.trim()) {
      setMessage('Выберите книгу и введите штрихкод');
      return;
    }

    try {
      await axios.post('/copies', {
        book: selectedBookId,
        barcode: barcode,
      });
      setMessage('OK: Копия добавлена');
      setSelectedBookId(null);
      setBarcode('');
    } catch (err) {
      setMessage('Ошибка: ' + (err.response?.data?.barcode || 'сервер'));
    }
  };

  return (
    <div>
      <h2>Добавить копию книги</h2>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '12px' }}>
          <label>Книга:</label>
          <BookAutocomplete
            value={selectedBookId}
            onChange={handleBookSelect}
            placeholder="Введите название книги..."
          />
        </div>
        <div style={{ marginBottom: '12px' }}>
          <label>
            Штрихкод:
            <input
              type="text"
              value={barcode}
              onChange={(e) => setBarcode(e.target.value)}
              style={{ width: '100%', padding: '6px', marginTop: '4px' }}
              required
            />
          </label>
        </div>
        <button type="submit">Добавить копию</button>
        {message && (
          <p style={{ marginTop: '10px', color: message.startsWith('OK:') ? 'green' : 'red' }}>
            {message}
          </p>
        )}
      </form>
    </div>
  );
}
