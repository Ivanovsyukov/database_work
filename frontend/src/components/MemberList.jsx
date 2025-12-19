import { useEffect, useState } from 'react';
import axios from 'axios';

export default function MemberList({ canManage = false }) {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingMemberId, setEditingMemberId] = useState(null);
  const [editForm, setEditForm] = useState(null);
  const [message, setMessage] = useState('');

  const fetchMembers = async () => {
    setLoading(true);
    setMessage('');
    try {
      const res = await axios.get('/members');
      setMembers(res.data);
    } catch (err) {
      setMessage('Ошибка загрузки читателей: ' + (err.response?.data?.detail || 'сервер'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMembers();
  }, []);

  const startEdit = (member) => {
    setEditingMemberId(member.id);
    setEditForm({
      first_name: member.first_name || '',
      last_name: member.last_name || '',
      email: member.email || '',
      phone: member.phone || '',
      address: member.address || '',
      membership_start_date: member.membership_start_date || '',
      membership_status: member.membership_status || 'active',
    });
    setMessage('');
  };

  const cancelEdit = () => {
    setEditingMemberId(null);
    setEditForm(null);
    setMessage('');
  };

  const handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditForm((prev) => ({ ...prev, [name]: value }));
  };

  const saveEdit = async (e) => {
    e.preventDefault();
    if (!editingMemberId || !editForm) return;

    setMessage('');
    try {
      const res = await axios.put(`/members/${editingMemberId}`, {
        first_name: editForm.first_name,
        last_name: editForm.last_name,
        email: editForm.email,
        phone: editForm.phone || null,
        address: editForm.address || null,
        membership_start_date: editForm.membership_start_date,
        membership_status: editForm.membership_status,
      });

      setMembers((prev) => prev.map((m) => (m.id === editingMemberId ? res.data : m)));
      setMessage('OK: Данные читателя обновлены');
      setEditingMemberId(null);
      setEditForm(null);
    } catch (err) {
      setMessage('Ошибка: ' + JSON.stringify(err.response?.data || err.message));
    }
  };

  if (loading) return <p>Загрузка...</p>;

  return (
    <div>
      <h2>Читатели</h2>

      <button onClick={fetchMembers} style={{ padding: '6px 10px' }}>
        Обновить
      </button>

      {message && (
        <p style={{ marginTop: '10px', color: message.startsWith('OK:') ? 'green' : 'red' }}>
          {message}
        </p>
      )}

      {canManage && editingMemberId && editForm && (
        <form onSubmit={saveEdit} style={{ marginTop: '16px', maxWidth: '520px' }}>
          <h3>Редактирование читателя (ID {editingMemberId})</h3>
          <input
            name="first_name"
            placeholder="Имя"
            value={editForm.first_name}
            onChange={handleEditChange}
            required
            style={{ width: '100%', padding: '8px', margin: '6px 0' }}
          />
          <input
            name="last_name"
            placeholder="Фамилия"
            value={editForm.last_name}
            onChange={handleEditChange}
            required
            style={{ width: '100%', padding: '8px', margin: '6px 0' }}
          />
          <input
            name="email"
            type="email"
            placeholder="Email"
            value={editForm.email}
            onChange={handleEditChange}
            required
            style={{ width: '100%', padding: '8px', margin: '6px 0' }}
          />
          <input
            name="phone"
            placeholder="Телефон"
            value={editForm.phone}
            onChange={handleEditChange}
            style={{ width: '100%', padding: '8px', margin: '6px 0' }}
          />
          <textarea
            name="address"
            placeholder="Адрес"
            value={editForm.address}
            onChange={handleEditChange}
            rows={2}
            style={{ width: '100%', padding: '8px', margin: '6px 0' }}
          />
          <div style={{ margin: '6px 0' }}>
            <label>
              Дата регистрации:
              <input
                type="date"
                name="membership_start_date"
                value={editForm.membership_start_date}
                onChange={handleEditChange}
                style={{ marginLeft: '8px' }}
                required
              />
            </label>
          </div>
          <div style={{ margin: '6px 0' }}>
            <label>
              Статус:
              <select
                name="membership_status"
                value={editForm.membership_status}
                onChange={handleEditChange}
                style={{ marginLeft: '8px' }}
              >
                <option value="active">active</option>
                <option value="suspended">suspended</option>
                <option value="expired">expired</option>
              </select>
            </label>
          </div>
          <div style={{ marginTop: '10px' }}>
            <button type="submit" style={{ marginRight: '10px' }}>
              Сохранить
            </button>
            <button type="button" onClick={cancelEdit}>
              Отмена
            </button>
          </div>
        </form>
      )}

      {members.length === 0 ? (
        <p>Нет читателей</p>
      ) : (
        <ul>
          {members.map(m => (
            <li key={m.id}>
              {m.first_name} {m.last_name} - {m.email} 
              <span style={{ color: m.membership_status === 'active' ? 'green' : 'red' }}>
                ({m.membership_status})
              </span>
              {canManage && (
                <button
                  onClick={() => startEdit(m)}
                  style={{ marginLeft: '10px' }}
                >
                  Редактировать
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
