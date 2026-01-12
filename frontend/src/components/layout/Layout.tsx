import React, { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { Home, TrendingUp, BookOpen, Settings, Menu, X, GraduationCap } from 'lucide-react';

const Layout = () => {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const location = useLocation();

    // Student-focused navigation
    const navigation = [
        { name: 'Dashboard', href: '/', icon: Home },
        { name: 'My Performance', href: '/performance', icon: TrendingUp },
        { name: 'Subjects', href: '/subjects', icon: BookOpen },
        { name: 'Settings', href: '/settings', icon: Settings },
    ];

    // Hardcoded student info (in a real app, this would come from auth context)
    const studentName = 'Priya Sharma';
    const studentBranch = 'Electronics Engineering';

    return (
        <div className="min-h-screen bg-[var(--bg-primary)]">
            {/* Mobile Header */}
            <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-[var(--bg-secondary)]/95 backdrop-blur-sm border-b border-[var(--border-primary)]">
                <div className="flex items-center justify-between px-4 py-3">
                    <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-[var(--brand-primary)] to-[var(--brand-secondary)] flex items-center justify-center">
                            <GraduationCap className="h-5 w-5 text-white" />
                        </div>
                        <span className="text-lg font-semibold text-[var(--text-primary)]">Academic Portal</span>
                    </div>
                    <button
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="p-2 rounded-lg hover:bg-[var(--bg-tertiary)] transition-colors"
                    >
                        {sidebarOpen ? (
                            <X className="h-5 w-5 text-[var(--text-secondary)]" />
                        ) : (
                            <Menu className="h-5 w-5 text-[var(--text-secondary)]" />
                        )}
                    </button>
                </div>
            </div>

            {/* Mobile Sidebar Overlay */}
            {sidebarOpen && (
                <div
                    className="lg:hidden fixed inset-0 bg-black/50 z-40 backdrop-blur-sm"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`
          fixed top-0 left-0 bottom-0 z-40
          w-64 bg-[var(--bg-secondary)] border-r border-[var(--border-primary)]
          transition-transform duration-300 ease-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0
        `}
            >
                <div className="flex flex-col h-full">
                    {/* Logo */}
                    <div className="h-16 flex items-center px-6 border-b border-[var(--border-primary)]">
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-[var(--brand-primary)] to-[var(--brand-secondary)] flex items-center justify-center shadow-lg">
                                <GraduationCap className="h-6 w-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-base font-bold text-[var(--text-primary)] leading-tight">
                                    Academic Portal
                                </h1>
                                <p className="text-xs text-[var(--text-tertiary)]">Student Dashboard</p>
                            </div>
                        </div>
                    </div>

                    {/* Student Profile Card */}
                    <div className="px-4 py-6 border-b border-[var(--border-primary)]">
                        <div className="flex items-center gap-3">
                            <div className="h-12 w-12 rounded-full bg-gradient-to-br from-[var(--brand-primary)] to-[var(--brand-secondary)] flex items-center justify-center text-lg font-bold text-white shadow-md">
                                {studentName.split(' ').map(n => n[0]).join('')}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-semibold text-[var(--text-primary)] truncate">{studentName}</p>
                                <p className="text-xs text-[var(--text-tertiary)] truncate">{studentBranch}</p>
                            </div>
                        </div>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-3 py-6 space-y-1">
                        {navigation.map((item) => {
                            const isActive = location.pathname === item.href;

                            return (
                                <NavLink
                                    key={item.name}
                                    to={item.href}
                                    onClick={() => setSidebarOpen(false)}
                                    className={`
                    flex items-center gap-3 px-4 py-3 rounded-lg
                    font-medium text-sm transition-all duration-200
                    ${isActive
                                            ? 'bg-[var(--brand-primary)]/10 text-[var(--brand-primary)] shadow-sm'
                                            : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]'
                                        }
                  `}
                                >
                                    <item.icon className="h-5 w-5" />
                                    <span>{item.name}</span>
                                    {isActive && (
                                        <div className="ml-auto h-1.5 w-1.5 rounded-full bg-[var(--brand-primary)]" />
                                    )}
                                </NavLink>
                            );
                        })}
                    </nav>

                    {/* Footer */}
                    <div className="p-4 border-t border-[var(--border-primary)]">
                        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4">
                            <p className="text-xs text-[var(--text-tertiary)] mb-1">Academic Year</p>
                            <p className="text-sm font-semibold text-[var(--text-primary)]">2024-2025</p>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <div className="lg:pl-64">
                <main className="min-h-screen pt-16 lg:pt-0">
                    <div className="page-content">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
};

export default Layout;
