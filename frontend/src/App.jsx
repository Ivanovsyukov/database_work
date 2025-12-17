import { useState, useEffect } from 'react';
import axios from 'axios';
import Login from './components/Login';

// Компоненты
import BookList from './components/BookList';
import MemberList from './components/MemberList';
import LoanForm from './components/LoanForm';
import ReturnForm from './components/ReturnForm';
import MemberRegistration from './components/MemberRegistration';
import ReservationList from './components/ReservationList';
import FineManagement from './components/FineManagement';
import BookManagement from './components/BookManagement';
import CopyManagement from './components/CopyManagement';

export default function App(){
  const [staff, setStaff] = useState(null);
  const [activeTab, setActiveTab] = useState('books');

  useEffect(() => {
    const saved = localStorage.getItem('staff');
    if (saved) {
      try {
        setStaff(JSON.parse(saved));
      } catch (e) {
        localStorage.removeItem('staff');
      }
    }
  }, []);

  const handleLogout = async () => {
    try {
      await axios.post('http://localhost:8000/api/auth/logout');
    } catch (err) {
      console.warn('Ошибка при выходе:', err);
    }
    localStorage.removeItem('staff');
    setStaff(null);
  };

  if (!staff) {
    return <Login onLogin={setStaff} />;
  }

  // Определяем, имеет ли доступ (библиотекарь или админ)
  const canManage = staff.role === 'librarian' || staff.role === 'admin';

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', position: 'relative' }}>
      <button
        onClick={handleLogout}
        style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          padding: '6px 12px',
          background: '#dc3545',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
        }}
      >
        Выйти
      </button>

      <h1>Добро пожаловать, {staff.first_name} {staff.last_name} ({staff.role})</h1>

      <div style={{ marginTop: '50px', marginBottom: '20px' }}>
        <button
          onClick={() => setActiveTab('books')}
          style={tabStyle(activeTab === 'books')}
        >
          Книги
        </button>
        <button
          onClick={() => setActiveTab('members')}
          style={tabStyle(activeTab === 'members')}
        >
          Читатели
        </button>

        {canManage && (
          <>
            <button
              onClick={() => setActiveTab('loan')}
              style={tabStyle(activeTab === 'loan')}
            >
              Выдать книгу
            </button>
            <button
              onClick={() => setActiveTab('return')}
              style={tabStyle(activeTab === 'return')}
            >
              Вернуть книгу
            </button>
            <button
              onClick={() => setActiveTab('register-member')}
              style={tabStyle(activeTab === 'register-member')}
            >
              Зарегистрировать читателя
            </button>
            <button
              onClick={() => setActiveTab('reservations')}
              style={tabStyle(activeTab === 'reservations')}
            >
              Бронирования
            </button>
            <button
              onClick={() => setActiveTab('fines')}
              style={tabStyle(activeTab === 'fines')}
            >
              Штрафы
            </button>
            <button
              onClick={() => setActiveTab('book-management')}
              style={tabStyle(activeTab === 'book-management')}
            >
              Управление книгами
            </button>
            <button
              onClick={() => setActiveTab('copy-management')}
              style={tabStyle(activeTab === 'copy-management')}
            >
              Добавить копию
            </button>
          </>
        )}
      </div>

      {/* Основные просмотры */}
      {activeTab === 'books' && <BookList />}
      {activeTab === 'members' && <MemberList />}

      {/* Функции для библиотекарей */}
      {canManage && activeTab === 'loan' && <LoanForm />}
      {canManage && activeTab === 'return' && <ReturnForm />}
      {canManage && activeTab === 'register-member' && <MemberRegistration />}
      {canManage && activeTab === 'reservations' && <ReservationList />}
      {canManage && activeTab === 'fines' && <FineManagement />}
      {canManage && activeTab === 'book-management' && <BookManagement />}
      {canManage && activeTab === 'copy-management' && <CopyManagement />}
    </div>
  );
}

// Вспомогательная функция для стилей вкладок
function tabStyle(isActive) {
  return {
    padding: '8px 16px',
    margin: '0 6px',
    background: isActive ? '#007bff' : '#f0f0f0',
    color: isActive ? 'white' : 'black',
    border: '1px solid #ccc',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  };
}