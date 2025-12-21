import { useState, useEffect } from 'react';
import axios from 'axios';
import BookAutocomplete from './BookAutocomplete';

export default function ReservationList() {
  const [reservations, setReservations] = useState([]);
  const [selectedBookId, setSelectedBookId] = useState(null);
  const [memberId, setMemberId] = useState('');
  const [expiryDate, setExpiryDate] = useState(() => {
    const d = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
    return d.toISOString().slice(0, 10);
  });
  const [message, setMessage] = useState('');

  const fetchActiveReservations = async () => {
    try {
      const res = await axios.get('/reservations/active');
      setReservations(res.data);
    } catch (err) {
      console.error(err);
      setMessage('Ошибка загрузки бронирований');
    }
  };

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const res = await axios.get('/reservations/active');
        if (!cancelled) setReservations(res.data);
      } catch (err) {
        console.error(err);
        if (!cancelled) setMessage('Ошибка загрузки бронирований');
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setMessage('');

    if (!selectedBookId || !memberId || !expiryDate) {
      setMessage('Ошибка: заполните книгу, читателя и дату истечения');
      return;
    }

    try {
      await axios.post('/reservations', {
        book: selectedBookId,
        member: Number(memberId),
        expiry_date: expiryDate,
      });
      setMessage('OK: Бронирование создано');
      setSelectedBookId(null);
      setMemberId('');
      fetchActiveReservations();
    } catch (err) {
      setMessage('Ошибка: ' + JSON.stringify(err.response?.data || err.message));
    }
  };

  const handleCancel = async (id) => {
    try {
      await axios.put(`/reservations/${id}/cancel`);
      setReservations(reservations.filter(r => r.id !== id));
      alert('Бронирование отменено');
    } catch {
      alert('Ошибка отмены');
    }
  };

  return (
    <div>
      <h2>Бронирования</h2>

      <form onSubmit={handleCreate} style={{ maxWidth: '520px', marginBottom: '20px' }}>
        <h3>Создать бронирование</h3>

        <div style={{ marginBottom: '12px' }}>
          <label>Книга:</label>
          <BookAutocomplete
            value={selectedBookId}
            onChange={(bookId) => setSelectedBookId(bookId)}
            placeholder="Введите название книги..."
          />
        </div>

        <div style={{ marginBottom: '12px' }}>
          <label>
            ID читателя:
            <input
              type="number"
              value={memberId}
              onChange={(e) => setMemberId(e.target.value)}
              style={{ width: '100%', padding: '6px', marginTop: '4px' }}
              required
            />
          </label>
        </div>

        <div style={{ marginBottom: '12px' }}>
          <label>
            Дата истечения:
            <input
              type="date"
              value={expiryDate}
              onChange={(e) => setExpiryDate(e.target.value)}
              style={{ width: '100%', padding: '6px', marginTop: '4px' }}
              required
            />
          </label>
        </div>

        <button type="submit">Создать</button>
        {message && (
          <p style={{ marginTop: '10px', color: message.startsWith('OK:') ? 'green' : 'red' }}>
            {message}
          </p>
        )}
      </form>

      <h3>Активные бронирования</h3>
      <button onClick={fetchActiveReservations} style={{ padding: '6px 10px' }}>
        Обновить
      </button>
      {reservations.length === 0 ? (
        <p>Нет активных бронирований</p>
      ) : (
        <ul>
          {reservations.map(r => (
            <li key={r.id}>
              #{r.id}: Книга ID {r.book} - Читатель ID {r.member} (до {r.expiry_date})
              <button onClick={() => handleCancel(r.id)} style={{ marginLeft: '10px', color: 'red' }}>
                Отменить
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
