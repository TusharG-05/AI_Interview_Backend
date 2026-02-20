import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { LogOut, User, LayoutDashboard, Calendar, History } from 'lucide-react';
import { authService } from '../services/authService';

const Layout = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const user = authService.getCurrentUser();
    const isAdmin = user?.role === 'admin';

    const handleLogout = () => {
        authService.logout();
        navigate('/login');
    };

    const navItems = isAdmin
        ? [
            { name: 'Dashboard', path: '/admin', icon: LayoutDashboard },
            { name: 'Schedules', path: '/admin/schedules', icon: Calendar },
        ]
        : [
            { name: 'Invites', path: '/candidate', icon: Calendar },
            { name: 'History', path: '/candidate/history', icon: History },
        ];

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-8">
                        <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate(isAdmin ? '/admin' : '/candidate')}>
                            <div className="w-8 h-8 bg-brand-orange rounded-lg flex items-center justify-center">
                                <span className="text-white font-bold text-xl">v</span>
                            </div>
                            <span className="font-bold text-xl bg-clip-text text-transparent bg-gradient-to-r from-brand-orange to-brand-orange-dark">
                                VisionAI
                            </span>
                        </div>

                        <nav className="hidden md:flex items-center gap-1">
                            {navItems.map((item) => (
                                <button
                                    key={item.path}
                                    onClick={() => navigate(item.path)}
                                    className={`px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium transition-colors ${location.pathname === item.path
                                            ? 'bg-brand-orange/10 text-brand-orange'
                                            : 'text-gray-600 hover:bg-gray-100'
                                        }`}
                                >
                                    <item.icon size={18} />
                                    {item.name}
                                </button>
                            ))}
                        </nav>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-3 pr-4 border-r border-gray-200">
                            <div className="text-right hidden sm:block">
                                <p className="text-sm font-semibold text-gray-900">{user?.full_name || 'User'}</p>
                                <p className="text-xs text-gray-500 capitalize">{user?.role || 'Guest'}</p>
                            </div>
                            <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center text-gray-600 border border-gray-200">
                                <User size={20} />
                            </div>
                        </div>

                        <button
                            onClick={handleLogout}
                            className="p-2 text-gray-400 hover:text-brand-orange hover:bg-brand-orange/5 rounded-lg transition-all"
                            title="Logout"
                        >
                            <LogOut size={20} />
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <Outlet />
            </main>

            {/* Footer */}
            <footer className="bg-white border-t border-gray-200 py-6 mt-auto">
                <div className="max-w-7xl mx-auto px-4 text-center">
                    <p className="text-sm text-gray-500">
                        © 2026 VisionAI Interview Platform. Professional AI-Powered Proctoring.
                    </p>
                </div>
            </footer>
        </div>
    );
};

export default Layout;
