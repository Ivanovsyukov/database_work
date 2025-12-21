import { useState, useEffect } from 'react';
import axios from 'axios';

export default function MemberAutocomplete({ value, onChange, placeholder = "Начните вводить ФИО..." }) {
  const [input, setInput] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showList, setShowList] = useState(false);
  const [loading, setLoading] = useState(false);

  // Сброс текста при сбросе value извне
  useEffect(() => {
    if (!value) setInput('');
  }, [value]);

  // Поиск читателей при вводе
  useEffect(() => {
    if (!input.trim()) {
      setSuggestions([]);
      setShowList(false);
      return;
    }

    const fetchMembers = async () => {
      setLoading(true);
      try {
        // Ищем по имени или фамилии
        const res = await axios.get(`/members?search=${encodeURIComponent(input)}`);
        setSuggestions(res.data);
        setShowList(true);
      } catch (err) {
        console.error("Ошибка поиска читателей", err);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    };

    const timer = setTimeout(fetchMembers, 300);
    return () => clearTimeout(timer);
  }, [input]);

  const handleSelect = (member) => {
    onChange(member.id, `${member.last_name} ${member.first_name}`);
    setInput(`${member.last_name} ${member.first_name}`);
    setShowList(false);
  };

  const handleInputChange = (e) => {
    const val = e.target.value;
    setInput(val);
    if (!val) onChange(null, '');
    setShowList(true);
  };

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <input
        type="text"
        value={input}
        onChange={handleInputChange}
        placeholder={placeholder}
        style={{
          width: '100%',
          padding: '6px',
          border: '1px solid #ccc',
          borderRadius: '4px',
        }}
        onFocus={() => input && setShowList(true)}
        onBlur={() => setTimeout(() => setShowList(false), 200)}
      />
      {loading && <div style={{ fontSize: '0.9em', color: '#666' }}>Поиск...</div>}

      {showList && suggestions.length > 0 && (
        <ul
          style={{
            position: 'absolute',
            zIndex: 100,
            width: '100%',
            maxHeight: '150px',
            overflowY: 'auto',
            border: '1px solid #ccc',
            borderRadius: '0 0 4px 4px',
            backgroundColor: 'white',
            listStyle: 'none',
            padding: 0,
            margin: 0,
          }}
        >
          {suggestions.map(member => (
            <li
              key={member.id}
              onMouseDown={(e) => {
                e.preventDefault();
                handleSelect(member);
              }}
              style={{
                padding: '6px 8px',
                cursor: 'pointer',
                borderBottom: '1px solid #eee',
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
            >
              {member.last_name} {member.first_name} ({member.email})
              <div style={{ fontSize: '0.9em', color: '#666' }}>
                {member.membership_status === 'active' ? 'Активен' : 'Заблокирован'}
              </div>
            </li>
          ))}
        </ul>
      )}

      {showList && suggestions.length === 0 && input.trim() && !loading && (
        <div style={{
          position: 'absolute',
          zIndex: 100,
          width: '100%',
          padding: '6px',
          border: '1px solid #ccc',
          borderTop: 'none',
          backgroundColor: 'white',
          borderRadius: '0 0 4px 4px',
        }}>
          Читатели не найдены
        </div>
      )}
    </div>
  );
}
