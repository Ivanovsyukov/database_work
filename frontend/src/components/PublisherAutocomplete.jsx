import { useState, useEffect } from 'react';
import axios from 'axios';

export default function PublisherAutocomplete({ value, onChange, onNewPublisher }) {
  const [input, setInput] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showList, setShowList] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!input.trim()) {
      setSuggestions([]);
      setShowList(false);
      return;
    }

    const fetchPublishers = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`http://localhost:8000/api/publishers/?name=${encodeURIComponent(input)}`);
        setSuggestions(res.data);
        setShowList(true);
      } catch (err) {
        console.error("Ошибка поиска издателей", err);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    };

    const timer = setTimeout(fetchPublishers, 300);
    return () => clearTimeout(timer);
  }, [input]);

  const handleSelect = (publisher) => {
    onChange(publisher.id, publisher.name);
    setInput(publisher.name);
    setShowList(false);
  };

  const handleInputChange = (e) => {
    const val = e.target.value;
    setInput(val);
    if (!val) {
      onChange(null, '');
    }
    setShowList(true);
  };

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <input
        type="text"
        value={input}
        onChange={handleInputChange}
        placeholder="Введите название издательства..."
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
        <ul style={{
          position: 'absolute', zIndex: 100, width: '100%',
          maxHeight: '150px', overflowY: 'auto',
          border: '1px solid #ccc', borderRadius: '0 0 4px 4px',
          backgroundColor: 'white', listStyle: 'none', padding: 0, margin: 0
        }}>
          {suggestions.map(pub => (
            <li
              key={pub.id}
              onClick={() => handleSelect(pub)}
              style={{ padding: '6px 8px', cursor: 'pointer', borderBottom: '1px solid #eee' }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
            >
              {pub.name}
            </li>
          ))}
        </ul>
      )}

      {showList && suggestions.length === 0 && input.trim() && !loading && (
        <div style={{
          position: 'absolute', zIndex: 100, width: '100%',
          padding: '6px',
          border: '1px solid #ccc', borderTop: 'none',
          backgroundColor: 'white', borderRadius: '0 0 4px 4px'
        }}>
          Не найдено — нажмите Enter, чтобы создать
        </div>
      )}

      {/* Обработка нажатия Enter для создания нового */}
      {!suggestions.length && input.trim() && (
        <div style={{ marginTop: '4px' }}>
          <button
            type="button"
            onClick={() => onNewPublisher(input.trim())}
            style={{ padding: '4px 8px', fontSize: '0.9em' }}
          >
            + Добавить «{input.trim()}»
          </button>
        </div>
      )}
    </div>
  );
}