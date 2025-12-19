import { useEffect, useState } from 'react';
import axios from 'axios';

export default function AuthorManagement() {
  const [authors, setAuthors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    birth_date: '',
    bio: '',
  });

  const fetchAuthors = async () => {
    setLoading(true);
    setMessage('');
    try {
      const res = await axios.get('/authors');
      setAuthors(res.data);
    } catch (err) {
      setMessage('Ошибка загрузки авторов: ' + (err.response?.data?.detail || 'сервер'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuthors();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');

    const payload = {
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      birth_date: form.birth_date || null,
      bio: form.bio.trim() || null,
    };

    try {
      await axios.post('/authors', payload);
      setForm({ first_name: '', last_name: '', birth_date: '', bio: '' });
      setMessage('OK: Автор добавлен');
      fetchAuthors();
    } catch (err) {
      setMessage('Ошибка: ' + JSON.stringify(err.response?.data || err.message));
    }
  };

  return (
    <div>
      <h2>Авторы</h2>

      <form onSubmit={handleSubmit} style={{ maxWidth: '520px' }}>
        <h3>Добавить автора</h3>
        <input
          name="first_name"
          placeholder="Имя"
          value={form.first_name}
          onChange={handleChange}
          required
          style={{ width: '100%', padding: '8px', margin: '6px 0' }}
        />
        <input
          name="last_name"
          placeholder="Фамилия"
          value={form.last_name}
          onChange={handleChange}
          required
          style={{ width: '100%', padding: '8px', margin: '6px 0' }}
        />
        <input
          type="date"
          name="birth_date"
          value={form.birth_date}
          onChange={handleChange}
          style={{ width: '100%', padding: '8px', margin: '6px 0' }}
        />
        <textarea
          name="bio"
          placeholder="Биография (необязательно)"
          value={form.bio}
          onChange={handleChange}
          rows={3}
          style={{ width: '100%', padding: '8px', margin: '6px 0' }}
        />
        <button type="submit" style={{ padding: '8px 14px' }}>
          Добавить
        </button>
        {message && (
          <p style={{ marginTop: '10px', color: message.startsWith('OK:') ? 'green' : 'red' }}>
            {message}
          </p>
        )}
      </form>

      <hr style={{ margin: '20px 0' }} />

      <div>
        <h3>Список авторов</h3>
        <button onClick={fetchAuthors} style={{ padding: '6px 10px' }}>
          Обновить
        </button>
        {loading ? (
          <p>Загрузка...</p>
        ) : authors.length === 0 ? (
          <p>Нет авторов</p>
        ) : (
          <table border="1" cellPadding="8" style={{ marginTop: '10px' }}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Имя</th>
                <th>Фамилия</th>
                <th>Дата рождения</th>
              </tr>
            </thead>
            <tbody>
              {authors.map((a) => (
                <tr key={a.id}>
                  <td>{a.id}</td>
                  <td>{a.first_name}</td>
                  <td>{a.last_name}</td>
                  <td>{a.birth_date || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

