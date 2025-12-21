import { useState } from 'react';
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
import AuthorManagement from './components/AuthorManagement';
import LoanDashboard from './components/LoanDashboard';
import Reports from './components/Reports';
import StaffManagement from './components/StaffManagment';

export default function App(){
  const [staff, setStaff] = useState(() => {
    const saved = localStorage.getItem('staff');
    if (!saved) return null;
    try {
      return JSON.parse(saved);
    } catch {
      localStorage.removeItem('staff');
      return null;
    }
  });
  const [activeTab, setActiveTab] = useState('books');

  const handleLogout = async () => {
    try {
      await axios.post('/auth/logout');
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
  const isAdmin = staff.role === 'admin';

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
              onClick={() => setActiveTab('authors')}
              style={tabStyle(activeTab === 'authors')}
            >
              Авторы
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
            <button
              onClick={() => setActiveTab('loan-dashboard')}
              style={tabStyle(activeTab === 'loan-dashboard')}
            >
              Выдачи
            </button>
            {isAdmin && (
              <>
                <button
                  onClick={() => setActiveTab('reports')}
                  style={tabStyle(activeTab === 'reports')}
                >
                  Отчёты
                </button>
                <button
                  onClick={() => setActiveTab('staff-management')}
                  style={tabStyle(activeTab === 'staff-management')}
                >
                  Управление сотрудниками
                </button>
              </>
            )}
          </>
        )}
      </div>

      {/* Основные просмотры */}
      {activeTab === 'books' && <BookList />}
      {activeTab === 'members' && <MemberList canManage={canManage} />}

      {/* Функции для библиотекарей */}
      {canManage && activeTab === 'loan' && <LoanForm />}
      {canManage && activeTab === 'return' && <ReturnForm />}
      {canManage && activeTab === 'register-member' && <MemberRegistration />}
      {canManage && activeTab === 'authors' && <AuthorManagement />}
      {canManage && activeTab === 'reservations' && <ReservationList />}
      {canManage && activeTab === 'fines' && <FineManagement />}
      {canManage && activeTab === 'book-management' && <BookManagement />}
      {canManage && activeTab === 'copy-management' && <CopyManagement />}
      {canManage && activeTab === 'loan-dashboard' && <LoanDashboard />}
      {isAdmin && activeTab === 'reports' && <Reports />}
      {isAdmin && activeTab === 'staff-management' && <StaffManagement isAdmin={isAdmin} />}
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
