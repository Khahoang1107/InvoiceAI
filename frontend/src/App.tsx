import { useState } from 'react';
import { Toaster } from 'sonner';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { UserDashboard } from './pages/UserDashboard';
import { AdminDashboard } from './pages/AdminDashboard';
import { useAuth } from './hooks/useAuth';
import { PageType } from './types';

export default function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('login');
  const { currentUser, login, logout, updateUser, isLoading } = useAuth();

  const handleLogin = async (email: string, password: string): Promise<boolean> => {
    return await login({ email, password });
  };

  const handleLogout = () => {
    logout();
    setCurrentPage('login');
  };

  // Show loading while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // If user is logged in, show appropriate dashboard
  if (currentUser) {
    console.log('🎯 Current User in App:', {
      email: currentUser.email,
      name: currentUser.name,
      role: currentUser.role,
      roleType: typeof currentUser.role,
      willShowAdmin: currentUser.role?.toLowerCase() === 'admin'
    });

    // TEMP DEBUG
    alert(`DEBUG: role="${currentUser.role}", type=${typeof currentUser.role}, isAdmin=${currentUser.role?.toLowerCase() === 'admin'}`);

    if (currentUser.role?.toLowerCase() === 'admin') {
      console.log('✨ Rendering AdminDashboard');
      return (
        <>
          <Toaster position="top-right" richColors expand={true} />
          <AdminDashboard user={currentUser} onLogout={handleLogout} />
        </>
      );
    } else {
      console.log('👤 Rendering UserDashboard');
      return (
        <>
          <Toaster position="top-right" richColors expand={true} />
          <UserDashboard 
            user={currentUser} 
            onLogout={handleLogout} 
            onUpdateUser={updateUser} 
          />
        </>
      );
    }
  }

  // Show login or signup page
  return (
    <>
      <Toaster position="top-right" richColors expand={true} />
      {currentPage === 'login' ? (
        <LoginPage 
          onNavigateToSignup={() => setCurrentPage('signup')}
          onLogin={handleLogin}
        />
      ) : (
        <SignupPage onNavigateToLogin={() => setCurrentPage('login')} />
      )}
    </>
  );
}
