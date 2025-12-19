// frontend/src/components/FineManagement.jsx
import { useState, useEffect } from 'react';
import axios from 'axios';

export default function FineManagement() {
  const [fines, setFines] = useState([]);
  const [memberId, setMemberId] = useState('');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [lastEndpoint, setLastEndpoint] = useState('/fines');

  const fetchFines = async (endpoint = '/fines') => {
    setLoading(true);
    setMessage('');
    setLastEndpoint(endpoint);
    try {
      const res = await axios.get(endpoint);
      setFines(res.data);
    } catch (err) {
      console.error(err);
      setMessage('Ошибка загрузки штрафов');
      setFines([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFines('/fines');
  }, []);

  const handleFilterByMember = () => {
    if (!memberId) {
      setMessage('Ошибка: укажите ID читателя');
      return;
    }
    fetchFines(`/fines/member/${memberId}`);
  };

  const handlePay = async (id) => {
    try {
      await axios.put(`/fines/${id}/pay`);
      setFines(fines.map(f => f.id === id ? { ...f, status: 'paid' } : f));
      alert('Штраф оплачен');
    } catch {
      alert('Ошибка оплаты');
    }
  };

  return (
    <div>
      <h2>Штрафы</h2>

      <div style={{ marginBottom: '12px' }}>
        <button onClick={() => fetchFines('/fines')} style={{ marginRight: '10px' }}>
          Показать все
        </button>
        <input
          type="number"
          placeholder="ID читателя"
          value={memberId}
          onChange={(e) => setMemberId(e.target.value)}
          style={{ marginRight: '10px' }}
        />
        <button onClick={handleFilterByMember}>Показать по читателю</button>
      </div>

      {message && (
        <p style={{ marginTop: '10px', color: message.startsWith('OK:') ? 'green' : 'red' }}>
          {message}
        </p>
      )}

      {loading ? (
        <p>Загрузка...</p>
      ) : fines.length === 0 ? (
        <p>Нет штрафов</p>
      ) : (
        <>
          <p style={{ color: '#666' }}>Источник: {lastEndpoint}</p>
          <table border="1" cellPadding="8">
            <thead>
              <tr>
                <th>ID</th>
                <th>Читатель</th>
                <th>Сумма</th>
                <th>Статус</th>
                <th>Действие</th>
              </tr>
            </thead>
            <tbody>
              {fines.map(f => (
                <tr key={f.id}>
                  <td>{f.id}</td>
                  <td>{f.member}</td>
                  <td>{f.fine_amount} руб</td>
                  <td>{f.status}</td>
                  <td>
                    {f.status === 'pending' && (
                      <button onClick={() => handlePay(f.id)}>Оплатить</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
