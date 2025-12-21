import { useState, useEffect } from 'react';
import axios from 'axios';

import MemberAutocomplete from './MemberAutocomplete';

export default function FineManagement() {
  const [fines, setFines] = useState([]);
  const [selectedMemberId, setSelectedMemberId] = useState(null); 
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [lastEndpoint, setLastEndpoint] = useState('/fines');

  const fetchFines = async (endpoint = '/fines') => {
    setLoading(true);
    setMessage('');
    setLastEndpoint(endpoint);
    try {
      await axios.post('/fines/prepare/'); 
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
    if (!selectedMemberId) {
      setMessage('Выберите читателя');
      return;
    }
    fetchFines(`/fines/member/${selectedMemberId}`); 
  };

  const getFineStatus = (fine) => {
    return fine.paid_date ? 'paid' : 'pending';
  };

  const handlePay = async (id) => {
    try {
      await axios.put(`/fines/${id}/pay`);
      setFines(fines.map(f => 
        f.id === id ? { ...f, paid_date: new Date().toISOString().split('T')[0] } : f
      ));
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
        <MemberAutocomplete
          value={selectedMemberId}
          onChange={(memberId) => setSelectedMemberId(memberId)}
          placeholder="ФИО читателя..."
        />
        <button onClick={handleFilterByMember} style={{ marginLeft: '10px' }}>
          Показать по читателю
        </button>
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
                  <td>{f.loan?.member?.first_name} {f.loan?.member?.last_name}</td>
                  <td>{f.fine_amount} руб</td>
                  <td>{getFineStatus(f) === 'paid' ? 'Оплачен' : 'Не оплачен'}</td>
                  <td>{f.paid_date || '-'}</td>
                  <td>
                    {!f.paid_date && (
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
