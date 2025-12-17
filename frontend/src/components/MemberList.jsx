import { useEffect, useState } from 'react';
import axios from 'axios';

export default function MemberList() {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('http://localhost:8000/api/members/')
      .then(res => {
        setMembers(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Ошибка загрузки читателей:', err);
        setLoading(false);
      });
  }, []);

  if (loading) return <p>Загрузка...</p>;

  return (
    <div>
      <h2>Читатели</h2>
      {members.length === 0 ? (
        <p>Нет читателей</p>
      ) : (
        <ul>
          {members.map(m => (
            <li key={m.id}>
              {m.first_name} {m.last_name} — {m.email} 
              <span style={{ color: m.membership_status === 'active' ? 'green' : 'red' }}>
                ({m.membership_status})
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}