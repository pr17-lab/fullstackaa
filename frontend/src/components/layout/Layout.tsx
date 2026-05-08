import { useState, useEffect } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { Home, BookOpen, Settings, Menu, X, GraduationCap, Cpu, Target, Map, LogOut } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';

const Layout = () => {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const location = useLocation();
    const { user, logout } = useAuth();

    // Close mobile menu on route change
    useEffect(() => {
        setMobileMenuOpen(false);
    }, [location.pathname]);

    const navigation = [
        { name: 'Dashboard', href: '/', icon: Home, accentText: 'text-indigo-400', accentBg: 'bg-indigo-400', border: 'border-indigo-500' },
        { name: 'Subjects', href: '/subjects', icon: BookOpen, accentText: 'text-blue-400', accentBg: 'bg-blue-400', border: 'border-blue-500' },
        { name: 'Interview Prep', href: '/interview', icon: Cpu, accentText: 'text-teal-400', accentBg: 'bg-teal-400', border: 'border-teal-500' },
        { name: 'Skills & Career', href: '/skills', icon: Target, accentText: 'text-purple-400', accentBg: 'bg-purple-400', border: 'border-purple-500' },
        { name: 'My Roadmap', href: '/roadmap', icon: Map, accentText: 'text-orange-400', accentBg: 'bg-orange-400', border: 'border-orange-500' },
    ];

    const settingsNav = { name: 'Settings', href: '/settings', icon: Settings, accentText: 'text-gray-300', accentBg: 'bg-gray-400', border: 'border-gray-500' };

    const activeNav = [...navigation, settingsNav].find(n => location.pathname === n.href) || { border: 'border-white/5' };

    return (
        <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans selection:bg-indigo-500/30 transition-colors">
            {/* Topbar */}
            <header className={`bg-[var(--bg-primary)]/80 backdrop-blur-md sticky top-0 z-50 transition-colors duration-500 border-b ${activeNav.border === 'border-white/5' ? 'border-[var(--border-secondary)]' : `border-b-[3px] ` + activeNav.border}`}>
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        {/* Logo */}
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-900/20">
                                <GraduationCap className="h-6 w-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-lg font-bold text-[var(--text-primary)] tracking-tight">Academic Portal</h1>
                                <p className="text-xs text-[var(--text-secondary)] hidden sm:block font-medium">{user?.name || 'Student'}</p>
                            </div>
                        </div>

                        {/* Desktop Navigation */}
                        <nav className="hidden md:flex items-center gap-1.5 h-full py-3">
                            {navigation.map((item) => {
                                const isActive = location.pathname === item.href;
                                return (
                                    <NavLink
                                        key={item.name}
                                        to={item.href}
                                        className={`relative flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold transition-all duration-200 overflow-hidden ${
                                            isActive
                                                ? 'bg-[var(--brand-primary)] text-white'
                                                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
                                        }`}
                                    >
                                        {isActive && (
                                            <motion.div layoutId="leftAccent" className={`absolute left-0 top-0 bottom-0 w-[3px] ${item.accentBg}`} />
                                        )}
                                        <item.icon className={`h-4 w-4 ${isActive ? item.accentText : ''}`} />
                                        <span>{item.name}</span>
                                    </NavLink>
                                );
                            })}

                            <div className="w-px h-6 bg-[var(--border-primary)] mx-2"></div>

                            {/* Settings */}
                            <NavLink
                                to={settingsNav.href}
                                className={`relative flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold transition-all duration-200 overflow-hidden ${
                                    location.pathname === settingsNav.href
                                        ? 'bg-[var(--brand-primary)] text-white'
                                        : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
                                }`}
                            >
                                {location.pathname === settingsNav.href && <motion.div layoutId="leftAccent" className={`absolute left-0 top-0 bottom-0 w-[3px] ${settingsNav.accentBg}`} />}
                                <settingsNav.icon className={`h-4 w-4 ${location.pathname === settingsNav.href ? settingsNav.accentText : ''}`} />
                                <span className="hidden lg:block">{settingsNav.name}</span>
                            </NavLink>

                            <div className="w-px h-6 bg-[var(--border-primary)] mx-2"></div>

                            {/* Log Out */}
                            <button
                                onClick={logout}
                                className="relative flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold text-[var(--text-secondary)] hover:text-red-500 hover:bg-red-500/10 transition-all duration-200"
                            >
                                <LogOut className="h-4 w-4" />
                                <span className="hidden lg:block">Log Out</span>
                            </button>
                        </nav>

                        {/* Mobile Menu Button */}
                        <button
                            onClick={() => setMobileMenuOpen(true)}
                            className="md:hidden p-2 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-colors"
                        >
                            <Menu className="h-5 w-5" />
                        </button>
                    </div>
                </div>
            </header>

            {/* Mobile Drawer (Slide-out via AnimatePresence) */}
            <AnimatePresence>
                {mobileMenuOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setMobileMenuOpen(false)}
                            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] md:hidden"
                        />
                        <motion.div
                            initial={{ x: '100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '100%' }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="fixed right-0 top-0 bottom-0 w-3/4 max-w-sm bg-[var(--bg-elevated)] border-l border-[var(--border-primary)] z-[70] p-6 shadow-2xl flex flex-col md:hidden"
                        >
                            <div className="flex justify-between items-center mb-8">
                                <h2 className="text-xl font-bold text-[var(--text-primary)] tracking-tight">Navigation</h2>
                                <button onClick={() => setMobileMenuOpen(false)} className="p-2 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors">
                                    <X className="h-6 w-6" />
                                </button>
                            </div>
                            
                            <nav className="flex flex-col gap-2">
                                {navigation.map((item) => {
                                    const isActive = location.pathname === item.href;
                                    return (
                                        <NavLink
                                            key={item.name}
                                            to={item.href}
                                            className={`relative flex items-center gap-3 px-4 py-3 rounded-xl text-base font-semibold transition-all duration-200 overflow-hidden ${
                                                isActive
                                                    ? 'bg-[var(--brand-primary)] text-white'
                                                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
                                            }`}
                                        >
                                            {isActive && <div className={`absolute left-0 top-0 bottom-0 w-1 ${item.accentBg}`} />}
                                            <item.icon className={`h-5 w-5 ${isActive ? item.accentText : ''}`} />
                                            <span>{item.name}</span>
                                        </NavLink>
                                    );
                                })}

                                <div className="h-px w-full bg-[var(--border-primary)] my-4"></div>

                                <NavLink
                                    to={settingsNav.href}
                                    className={`relative flex items-center gap-3 px-4 py-3 rounded-xl text-base font-semibold transition-all duration-200 overflow-hidden ${
                                        location.pathname === settingsNav.href
                                            ? 'bg-[var(--brand-primary)] text-white'
                                            : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
                                    }`}
                                >
                                    {location.pathname === settingsNav.href && <div className={`absolute left-0 top-0 bottom-0 w-1 ${settingsNav.accentBg}`} />}
                                    <settingsNav.icon className={`h-5 w-5 ${location.pathname === settingsNav.href ? settingsNav.accentText : ''}`} />
                                    <span>{settingsNav.name}</span>
                                </NavLink>

                                <div className="h-px w-full bg-[var(--border-primary)] my-4"></div>

                                {/* Log Out */}
                                <button
                                    onClick={() => {
                                        setMobileMenuOpen(false);
                                        logout();
                                    }}
                                    className="relative flex items-center gap-3 px-4 py-3 rounded-xl text-base font-semibold text-[var(--text-secondary)] hover:text-red-500 hover:bg-red-500/10 transition-all duration-200 text-left w-full"
                                >
                                    <LogOut className="h-5 w-5" />
                                    <span>Log Out</span>
                                </button>
                            </nav>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-10">
                <Outlet />
            </main>
        </div>
    );
};

export default Layout;
