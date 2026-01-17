import React, { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { Home, TrendingUp, BookOpen, Settings, Menu, X, GraduationCap } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const Layout = () => {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const location = useLocation();
    const { user } = useAuth();

    const navigation = [
        { name: 'Dashboard', href: '/', icon: Home },
        { name: 'My Performance', href: '/performance', icon: TrendingUp },
        { name: 'Subjects', href: '/subjects', icon: BookOpen },
        { name: 'Settings', href: '/settings', icon: Settings },
    ];

    const studentName = user?.name || 'Student';

    return (
        <div className="min-h-screen bg-[#f5f7fb] dark:bg-zinc-950 transition-colors duration-300">
            {/* Glassmorphism Header */}
            <header className="bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md border-b border-gray-200/50 dark:border-zinc-700/50 sticky top-0 z-50 transition-colors duration-300">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        {/* Logo */}
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-md">
                                <GraduationCap className="h-6 w-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-lg font-bold text-gray-900 dark:text-zinc-100">Academic Portal</h1>
                                <p className="text-xs text-gray-500 dark:text-zinc-400 hidden sm:block">{studentName}</p>
                            </div>
                        </div>

                        {/* Desktop Navigation */}
                        <nav className="hidden md:flex items-center gap-1">
                            {navigation.map((item) => {
                                const isActive = location.pathname === item.href;
                                return (
                                    <NavLink
                                        key={item.name}
                                        to={item.href}
                                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isActive
                                            ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
                                            : 'text-gray-600 dark:text-zinc-400 hover:bg-gray-50 dark:hover:bg-zinc-800 hover:text-gray-900 dark:hover:text-zinc-200'
                                            }`}
                                    >
                                        <item.icon className="h-4 w-4" />
                                        <span>{item.name}</span>
                                    </NavLink>
                                );
                            })}
                        </nav>

                        {/* Mobile Menu Button */}
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800"
                        >
                            {mobileMenuOpen ? (
                                <X className="h-5 w-5 text-gray-600 dark:text-zinc-400" />
                            ) : (
                                <Menu className="h-5 w-5 text-gray-600 dark:text-zinc-400" />
                            )}
                        </button>
                    </div>
                </div>

                {/* Mobile Navigation */}
                {mobileMenuOpen && (
                    <div className="md:hidden border-t border-gray-200/50 dark:border-zinc-700/50 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-md">
                        <nav className="px-4 py-4 space-y-1">
                            {navigation.map((item) => {
                                const isActive = location.pathname === item.href;
                                return (
                                    <NavLink
                                        key={item.name}
                                        to={item.href}
                                        onClick={() => setMobileMenuOpen(false)}
                                        className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${isActive
                                            ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
                                            : 'text-gray-600 dark:text-zinc-400 hover:bg-gray-50 dark:hover:bg-zinc-800'
                                            }`}
                                    >
                                        <item.icon className="h-5 w-5" />
                                        <span>{item.name}</span>
                                    </NavLink>
                                );
                            })}
                        </nav>
                    </div>
                )}
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <Outlet />
            </main>
        </div>
    );
};

export default Layout;
