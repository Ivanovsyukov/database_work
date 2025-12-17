import { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * Компонент автозаполнения книги по названию.
 * 
 * Пропсы:
 * - value: ID выбранной книги (для двусторонней привязки)
 * - onChange: (bookId, bookTitle) => void
 * - placeholder: строка-подсказка
 */
export default function BookAutocomplete({ value, onChange, placeholder = "Начните вводить название..." }) {
  const [input, setInput] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showList, setShowList] = useState(false);
  const [loading, setLoading] = useState(false);

  // При изменении value извне (например, при сбросе формы) — сбрасываем текст
  useEffect(() => {
    if (!value) {
      setInput('');
    }
  }, [value]);

  // Загружаем подсказки при вводе
  useEffect(() => {
    if (!input.trim()) {
      setSuggestions([]);
      setShowList(false);
      return;
    }

    const fetchBooks = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`http://localhost:8000/api/books/?title=${encodeURIComponent(input)}`);
        setSuggestions(res.data);
        setShowList(true);
      } catch (err) {
        console.error("Ошибка поиска книг", err);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    };

    const timer = setTimeout(fetchBooks, 300); // debounce
    return () => clearTimeout(timer);
  }, [input]);

  const handleSelect = (book) => {
    onChange(book.id, book.title);
    setInput(book.title);
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
        placeholder={placeholder}
        style={{
          width: '100%',
          padding: '6px',
          border: '1px solid #ccc',
          borderRadius: '4px',
        }}
        onFocus={() => input && setShowList(true)}
        onBlur={() => setTimeout(() => setShowList(false), 200)} // задержка для клика по списку
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
          {suggestions.map(book => (
            <li
              key={book.id}
              onClick={() => handleSelect(book)}
              style={{
                padding: '6px 8px',
                cursor: 'pointer',
                borderBottom: '1px solid #eee',
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
            >
              <strong>{book.title}</strong> ({book.isbn})
              {book.genre && <span style={{ color: '#666', marginLeft: '6px' }}>[{book.genre}]</span>}
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
          Книг не найдено
        </div>
      )}
    </div>
  );
}