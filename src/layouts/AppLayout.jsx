import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar.jsx';
import Navbar from '../components/Navbar.jsx';
import FloatingAssistantButton from '../components/FloatingAssistantButton.jsx';

function AppLayout() {
  return (
    <div className="h-screen overflow-hidden bg-ink/80 text-slate-100">
      <div className="flex h-full">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Navbar />
          <main className="thin-scrollbar min-h-0 flex-1 overflow-y-auto px-4 pb-5 pt-4 sm:px-6">
            <Outlet />
          </main>
        </div>
      </div>
      <FloatingAssistantButton />
    </div>
  );
}

export default AppLayout;
