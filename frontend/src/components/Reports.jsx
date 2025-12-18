import { useEffect, useState } from 'react';
import axios from 'axios';

export default function Reports() {
  const [popularBooks, setPopularBooks] = useState([]);
  const [memberActivity, setMemberActivity] = useState([]);
  const [finesSummary, setFinesSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  const fetchReports = async () => {
    setLoading(true);
    setMessage('');
    try {
      const [popularRes, activityRes, finesRes] = await Promise.all([
        axios.get('/reports/popular-books'),
        axios.get('/reports/member-activity'),
        axios.get('/reports/fines-summary'),
      ]);
      setPopularBooks(popularRes.data);
      setMemberActivity(activityRes.data);
      setFinesSummary(finesRes.data);
    } catch (err) {
      setMessage('Ошибка загрузки отчётов: ' + (err.response?.data?.detail || 'сервер'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  return (
    <div>
      <h2>Отчёты</h2>
      <button onClick={fetchReports} style={{ padding: '6px 10px' }}>
        Обновить
      </button>

      {message && <p style={{ color: 'red', marginTop: '10px' }}>{message}</p>}

      {loading ? (
        <p>Загрузка...</p>
      ) : (
        <>
          <h3 style={{ marginTop: '16px' }}>Сводка по штрафам</h3>
          {finesSummary ? (
            <ul>
              <li>Всего начислено: {finesSummary.total_fines} руб</li>
              <li>Оплачено: {finesSummary.paid_fines} руб</li>
              <li>Неоплачено (кол-во): {finesSummary.unpaid_count}</li>
              <li>Неоплачено (сумма): {finesSummary.unpaid_total} руб</li>
            </ul>
          ) : (
            <p>Нет данных</p>
          )}

          <h3 style={{ marginTop: '24px' }}>Самые популярные книги</h3>
          {popularBooks.length === 0 ? (
            <p>Нет данных</p>
          ) : (
            <table border="1" cellPadding="8">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Название</th>
                  <th>ISBN</th>
                  <th>Кол-во выдач</th>
                </tr>
              </thead>
              <tbody>
                {popularBooks.map((b) => (
                  <tr key={b.id}>
                    <td>{b.id}</td>
                    <td>{b.title}</td>
                    <td>{b.isbn}</td>
                    <td>{b.num_loans}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h3 style={{ marginTop: '24px' }}>Активность читателей</h3>
          {memberActivity.length === 0 ? (
            <p>Нет данных</p>
          ) : (
            <table border="1" cellPadding="8">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Имя</th>
                  <th>Фамилия</th>
                  <th>Кол-во выдач</th>
                  <th>Просрочек</th>
                </tr>
              </thead>
              <tbody>
                {memberActivity.map((m) => (
                  <tr key={m.id}>
                    <td>{m.id}</td>
                    <td>{m.first_name}</td>
                    <td>{m.last_name}</td>
                    <td>{m.loans_count}</td>
                    <td>{m.overdue_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}

