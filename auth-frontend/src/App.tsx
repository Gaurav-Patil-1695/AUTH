import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import RequireAuth from './features/auth/RequireAuth';
import RequireGuest from './features/auth/RequireGuest';
import LoginPage from './features/auth/pages/LoginPage';
import RegisterPage from './features/auth/pages/RegisterPage';
import ForgotPasswordPage from './features/auth/pages/ForgotPasswordPage';
import ResetPasswordPage from './features/auth/pages/ResetPasswordPage';
import ProfilePage from './pages/ProfilePage';
import LogoutRoute from './features/auth/LogoutRoute';

const App: React.FC = () => {
  return (
    <Routes>
      <Route element={<RequireGuest />}>
        <Route path='/login' element={<LoginPage />} />
        <Route path='/register' element={<RegisterPage />} />
        <Route path='/forgot-password' element={<ForgotPasswordPage />} />
        <Route path='/reset-password' element={<ResetPasswordPage />} />
      </Route>

      <Route element={<RequireAuth />}>
        <Route path='/profile' element={<ProfilePage />} />
      </Route>

      <Route path='/logout' element={<LogoutRoute />} />

      <Route path='*' element={<Navigate to='/login' replace />} />
    </Routes>
  );
};

export default App;
