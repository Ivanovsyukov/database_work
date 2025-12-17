// frontend/src/components/ReservationList.jsx
import { useState, useEffect } from 'react';
import axios from 'axios';

export default function ReservationList() {
  const [reservations, setReservations] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:8000/api/reservations/active/')
      .then(res => setReservations(res.data))
      .catch(err => console.error(err));
  }, []);

  const handleCancel = async (id) => {
    try {
      await axios.put(`http://localhost:8000/api/reservations/${id}/cancel/`);
      setReservations(reservations.filter(r => r.id !== id));
      alert('Бронирование отменено');
    } catch (err) {
      alert('Ошибка отмены');
    }
  };

  return (
    <div>
      <h2>Активные бронирования</h2>
      {reservations.length === 0 ? (
        <p>Нет активных бронирований</p>
      ) : (
        <ul>
          {reservations.map(r => (
            <li key={r.id}>
              Книга ID {r.book} — Читатель ID {r.member}
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