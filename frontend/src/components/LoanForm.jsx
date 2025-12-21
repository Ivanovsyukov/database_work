import { useState, useEffect } from 'react';
import axios from 'axios';
import BookAutocomplete from './BookAutocomplete';
import MemberAutocomplete from './MemberAutocomplete'; 

export default function LoanForm() {
  const [selectedBookId, setSelectedBookId] = useState(null);
  const [availableCopies, setAvailableCopies] = useState([]);
  const [selectedCopyId, setSelectedCopyId] = useState(null);
  const [message, setMessage] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [selectedMemberId, setSelectedMemberId] = useState(null);

  // При монтировании компонента — установи дату по умолчанию (+14 дней)
  useEffect(() => {
    const today = new Date();
    const defaultDue = new Date(today);
    defaultDue.setDate(today.getDate() + 14);
    setDueDate(defaultDue.toISOString().split('T')[0]); // Формат YYYY-MM-DD
  }, []);
  // При выборе книги — загружаем доступные копии
  const handleBookSelect = async (bookId) => {
    setSelectedBookId(bookId);
    setSelectedCopyId(null);
    setAvailableCopies([]);
    if (!bookId) return;

    try {
      const res = await axios.get(`/copies?book_id=${bookId}&status=available`);
      setAvailableCopies(res.data);
    } catch (err) {
      console.error("Ошибка загрузки копий", err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedCopyId || !selectedMemberId) { // ← проверка по ID
      setMessage('Выберите копию и читателя');
      return;
    }

    try {
      await axios.post('/loans', {
        copy: selectedCopyId,
        member: selectedMemberId,
        due_date: dueDate,
      });
      setMessage('OK: Книга выдана');
      // Сброс формы
      setSelectedBookId(null);
      setSelectedCopyId(null);
      setAvailableCopies([]);
      setSelectedMemberId(null);
      // Обновляем дату по умолчанию для следующей выдачи
      const today = new Date();
      const defaultDue = new Date(today);
      defaultDue.setDate(today.getDate() + 14);
      setDueDate(defaultDue.toISOString().split('T')[0]);
    } catch (err) {
      setMessage('Ошибка: ' + (err.response?.data?.error || 'не удалось выдать'));
    }
  };

  return (
    <div>
      <h2>Оформить выдачу</h2>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '12px' }}>
          <label>Книга:</label>
          <BookAutocomplete
            value={selectedBookId}
            onChange={handleBookSelect}
            placeholder="Введите название книги..."
          />
        </div>

        {availableCopies.length > 0 && (
          <div style={{ marginBottom: '12px' }}>
            <label>Доступные копии:</label>
            <select
              value={selectedCopyId || ''}
              onChange={(e) => setSelectedCopyId(Number(e.target.value))}
              style={{ width: '100%', padding: '6px', marginTop: '4px' }}
              required
            >
              <option value="">Выберите копию</option>
              {availableCopies.map(copy => (
                <option key={copy.id} value={copy.id}>
                  Штрихкод: {copy.barcode}
                </option>
              ))}
            </select>
          </div>
        )}

        <div style={{ marginBottom: '12px' }}>
          <label>Читатель:</label>
          <MemberAutocomplete
            value={selectedMemberId}
            onChange={(memberId) => setSelectedMemberId(memberId)}
            placeholder="Введите ФИО читателя..."
          />
        </div>

        <div style={{ marginBottom: '12px' }}>
          <label>
            Дата возврата:
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              style={{ width: '100%', padding: '6px', marginTop: '4px' }}
              required
            />
          </label>
        </div>

        <button type="submit">Выдать книгу</button>
        {message && (
          <p style={{ marginTop: '10px', color: message.startsWith('OK:') ? 'green' : 'red' }}>
            {message}
          </p>
        )}
      </form>
    </div>
  );
}
