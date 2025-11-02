import { useAuth } from '../../contexts/AuthContext';
import Sidebar from '../common/Sidebar';
import './AppLayout.css';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { isAuthenticated } = useAuth();

  return (
    <div className="app-layout">
      {isAuthenticated && <Sidebar />}
      <main className={`app-main ${isAuthenticated ? 'with-sidebar' : ''}`}>
        {children}
      </main>
    </div>
  );
}

