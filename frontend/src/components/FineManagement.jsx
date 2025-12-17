// frontend/src/components/FineManagement.jsx
import { useState, useEffect } from 'react';
import axios from 'axios';

export default function FineManagement() {
  const [fines, setFines] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:8000/api/fines')
      .then(res => setFines(res.data))
      .catch(err => console.error(err));
  }, []);

  const handlePay = async (id) => {
    try {
      await axios.put(`http://localhost:8000/api/fines/${id}/pay`);
      setFines(fines.map(f => f.id === id ? { ...f, status: 'paid' } : f));
      alert('Штраф оплачен');
    } catch (err) {
      alert('Ошибка оплаты');
    }
  };

  return (
    <div>
      <h2>Штрафы</h2>
      {fines.length === 0 ? (
        <p>Нет штрафов</p>
      ) : (
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
      )}
    </div>
  );
}