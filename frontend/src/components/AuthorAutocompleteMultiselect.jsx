import { useState, useEffect } from 'react';
import axios from 'axios';

export default function AuthorAutocompleteMultiselect({ selectedAuthors, onChange }) {
  const [input, setInput] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showList, setShowList] = useState(false);

  // При вводе — ищем авторов
  useEffect(() => {
    if (!input.trim()) {
      setSuggestions([]);
      setShowList(false);
      return;
    }

    const fetchAuthors = async () => {
      setLoading(true);
      try {
        // Ищем по фамилии или имени
        const res = await axios.get(`/authors?search=${encodeURIComponent(input)}`);
        setSuggestions(res.data);
        setShowList(true);
      } catch (err) {
        console.error("Ошибка поиска авторов", err);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    };

    const timer = setTimeout(fetchAuthors, 300);
    return () => clearTimeout(timer);
  }, [input]);

  // Добавить автора в выбранные
  const handleSelect = (author) => {
    if (!selectedAuthors.some(a => a.id === author.id)) {
      onChange([...selectedAuthors, author]);
    }
    setInput('');
    setShowList(false);
  };

  // Удалить автора
  const handleRemove = (authorId) => {
    onChange(selectedAuthors.filter(a => a.id !== authorId));
  };

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      {/* Выбранные авторы — как теги */}
      <div style={{ marginBottom: '6px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
        {selectedAuthors.map(author => (
          <span
            key={author.id}
            style={{
              background: '#007bff',
              color: 'white',
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            {author.last_name} {author.first_name}
            <button
              type="button"
              onClick={() => handleRemove(author.id)}
              style={{
                background: 'none',
                border: 'none',
                color: 'white',
                cursor: 'pointer',
                fontSize: '16px',
                lineHeight: 1
              }}
            >
              ×
            </button>
          </span>
        ))}
      </div>

      {/* Поле ввода */}
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Начните вводить имя или фамилию автора..."
        style={{
          width: '10??%',
          padding: '6px',
          border: '1px solid #ccc',
          borderRadius: '4px',
        }}
        onFocus={() => input && setShowList(true)}
        onBlur={() => setTimeout(() => setShowList(false), 200)}
      />

      {loading && <div style={{ fontSize: '0.9em', color: '#666' }}>Поиск...</div>}

      {/* Выпадающий список */}
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
          {suggestions.map(author => (
            <li
              key={author.id}
              onClick={() => handleSelect(author)}
              style={{
                padding: '6px 8px',
                cursor: 'pointer',
                borderBottom: '1px solid #eee',
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
            >
              {author.last_name} {author.first_name}
              {author.birth_date && <span style={{ color: '#666', marginLeft: '6px' }}>
                ({author.birth_date})
              </span>}
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
          Авторы не найдены
        </div>
      )}
    </div>
  );
}