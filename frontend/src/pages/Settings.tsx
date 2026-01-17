import { User, Bell, Lock, Globe, Moon, Mail } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

const Settings = () => {
    const { user } = useAuth();
    const { theme, toggleTheme } = useTheme();

    // Get user initials
    const getInitials = (name?: string) => {
        if (!name) return 'U';
        const parts = name.split(' ');
        if (parts.length >= 2) {
            return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
        }
        return name[0].toUpperCase();
    };

    // This is a placeholder page for future implementation

    return (
        <div className="space-y-6 animate-slide-up max-w-4xl mx-auto">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-2">Settings</h1>
                <p className="text-lg text-[var(--text-secondary)]">
                    Manage your account and preferences
                </p>
            </div>

            {/* Profile Settings */}
            <Card variant="elevated">
                <CardHeader>
                    <CardTitle>Profile Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center gap-4 p-4 bg-[var(--bg-tertiary)] rounded-lg">
                        <div className="h-16 w-16 rounded-full bg-gradient-to-br from-[var(--brand-primary)] to-[var(--brand-secondary)] flex items-center justify-center text-2xl font-bold text-white shadow-lg">
                            {getInitials(user?.name)}
                        </div>
                        <div className="flex-1">
                            <p className="font-semibold text-[var(--text-primary)]">{user?.name || 'Student'}</p>
                            <p className="text-sm text-[var(--text-secondary)]">{user?.branch || 'N/A'}</p>
                            <p className="text-xs text-[var(--text-tertiary)]">Student ID: {user?.student_id || 'N/A'}</p>
                        </div>
                        <Badge variant="success">Active</Badge>
                    </div>

                    <div className="space-y-3">
                        <div className="flex items-center justify-between p-3 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors cursor-not-allowed opacity-60">
                            <div className="flex items-center gap-3">
                                <Mail className="h-5 w-5 text-[var(--text-tertiary)]" />
                                <div>
                                    <p className="text-sm font-medium text-[var(--text-primary)]">Email</p>
                                    <p className="text-xs text-[var(--text-secondary)]">{user?.email || 'N/A'}</p>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center justify-between p-3 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors cursor-not-allowed opacity-60">
                            <div className="flex items-center gap-3">
                                <User className="h-5 w-5 text-[var(--text-tertiary)]" />
                                <div>
                                    <p className="text-sm font-medium text-[var(--text-primary)]">Semester</p>
                                    <p className="text-xs text-[var(--text-secondary)]">{user?.semester ? `${user.semester}th Semester` : 'N/A'}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Preferences */}
            <Card variant="elevated">
                <CardHeader>
                    <CardTitle>Preferences</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    <div className="flex items-center justify-between p-3 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors cursor-not-allowed opacity-60">
                        <div className="flex items-center gap-3">
                            <Bell className="h-5 w-5 text-[var(--text-tertiary)]" />
                            <div>
                                <p className="text-sm font-medium text-[var(--text-primary)]">Notifications</p>
                                <p className="text-xs text-[var(--text-secondary)]">Manage notification preferences</p>
                            </div>
                        </div>
                        <Badge variant="info" size="sm">On</Badge>
                    </div>

                    {/* Dark Mode Toggle - Now Functional */}
                    <div
                        onClick={toggleTheme}
                        className="flex items-center justify-between p-3 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors cursor-pointer"
                    >
                        <div className="flex items-center gap-3">
                            <Moon className="h-5 w-5 text-[var(--text-tertiary)]" />
                            <div>
                                <p className="text-sm font-medium text-[var(--text-primary)]">Dark Mode</p>
                                <p className="text-xs text-[var(--text-secondary)]">
                                    {theme === 'dark' ? 'Currently enabled' : 'Currently disabled'}
                                </p>
                            </div>
                        </div>
                        <Badge variant={theme === 'dark' ? 'success' : 'default'} size="sm">
                            {theme === 'dark' ? 'Enabled' : 'Disabled'}
                        </Badge>
                    </div>

                    <div className="flex items-center justify-between p-3 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors cursor-not-allowed opacity-60">
                        <div className="flex items-center gap-3">
                            <Globe className="h-5 w-5 text-[var(--text-tertiary)]" />
                            <div>
                                <p className="text-sm font-medium text-[var(--text-primary)]">Language</p>
                                <p className="text-xs text-[var(--text-secondary)]">English (US)</p>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Security */}
            <Card variant="elevated">
                <CardHeader>
                    <CardTitle>Security</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    <div className="flex items-center justify-between p-3 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors cursor-not-allowed opacity-60">
                        <div className="flex items-center gap-3">
                            <Lock className="h-5 w-5 text-[var(--text-tertiary)]" />
                            <div>
                                <p className="text-sm font-medium text-[var(--text-primary)]">Change Password</p>
                                <p className="text-xs text-[var(--text-secondary)]">Update your account password</p>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Notice */}
            <div className="bg-[var(--bg-tertiary)]/50 border border-[var(--border-secondary)] rounded-lg p-4">
                <p className="text-sm text-[var(--text-secondary)] text-center">
                    Settings functionality will be available in a future update
                </p>
            </div>
        </div>
    );
};

export default Settings;
