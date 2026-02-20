import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { LogOut, User, Users, LayoutDashboard, Calendar, History, BookOpen, Home } from 'lucide-react';
import { authService } from '../services/authService';

const Layout = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const user = authService.getCurrentUser();
    const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

    const handleLogout = () => {
        authService.logout();
        navigate('/login');
    };

    const navItems = isAdmin
        ? [
            { name: 'Dashboard', path: '/admin', icon: LayoutDashboard },
            { name: 'Schedules', path: '/admin/schedules', icon: Calendar },
            { name: 'Papers', path: '/admin/papers', icon: BookOpen },
            { name: 'Candidates', path: '/admin/candidates', icon: Users },
        ]
        : [
            { name: 'Dashboard', path: '/candidate', icon: LayoutDashboard },
            { name: 'History', path: '/candidate/history', icon: History },
        ];

    const getHomeRoute = () => isAdmin ? '/admin' : '/candidate';

    return (
        <div className="min-h-screen bg-gray-50 flex">
            {/* Sidebar Navigation */}
            <aside className="w-64 bg-white border-r border-gray-200 sticky top-0 h-screen flex flex-col z-50">
                <div className="p-6 pb-2">
                    <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate(getHomeRoute())}>
                        <div className="w-10 h-10 bg-brand-orange rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm shadow-brand-orange/20">
                            <span className="text-white font-bold text-2xl font-serif">v</span>
                        </div>
                        <span className="font-bold text-2xl tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-gray-900 to-gray-700">
                            VisionAI
                        </span>
                    </div>
                </div>

                <nav className="flex-1 px-4 py-8 space-y-1 overflow-y-auto">
                    {navItems.map((item, idx) => (
                        <button
                            key={`${item.path}-${idx}`}
                            onClick={() => navigate(item.path)}
                            className={`w-full px-4 py-3 rounded-xl flex items-center gap-3 text-sm font-semibold transition-all duration-200 ${location.pathname === item.path && item.name !== 'Home'
                                ? 'bg-brand-orange/10 text-brand-orange shadow-sm'
                                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                                }`}
                        >
                            <item.icon size={20} className={location.pathname === item.path && item.name !== 'Home' ? 'text-brand-orange' : 'text-gray-400'} />
                            {item.name}
                        </button>
                    ))}
                </nav>

                <div className="p-4 border-t border-gray-100 bg-gray-50/50">
                    <div className="flex items-center justify-between p-2 rounded-xl border border-gray-200 bg-white shadow-sm">
                        <div className="flex items-center gap-3 truncate">
                            <div className="w-10 h-10 bg-brand-orange/10 rounded-full flex items-center justify-center text-brand-orange border border-brand-orange/20 flex-shrink-0">
                                <User size={20} />
                            </div>
                            <div className="flex flex-col truncate pr-2">
                                <p className="text-sm font-bold text-gray-900 truncate">{user?.full_name || 'User'}</p>
                                <p className="text-xs text-brand-orange font-medium tracking-wide uppercase">{user?.role || 'Guest'}</p>
                            </div>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors flex-shrink-0"
                            title="Logout"
                        >
                            <LogOut size={18} />
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
                <main className="flex-1 w-full max-w-7xl mx-auto px-6 lg:px-12 py-8">
                    <Outlet />
                </main>

                {/* Optional Footer inside the scrolling content */}
                <footer className="py-6 mt-auto border-t border-gray-200">
                    <div className="max-w-7xl mx-auto px-6 lg:px-12 text-center text-sm font-medium text-gray-400 flex items-center justify-center gap-2">
                        <span>© 2026 VisionAI</span>
                        <span className="w-1 h-1 bg-gray-300 rounded-full"></span>
                        <span>Professional AI-Powered Proctoring</span>
                    </div>
                </footer>
            </div>
        </div>
    );
};

export default Layout;
