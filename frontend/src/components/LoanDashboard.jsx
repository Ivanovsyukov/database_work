import { useEffect, useState } from 'react';
import axios from 'axios';

export default function LoanDashboard() {
  const [activeLoans, setActiveLoans] = useState([]);
  const [overdueLoans, setOverdueLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [returningId, setReturningId] = useState(null);

  const fetchLoans = async () => {
    setLoading(true);
    setMessage('');
    try {
      const [activeRes, overdueRes] = await Promise.all([
        axios.get('/loans/active'),
        axios.get('/loans/overdue'),
      ]);
      setActiveLoans(activeRes.data);
      setOverdueLoans(overdueRes.data);
    } catch (err) {
      setMessage('Ошибка загрузки выдач: ' + (err.response?.data?.detail || 'сервер'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLoans();
  }, []);

  const handleReturn = async (loanId) => {
    setMessage('');
    setReturningId(loanId);
    try {
      await axios.put(`/loans/${loanId}/return`);
      setMessage('OK: Книга возвращена');
      fetchLoans();
    } catch (err) {
      setMessage('Ошибка: ' + (err.response?.data?.error || 'не удалось вернуть'));
    } finally {
      setReturningId(null);
    }
  };

  const renderLoansTable = (loans) => (
    <table border="1" cellPadding="8" style={{ marginTop: '10px', width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr>
          <th>ID</th>
          <th>Книга</th>
          <th>Читатель</th>
          <th>Дата выдачи</th>
          <th>Срок возврата</th>
          <th>Статус</th>
          <th>Действие</th>
        </tr>
      </thead>
      <tbody>
        {loans.map((l) => (
          <tr key={l.id}>
            <td>{l.id}</td>
            <td>{l.book_title}</td>
            <td>{l.member_last_name} {l.member_first_name}</td>
            <td>{l.loan_date}</td>
            <td>{l.due_date}</td>
            <td>{l.status}</td>
            <td>
              {l.status !== 'returned' && (
                <button
                  onClick={() => handleReturn(l.id)}
                  disabled={returningId === l.id}
                  style={{ padding: '4px 8px', background: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}
                >
                  {returningId === l.id ? '...' : 'Вернуть'}
                </button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  return (
    <div>
      <h2>Выдачи</h2>
      <button onClick={fetchLoans} style={{ padding: '6px 10px', marginBottom: '10px' }}>
        Обновить
      </button>

      {message && (
        <p style={{ marginTop: '10px', color: message.startsWith('OK:') ? 'green' : 'red' }}>
          {message}
        </p>
      )}

      {loading ? (
        <p>Загрузка...</p>
      ) : (
        <>
          <h3 style={{ marginTop: '16px' }}>Активные</h3>
          {activeLoans.length === 0 ? <p>Нет активных выдач</p> : renderLoansTable(activeLoans)}

          <h3 style={{ marginTop: '24px' }}>Просроченные</h3>
          {overdueLoans.length === 0 ? <p>Нет просроченных выдач</p> : renderLoansTable(overdueLoans)}
        </>
      )}
    </div>
  );
}
