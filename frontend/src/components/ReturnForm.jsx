import { useState } from 'react';
import axios from 'axios';

export default function ReturnForm() {
  const [loanId, setLoanId] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`/loans/${loanId}/return`);
      alert('Книга успешно возвращена!');
      setLoanId('');
    } catch (err) {
      alert('Ошибка: ' + (err.response?.data?.error || 'не удалось вернуть книгу'));
    }
  };

  return (
    <div>
      <h2>Вернуть книгу</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="number"
          placeholder="ID выдачи"
          value={loanId}
          onChange={(e) => setLoanId(e.target.value)}
          required
        />
        <button type="submit">Вернуть</button>
      </form>
    </div>
  );
}
