import { useState } from 'react';
import axios from 'axios';

export default function MemberRegistration() {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    address: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:8000/api/members/', formData);
      alert('Читатель успешно зарегистрирован!');
      setFormData({ first_name: '', last_name: '', email: '', phone: '', address: '' });
    } catch (err) {
      alert('Ошибка: ' + JSON.stringify(err.response?.data));
    }
  };

  return (
    <div>
      <h2>Регистрация нового читателя</h2>
      <form onSubmit={handleSubmit}>
        <input name="first_name" placeholder="Имя" value={formData.first_name} onChange={handleChange} required />
        <input name="last_name" placeholder="Фамилия" value={formData.last_name} onChange={handleChange} required />
        <input name="email" type="email" placeholder="Email" value={formData.email} onChange={handleChange} required />
        <input name="phone" placeholder="Телефон" value={formData.phone} onChange={handleChange} />
        <textarea name="address" placeholder="Адрес" value={formData.address} onChange={handleChange} />
        <button type="submit">Зарегистрировать</button>
      </form>
    </div>
  );
}