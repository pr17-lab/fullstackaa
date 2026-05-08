import { useState } from 'react';
import {
    User, Lock, Moon, Mail, BadgeCheck,
    Pencil, Save, X, KeyRound, Eye, EyeOff,
    ShieldCheck, CheckCircle2, AlertCircle,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { PageTransition } from '../components/layout/PageTransition';
import { ProfileService } from '../services/api';

// ─── tiny toast ───────────────────────────────────────────────────────────────
type ToastVariant = 'success' | 'error';
interface ToastMsg { variant: ToastVariant; text: string }

const Toast = ({ toast, onClose }: { toast: ToastMsg; onClose: () => void }) => (
    <div
        className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-4 rounded-xl shadow-2xl border animate-slide-up
            ${toast.variant === 'success'
                ? 'bg-[var(--bg-secondary)] border-[var(--accent-emerald)]/40 text-[var(--accent-emerald)]'
                : 'bg-[var(--bg-secondary)] border-red-500/40 text-red-400'}`}
        style={{ minWidth: 280 }}
    >
        {toast.variant === 'success'
            ? <CheckCircle2 className="h-5 w-5 shrink-0" />
            : <AlertCircle className="h-5 w-5 shrink-0" />}
        <p className="text-sm font-medium flex-1">{toast.text}</p>
        <button onClick={onClose} className="opacity-60 hover:opacity-100 transition-opacity">
            <X className="h-4 w-4" />
        </button>
    </div>
);

// ─── field row ────────────────────────────────────────────────────────────────
const FieldRow = ({
    label, value, editing, children,
}: { label: string; value: string; editing: boolean; children: React.ReactNode }) => (
    <div className="flex items-center justify-between py-3">
        <div>
            <p className="text-sm font-medium text-[var(--text-primary)]">{label}</p>
            {!editing && <p className="text-xs text-[var(--text-secondary)] mt-0.5">{value}</p>}
        </div>
        {editing && <div className="w-56">{children}</div>}
    </div>
);

// ─── main component ───────────────────────────────────────────────────────────
const Settings = () => {
    const { user, updateUser } = useAuth();
    const { theme, toggleTheme } = useTheme();

    // ── profile edit state ────────────────────────────────────────────────────
    const [editingProfile, setEditingProfile] = useState(false);
    const [profileName, setProfileName] = useState(user?.name || '');
    const [profileSemester, setProfileSemester] = useState<number>(user?.semester || 1);
    const [profileLoading, setProfileLoading] = useState(false);

    // ── password state ────────────────────────────────────────────────────────
    const [currentPwd, setCurrentPwd] = useState('');
    const [newPwd, setNewPwd] = useState('');
    const [confirmPwd, setConfirmPwd] = useState('');
    const [showCurrent, setShowCurrent] = useState(false);
    const [showNew, setShowNew] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);
    const [pwdLoading, setPwdLoading] = useState(false);

    // ── toast ─────────────────────────────────────────────────────────────────
    const [toast, setToast] = useState<ToastMsg | null>(null);
    const showToast = (variant: ToastVariant, text: string) => {
        setToast({ variant, text });
        setTimeout(() => setToast(null), 4000);
    };

    // ── helpers ───────────────────────────────────────────────────────────────
    const getInitials = (name?: string) => {
        if (!name) return 'U';
        const parts = name.split(' ');
        return parts.length >= 2
            ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
            : name[0].toUpperCase();
    };

    const cancelProfileEdit = () => {
        setProfileName(user?.name || '');
        setProfileSemester(user?.semester || 1);
        setEditingProfile(false);
    };

    // password strength: needs ≥8 chars + 1 digit
    const pwdStrong = newPwd.length >= 8 && /\d/.test(newPwd);
    const pwdMatch = newPwd === confirmPwd && confirmPwd.length > 0;

    // ── handlers ──────────────────────────────────────────────────────────────
    const handleSaveProfile = async () => {
        if (!profileName.trim()) {
            showToast('error', 'Name cannot be empty');
            return;
        }
        setProfileLoading(true);
        try {
            const updated = await ProfileService.updateProfile({
                name: profileName.trim(),
                semester: profileSemester,
            });
            updateUser({ name: updated.name, semester: updated.semester });
            setEditingProfile(false);
            showToast('success', 'Profile updated successfully!');
        } catch (err: any) {
            showToast('error', err.message || 'Failed to update profile');
        } finally {
            setProfileLoading(false);
        }
    };

    const handleChangePassword = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!pwdStrong) {
            showToast('error', 'New password must be ≥8 characters and contain a number');
            return;
        }
        if (!pwdMatch) {
            showToast('error', 'Passwords do not match');
            return;
        }
        setPwdLoading(true);
        try {
            await ProfileService.changePassword(currentPwd, newPwd);
            setCurrentPwd('');
            setNewPwd('');
            setConfirmPwd('');
            showToast('success', 'Password changed successfully!');
        } catch (err: any) {
            showToast('error', err.message || 'Failed to change password');
        } finally {
            setPwdLoading(false);
        }
    };

    // ── shared input class ────────────────────────────────────────────────────
    const inputCls =
        'w-full bg-[var(--bg-tertiary)] border border-[var(--border-primary)] rounded-lg px-3 py-2 ' +
        'text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] ' +
        'focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)]/50 transition';

    // ─── render ───────────────────────────────────────────────────────────────
    return (
        <PageTransition className="space-y-6 max-w-4xl mx-auto">
            {toast && <Toast toast={toast} onClose={() => setToast(null)} />}

            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-2">Settings</h1>
                <p className="text-lg text-[var(--text-secondary)]">Manage your account and preferences</p>
            </div>

            {/* ── Profile Information ─────────────────────────────────────── */}
            <Card variant="elevated">
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle>Profile Information</CardTitle>
                        {!editingProfile ? (
                            <Button
                                id="btn-edit-profile"
                                variant="secondary"
                                size="sm"
                                leftIcon={<Pencil className="h-3.5 w-3.5" />}
                                onClick={() => { setProfileName(user?.name || ''); setProfileSemester(user?.semester || 1); setEditingProfile(true); }}
                            >
                                Edit
                            </Button>
                        ) : (
                            <div className="flex items-center gap-2">
                                <Button
                                    id="btn-cancel-profile"
                                    variant="ghost"
                                    size="sm"
                                    leftIcon={<X className="h-3.5 w-3.5" />}
                                    onClick={cancelProfileEdit}
                                    disabled={profileLoading}
                                >
                                    Cancel
                                </Button>
                                <Button
                                    id="btn-save-profile"
                                    variant="primary"
                                    size="sm"
                                    leftIcon={<Save className="h-3.5 w-3.5" />}
                                    onClick={handleSaveProfile}
                                    disabled={profileLoading}
                                >
                                    {profileLoading ? 'Saving…' : 'Save'}
                                </Button>
                            </div>
                        )}
                    </div>
                </CardHeader>
                <CardContent className="space-y-1">
                    {/* Avatar row */}
                    <div className="flex items-center gap-4 p-4 bg-[var(--bg-tertiary)] rounded-xl mb-4">
                        <div className="h-16 w-16 rounded-full bg-gradient-to-br from-[var(--brand-primary)] to-[var(--brand-secondary)] flex items-center justify-center text-2xl font-bold text-white shadow-lg shrink-0">
                            {getInitials(user?.name)}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="font-semibold text-[var(--text-primary)] truncate">{user?.name || 'Student'}</p>
                            <p className="text-sm text-[var(--text-secondary)]">{user?.branch || 'N/A'}</p>
                            <p className="text-xs text-[var(--text-tertiary)]">ID: {user?.student_id || 'N/A'}</p>
                        </div>
                        <Badge variant="success">Active</Badge>
                    </div>

                    <div className="divide-y divide-[var(--border-primary)]">
                        {/* Email — always read-only */}
                        <div className="flex items-center gap-3 py-3 opacity-60">
                            <Mail className="h-5 w-5 text-[var(--text-tertiary)] shrink-0" />
                            <div className="flex-1">
                                <p className="text-sm font-medium text-[var(--text-primary)]">Email</p>
                                <p className="text-xs text-[var(--text-secondary)]">{user?.email || 'N/A'}</p>
                            </div>
                            <Badge variant="default" size="sm">Read-only</Badge>
                        </div>

                        {/* Branch — read-only */}
                        <div className="flex items-center gap-3 py-3 opacity-60">
                            <BadgeCheck className="h-5 w-5 text-[var(--text-tertiary)] shrink-0" />
                            <div className="flex-1">
                                <p className="text-sm font-medium text-[var(--text-primary)]">Branch / Department</p>
                                <p className="text-xs text-[var(--text-secondary)]">{user?.branch || 'N/A'}</p>
                            </div>
                            <Badge variant="default" size="sm">Read-only</Badge>
                        </div>

                        {/* Name — editable */}
                        <div className="flex items-center gap-3 py-3">
                            <User className="h-5 w-5 text-[var(--text-tertiary)] shrink-0" />
                            <FieldRow
                                label="Full Name"
                                value={user?.name || 'N/A'}
                                editing={editingProfile}
                            >
                                <input
                                    id="input-name"
                                    type="text"
                                    value={profileName}
                                    onChange={(e) => setProfileName(e.target.value)}
                                    placeholder="Your full name"
                                    className={inputCls}
                                    maxLength={255}
                                />
                            </FieldRow>
                        </div>

                        {/* Semester — editable */}
                        <div className="flex items-center gap-3 py-3">
                            <ShieldCheck className="h-5 w-5 text-[var(--text-tertiary)] shrink-0" />
                            <FieldRow
                                label="Current Semester"
                                value={user?.semester ? `Semester ${user.semester}` : 'N/A'}
                                editing={editingProfile}
                            >
                                <select
                                    id="select-semester"
                                    value={profileSemester}
                                    onChange={(e) => setProfileSemester(Number(e.target.value))}
                                    className={inputCls}
                                >
                                    {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                                        <option key={s} value={s}>Semester {s}</option>
                                    ))}
                                </select>
                            </FieldRow>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* ── Preferences ────────────────────────────────────────────── */}
            <Card variant="elevated">
                <CardHeader><CardTitle>Preferences</CardTitle></CardHeader>
                <CardContent className="space-y-1">
                    {/* Dark Mode */}
                    <button
                        id="btn-toggle-theme"
                        onClick={toggleTheme}
                        className="w-full flex items-center justify-between p-3 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors"
                    >
                        <div className="flex items-center gap-3">
                            <Moon className="h-5 w-5 text-[var(--text-tertiary)]" />
                            <div className="text-left">
                                <p className="text-sm font-medium text-[var(--text-primary)]">Dark Mode</p>
                                <p className="text-xs text-[var(--text-secondary)]">
                                    {theme === 'dark' ? 'Currently enabled' : 'Currently disabled'}
                                </p>
                            </div>
                        </div>
                        <Badge variant={theme === 'dark' ? 'success' : 'default'} size="sm">
                            {theme === 'dark' ? 'Enabled' : 'Disabled'}
                        </Badge>
                    </button>
                </CardContent>
            </Card>

            {/* ── Security / Change Password ──────────────────────────────── */}
            <Card variant="elevated">
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <Lock className="h-5 w-5 text-[var(--brand-primary)]" />
                        <CardTitle>Security</CardTitle>
                    </div>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-[var(--text-secondary)] mb-5">
                        Choose a strong password with at least 8 characters and one number.
                    </p>

                    <form id="form-change-password" onSubmit={handleChangePassword} className="space-y-4">
                        {/* Current password */}
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wide">
                                Current Password
                            </label>
                            <div className="relative">
                                <input
                                    id="input-current-password"
                                    type={showCurrent ? 'text' : 'password'}
                                    value={currentPwd}
                                    onChange={(e) => setCurrentPwd(e.target.value)}
                                    placeholder="Enter current password"
                                    className={inputCls + ' pr-10'}
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowCurrent((p) => !p)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
                                >
                                    {showCurrent ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                            </div>
                        </div>

                        {/* New password */}
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wide">
                                New Password
                            </label>
                            <div className="relative">
                                <input
                                    id="input-new-password"
                                    type={showNew ? 'text' : 'password'}
                                    value={newPwd}
                                    onChange={(e) => setNewPwd(e.target.value)}
                                    placeholder="Min 8 chars, include a number"
                                    className={inputCls + ' pr-10'}
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowNew((p) => !p)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
                                >
                                    {showNew ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                            </div>
                            {/* strength bar */}
                            {newPwd.length > 0 && (
                                <div className="flex items-center gap-2 mt-1">
                                    <div className="flex-1 h-1.5 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full transition-all duration-300 ${
                                                pwdStrong ? 'bg-[var(--accent-emerald)] w-full' : 'bg-amber-500 w-1/2'
                                            }`}
                                        />
                                    </div>
                                    <span className={`text-xs font-medium ${pwdStrong ? 'text-[var(--accent-emerald)]' : 'text-amber-500'}`}>
                                        {pwdStrong ? 'Strong' : 'Weak'}
                                    </span>
                                </div>
                            )}
                        </div>

                        {/* Confirm password */}
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wide">
                                Confirm New Password
                            </label>
                            <div className="relative">
                                <input
                                    id="input-confirm-password"
                                    type={showConfirm ? 'text' : 'password'}
                                    value={confirmPwd}
                                    onChange={(e) => setConfirmPwd(e.target.value)}
                                    placeholder="Repeat new password"
                                    className={`${inputCls} pr-10 ${
                                        confirmPwd.length > 0
                                            ? pwdMatch
                                                ? 'border-[var(--accent-emerald)]/60'
                                                : 'border-red-500/60'
                                            : ''
                                    }`}
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowConfirm((p) => !p)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
                                >
                                    {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                            </div>
                            {confirmPwd.length > 0 && (
                                <p className={`text-xs mt-1 ${pwdMatch ? 'text-[var(--accent-emerald)]' : 'text-red-400'}`}>
                                    {pwdMatch ? '✓ Passwords match' : '✗ Passwords do not match'}
                                </p>
                            )}
                        </div>

                        <Button
                            id="btn-change-password"
                            type="submit"
                            variant="primary"
                            size="md"
                            leftIcon={<KeyRound className="h-4 w-4" />}
                            disabled={pwdLoading || !currentPwd || !pwdStrong || !pwdMatch}
                            className="w-full mt-2"
                        >
                            {pwdLoading ? 'Updating Password…' : 'Update Password'}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </PageTransition>
    );
};

export default Settings;
