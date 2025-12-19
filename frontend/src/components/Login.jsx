import { useState } from 'react';
import axios from 'axios';

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const normalizedEmail = email.trim().toLowerCase();
      const res = await axios.post('/auth/login', { email: normalizedEmail });
      localStorage.setItem('staff', JSON.stringify(res.data));
      onLogin(res.data);
    } catch (err) {
      const serverError = err.response?.data?.error;
      if (serverError) {
        alert('Ошибка входа: ' + serverError);
        return;
      }
      alert('Не удалось подключиться к бэкенду (проверь `python manage.py runserver`)');
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '400px', margin: '50px auto' }}>
      <h2>Вход для сотрудников</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Ваш email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{ width: '100%', padding: '8px', margin: '10px 0' }}
        />
        <button type="submit" style={{ width: '100%', padding: '10px' }}>
          Войти
        </button>
      </form>
    </div>
  );
}
