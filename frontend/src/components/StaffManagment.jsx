import { useState, useEffect } from 'react';
import axios from 'axios';

export default function StaffManagement({ isAdmin }) {
  // === Состояние для формы создания ===
  const [createForm, setCreateForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    // role фиксирован как 'librarian' — нельзя создать админа!
  });

  // === Состояние для списка сотрудников ===
  const [staffList, setStaffList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  // === Загрузка списка сотрудников ===
  const fetchStaff = async () => {
    try {
      const res = await axios.get('/staff');
      setStaffList(res.data);
    } catch (err) {
      setMessage('Ошибка загрузки сотрудников');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStaff();
  }, []);

  // === Создание библиотекаря ===
  const handleCreate = async (e) => {
    e.preventDefault();
    setMessage('');
    try {
      // ВСЕГДА создаём только библиотекаря
      await axios.post('/staff', {
        first_name: createForm.first_name.trim(),
        last_name: createForm.last_name.trim(),
        email: createForm.email.trim(),
        role: 'librarian', // ← ФИКСИРОВАННОЕ ЗНАЧЕНИЕ
      });
      setMessage('Библиотекарь успешно создан');
      setCreateForm({ first_name: '', last_name: '', email: '' });
      fetchStaff(); // Обновить список
    } catch (err) {
      setMessage('Ошибка: ' + JSON.stringify(err.response?.data));
    }
  };

  // === Обновление сотрудника ===
  const handleUpdate = async (id, updatedData) => {
    try {
      await axios.put(`/staff/${id}`, updatedData);
      setMessage('Данные сотрудника обновлены');
      fetchStaff();
    } catch (err) {
      setMessage('Ошибка обновления: ' + JSON.stringify(err.response?.data));
    }
  };

  // === Удаление библиотекаря (только для админов) ===
  const handleDelete = async (id) => {
    if (!isAdmin) return;
    if (!window.confirm('Удалить библиотекаря? Это действие нельзя отменить.')) return;

    try {
      await axios.delete(`/staff/${id}`);
      setMessage('Библиотекарь удалён');
      fetchStaff();
    } catch (err) {
      setMessage('Ошибка удаления: ' + JSON.stringify(err.response?.data));
    }
  };

  return (
    <div>
      <h2>Управление сотрудниками</h2>

      <div style={{ marginBottom: '30px', padding: '15px', border: '1px solid #ddd', borderRadius: '8px' }}>
        <h3>Создать библиотекаря</h3>
        <form onSubmit={handleCreate}>
          <input
            name="first_name"
            placeholder="Имя"
            value={createForm.first_name}
            onChange={(e) => setCreateForm({ ...createForm, first_name: e.target.value })}
            required
            style={{ width: '100%', padding: '6px', margin: '4px 0' }}
          />
          <input
            name="last_name"
            placeholder="Фамилия"
            value={createForm.last_name}
            onChange={(e) => setCreateForm({ ...createForm, last_name: e.target.value })}
            required
            style={{ width: '100%', padding: '6,px', margin: '4px 0' }}
          />
          <input
            name="email"
            type="email"
            placeholder="Email"
            value={createForm.email}
            onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
            required
            style={{ width: '100%', padding: '6px', margin: '4px 0' }}
          />
          <button type="submit" style={{ padding: '6px 12px', marginTop: '8px' }}>
            Создать библиотекаря
          </button>
        </form>
      </div>

      <div>
        <h3>Список сотрудников</h3>
        {loading ? (
          <p>Загрузка...</p>
        ) : staffList.length === 0 ? (
          <p>Нет сотрудников</p>
        ) : (
          <table border="1" cellPadding="8" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Имя</th>
                <th>Фамилия</th>
                <th>Email</th>
                <th>Роль</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {staffList.map((staff) => (
                <StaffRow
                  key={staff.id}
                  staff={staff}
                  isAdmin={isAdmin}
                  onUpdate={handleUpdate}
                  onDelete={handleDelete}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {message && (
        <p style={{ marginTop: '10px', color: message.includes('Ошибка') ? 'red' : 'green' }}>
          {message}
        </p>
      )}
    </div>
  );
}

// === Вспомогательный компонент для строки таблицы ===
function StaffRow({ staff, isAdmin, onUpdate, onDelete }) {
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({ ...staff });

  const handleSave = () => {
    // Не позволяем менять роль на 'admin' через интерфейс
    const dataToSend = { ...editData };
    if (staff.role === 'admin' && dataToSend.role !== 'admin') {
      // Админов можно только оставить админами (или, по желанию, запретить редактирование роли)
      dataToSend.role = 'admin';
    }
    onUpdate(staff.id, dataToSend);
    setEditMode(false);
  };

  if (editMode) {
    return (
      <tr>
        <td>{staff.id}</td>
        <td>
          <input
            value={editData.first_name}
            onChange={(e) => setEditData({ ...editData, first_name: e.target.value })}
          />
        </td>
        <td>
          <input
            value={editData.last_name}
            onChange={(e) => setEditData({ ...editData, last_name: e.target.value })}
          />
        </td>
        <td>
          <input
            value={editData.email}
            onChange={(e) => setEditData({ ...editData, email: e.target.value })}
          />
        </td>
        <td>
          {staff.role === 'admin' ? (
            'admin'
          ) : (
            <select
              value={editData.role}
              onChange={(e) => setEditData({ ...editData, role: e.target.value })}
            >
              <option value="librarian">Библиотекарь</option>
            </select>
          )}
        </td>
        <td>
          <button onClick={handleSave} style={{ marginRight: '4px' }}>Сохранить</button>
          <button onClick={() => setEditMode(false)}>Отмена</button>
        </td>
      </tr>
    );
  }

  return (
    <tr>
      <td>{staff.id}</td>
      <td>{staff.first_name}</td>
      <td>{staff.last_name}</td>
      <td>{staff.email}</td>
      <td>{staff.role}</td>
      <td>
        <button onClick={() => setEditMode(true)} style={{ marginRight: '4px' }}>
          Редактировать
        </button>
        {isAdmin && staff.role === 'librarian' && (
          <button
            onClick={() => onDelete(staff.id)}
            style={{ background: '#dc3545', color: 'white', border: 'none', padding: '2px 6px' }}
          >
            Удалить
          </button>
        )}
      </td>
    </tr>
  );
}