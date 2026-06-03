import { useState, useEffect } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
    Home, Settings, Menu, X, LogOut, Bell,
    Target, Map, Cpu, TrendingUp, LayoutDashboard
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';

// ─── Nav Items ────────────────────────────────────────────────────────────────

const NAV_ITEMS = [
    { name: 'Dashboard', href: '/',         icon: LayoutDashboard },
    { name: 'Skills',    href: '/skills',   icon: Target },
    { name: 'Roadmap',   href: '/roadmap',  icon: Map },
    { name: 'Interview', href: '/interview',icon: Cpu },
    { name: 'Growth',    href: '/settings', icon: TrendingUp },
];

// ─── Sidebar NavLink ──────────────────────────────────────────────────────────

function SideNavItem({ item, collapsed = false }: { item: typeof NAV_ITEMS[0]; collapsed?: boolean }) {
    return (
        <NavLink
            to={item.href}
            end={item.href === '/'}
            className={({ isActive }) =>
                `side-nav-item ${isActive ? 'active' : ''}`
            }
        >
            {({ isActive }) => (
                <>
                    <item.icon
                        className={`h-4 w-4 flex-shrink-0 transition-all duration-150 ${
                            isActive ? 'text-[var(--brand-primary)]' : 'text-[var(--text-tertiary)]'
                        }`}
                    />
                    {!collapsed && <span>{item.name}</span>}
                </>
            )}
        </NavLink>
    );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────

function Sidebar({ collapsed = false, user, onLogout }: {
    collapsed?: boolean;
    user: any;
    onLogout: () => void;
}) {
    return (
        <aside
            className={`
                fixed left-0 top-0 bottom-0 z-40
                flex flex-col
                transition-all duration-200
                ${collapsed ? 'w-16' : 'w-[220px]'}
            `}
            style={{
                background: 'var(--bg-sidebar)',
                borderRight: '1px solid var(--border-primary)',
            }}
        >
            {/* Logo */}
            <div className={`px-4 pt-6 pb-5 ${collapsed ? 'px-3 items-center' : ''}`}>
                <div className="flex items-center gap-2.5">
                    <div
                        className="h-8 w-8 rounded-xl flex items-center justify-center flex-shrink-0"
                        style={{
                            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                            boxShadow: '0 0 16px rgba(99,102,241,0.35)',
                        }}
                    >
                        <span style={{ color: '#ffffff', fontWeight: 900, fontSize: '12px' }}>CI</span>
                    </div>
                    {!collapsed && (
                        <div className="min-w-0">
                            <p style={{ color: 'var(--text-primary)', fontWeight: 800, fontSize: '0.875rem', letterSpacing: '-0.02em' }}>
                                Career Intel
                            </p>
                            <p style={{ fontSize: '0.6875rem', color: 'var(--brand-primary)', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                                Portal
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* Active Intelligence label */}
            {!collapsed && (
                <div className="px-4 mb-3">
                    <div
                        className="px-2.5 py-1.5 rounded-lg"
                        style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.12)' }}
                    >
                        <p className="section-label">Active Intelligence</p>
                    </div>
                </div>
            )}

            {/* Main Nav */}
            <nav className={`flex-1 px-3 space-y-0.5 overflow-y-auto py-1`}>
                {NAV_ITEMS.map(item => (
                    <SideNavItem key={item.href} item={item} collapsed={collapsed} />
                ))}
            </nav>

            {/* Divider */}
            <div className="mx-3 my-2 divider" />

            {/* Bottom Section */}
            <div className="px-3 pb-2 space-y-0.5">
                <NavLink
                    to="/settings"
                    className={({ isActive }) => `side-nav-item ${isActive ? 'active' : ''}`}
                >
                    {({ isActive }) => (
                        <>
                            <Settings className={`h-4 w-4 flex-shrink-0 ${isActive ? 'text-[var(--brand-primary)]' : 'text-[var(--text-tertiary)]'}`} />
                            {!collapsed && <span>Settings</span>}
                        </>
                    )}
                </NavLink>
                <button
                    onClick={onLogout}
                    className="side-nav-item w-full text-left"
                    style={{ color: 'var(--text-tertiary)' }}
                >
                    <LogOut className="h-4 w-4 flex-shrink-0" />
                    {!collapsed && <span>Log out</span>}
                </button>
            </div>

            {/* User Profile */}
            {!collapsed && user && (
                <div
                    className="mx-3 mb-4 p-3 rounded-xl flex items-center gap-2.5"
                    style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-primary)' }}
                >
                    <div
                        className="h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0"
                        style={{
                            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                            boxShadow: '0 0 10px rgba(99,102,241,0.3)',
                        }}
                    >
                        <span style={{ color: '#ffffff', fontWeight: 800, fontSize: '11px' }}>
                            {user?.name?.[0]?.toUpperCase() || 'U'}
                        </span>
                    </div>
                    <div className="min-w-0 flex-1">
                        <p style={{ color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600 }} className="truncate">
                            {user?.name || 'Student'}
                        </p>
                        <p style={{ color: 'var(--text-tertiary)', fontSize: '0.6875rem' }} className="truncate">
                            {user?.branch || 'B.Tech'}
                        </p>
                    </div>
                </div>
            )}
        </aside>
    );
}

// ─── Top Bar ─────────────────────────────────────────────────────────────────

function TopBar({ onMobileMenuToggle, user }: { onMobileMenuToggle: () => void; user: any }) {
    return (
        <header
            className="sticky top-0 z-30 h-14 flex items-center"
            style={{
                background: 'rgba(10, 14, 26, 0.85)',
                backdropFilter: 'blur(16px)',
                borderBottom: '1px solid var(--border-primary)',
            }}
        >
            <div className="flex-1 flex items-center gap-3 px-5">
                {/* Mobile toggle */}
                <button
                    onClick={onMobileMenuToggle}
                    className="lg:hidden p-1.5 rounded-lg transition-colors"
                    style={{ color: 'var(--text-secondary)' }}
                >
                    <Menu className="h-5 w-5" />
                </button>

                {/* Mobile Logo */}
                <div className="lg:hidden flex items-center gap-2">
                    <div
                        className="h-7 w-7 rounded-lg flex items-center justify-center"
                        style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
                    >
                        <span style={{ color: '#ffffff', fontWeight: 900, fontSize: '10px' }}>CI</span>
                    </div>
                    <span style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.875rem' }}>
                        Career Intelligence
                    </span>
                </div>

                {/* Search — desktop only */}
                <div className="hidden lg:flex flex-1 max-w-sm">
                    <div className="relative w-full">
                        <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24" style={{ color: 'var(--text-tertiary)' }}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35m0 0A7 7 0 1116.65 16.65z" />
                        </svg>
                        <input
                            type="text"
                            placeholder="Search insights..."
                            className="w-full pl-9 pr-4 py-2 rounded-xl text-sm transition-all"
                            style={{
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid var(--border-primary)',
                                color: 'var(--text-primary)',
                                outline: 'none',
                            }}
                        />
                    </div>
                </div>
            </div>

            {/* Right side */}
            <div className="flex items-center gap-1 pr-5">
                <button
                    className="p-2 rounded-xl transition-colors relative"
                    style={{ color: 'var(--text-secondary)' }}
                >
                    <Bell className="h-5 w-5" />
                    <span
                        className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full"
                        style={{ background: 'var(--brand-primary)', boxShadow: '0 0 6px rgba(99,102,241,0.7)' }}
                    />
                </button>
                <div
                    className="h-8 w-8 rounded-full flex items-center justify-center ml-1 cursor-pointer"
                    style={{
                        background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                        boxShadow: '0 0 12px rgba(99,102,241,0.3)',
                    }}
                >
                    <span style={{ color: '#0a0e1a', fontWeight: 800, fontSize: '11px' }}>
                        {user?.name?.[0]?.toUpperCase() || 'U'}
                    </span>
                </div>
            </div>
        </header>
    );
}

// ─── Bottom Navigation (Mobile) ───────────────────────────────────────────────

function BottomNav() {
    const location = useLocation();
    const BOTTOM_ITEMS = [
        { name: 'Dashboard', href: '/',         icon: LayoutDashboard },
        { name: 'Skills',    href: '/skills',   icon: Target },
        { name: 'Jobs',      href: '/roadmap',  icon: Map },
        { name: 'Growth',    href: '/interview',icon: TrendingUp },
    ];

    return (
        <nav className="bottom-nav lg:hidden">
            {BOTTOM_ITEMS.map((item) => {
                const isActive = item.href === '/'
                    ? location.pathname === '/'
                    : location.pathname.startsWith(item.href);
                return (
                    <NavLink
                        key={item.href}
                        to={item.href}
                        end={item.href === '/'}
                        className={`bottom-nav-item ${isActive ? 'active' : ''}`}
                    >
                        <item.icon className="h-5 w-5" />
                        <span>{item.name}</span>
                    </NavLink>
                );
            })}
        </nav>
    );
}

// ─── Layout ───────────────────────────────────────────────────────────────────

const Layout = () => {
    const [mobileOpen, setMobileOpen] = useState(false);
    const location = useLocation();
    const { user, logout } = useAuth();

    useEffect(() => { setMobileOpen(false); }, [location.pathname]);

    return (
        <div className="min-h-screen flex" style={{ background: 'var(--bg-page)' }}>
            {/* Desktop Sidebar */}
            <div className="hidden lg:block w-[220px] flex-shrink-0">
                <Sidebar user={user} onLogout={logout} />
            </div>

            {/* Mobile Drawer Overlay */}
            <AnimatePresence>
                {mobileOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setMobileOpen(false)}
                            className="fixed inset-0 z-50 lg:hidden"
                            style={{ background: 'rgba(0,0,0,0.7)' }}
                        />
                        <motion.div
                            initial={{ x: '-100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '-100%' }}
                            transition={{ type: 'spring', damping: 28, stiffness: 220 }}
                            className="fixed left-0 top-0 bottom-0 z-50 lg:hidden"
                        >
                            <div className="relative">
                                <button
                                    onClick={() => setMobileOpen(false)}
                                    className="absolute top-4 right-[-44px] p-2 rounded-full"
                                    style={{ background: 'var(--bg-card)', color: 'var(--text-secondary)', border: '1px solid var(--border-primary)' }}
                                >
                                    <X className="h-4 w-4" />
                                </button>
                                <Sidebar user={user} onLogout={logout} />
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            {/* Main panel */}
            <div className="flex-1 flex flex-col min-w-0">
                <TopBar onMobileMenuToggle={() => setMobileOpen(v => !v)} user={user} />

                <main className="flex-1 px-4 md:px-6 py-6 max-w-[1280px] mx-auto w-full pb-24 lg:pb-6">
                    <Outlet />
                </main>
            </div>

            {/* Mobile Bottom Nav */}
            <BottomNav />
        </div>
    );
};

export default Layout;
