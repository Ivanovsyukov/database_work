import { useState, useEffect } from 'react';
import axios from 'axios';
import BookAutocomplete from './BookAutocomplete';
import MemberAutocomplete from './MemberAutocomplete';

export default function ReservationList() {
  const [reservations, setReservations] = useState([]);
  const [selectedBookId, setSelectedBookId] = useState(null);
  const [selectedMemberId, setSelectedMemberId] = useState(null);
  const [expiryDate, setExpiryDate] = useState(() => {
    const d = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
    return d.toISOString().slice(0, 10);
  });
  const [message, setMessage] = useState('');

  const fetchActiveReservations = async () => {
    try{
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
    return () => { cancelled = true; };
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setMessage('');

    if (!selectedBookId || !selectedMemberId || !expiryDate) {
      setMessage('Ошибка: заполните книгу, читателя и дату истечения');
      return;
    }

    try {
      await axios.post('/reservations', {
        book: selectedBookId,
        member: selectedMemberId,
        expiry_date: expiryDate,
      });
      setMessage('OK: Бронирование создано');
      setSelectedBookId(null);
      setSelectedMemberId(null);
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
          <label>Читатель:</label>
          <MemberAutocomplete
            value={selectedMemberId}
            onChange={(memberId) => setSelectedMemberId(memberId)}
            placeholder="Введите ФИО читателя..."
          />
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
      <button onClick={fetchActiveReservations} style={{ padding: '6px 10px', marginBottom: '10px' }}>
        Обновить
      </button>
      {reservations.length === 0 ? (
        <p>Нет активных бронирований</p>
      ) : (
        <table border="1" cellPadding="8" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Книга</th>
              <th>Читатель</th>
              <th>Дата истечения</th>
              <th>Действие</th>
            </tr>
          </thead>
          <tbody>
            {reservations.map(r => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.book_title}</td>
                <td>{r.member_last_name} {r.member_first_name}</td>
                <td>{r.expiry_date}</td>
                <td>
                  <button 
                    onClick={() => handleCancel(r.id)} 
                    style={{ 
                      padding: '4px 8px', 
                      background: '#dc3545', 
                      color: 'white', 
                      border: 'none', 
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Отменить
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
