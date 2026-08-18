import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { LogIn, User, Lock, AlertCircle, Zap } from 'lucide-react';

const Login = () => {
    const navigate = useNavigate();
    const [studentId, setStudentId] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        try {
            await login(studentId, password);
        } catch (err: any) {
            setError(err.message || 'Invalid credentials');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div
            className="min-h-screen flex items-center justify-center p-4"
            style={{ background: 'var(--bg-page)', position: 'relative', overflow: 'hidden' }}
        >
            {/* Background glow blobs */}
            <div
                style={{
                    position: 'absolute', top: '-10%', left: '-10%',
                    width: '500px', height: '500px', borderRadius: '50%',
                    background: 'radial-gradient(circle, rgba(0,212,180,0.06) 0%, transparent 70%)',
                    pointerEvents: 'none',
                }}
            />
            <div
                style={{
                    position: 'absolute', bottom: '-10%', right: '-10%',
                    width: '400px', height: '400px', borderRadius: '50%',
                    background: 'radial-gradient(circle, rgba(59,130,246,0.06) 0%, transparent 70%)',
                    pointerEvents: 'none',
                }}
            />

            <div className="max-w-md w-full animate-fade-in-up">
                {/* Header */}
                <div className="text-center mb-8">
                    <div
                        className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-5"
                        style={{
                            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                            boxShadow: '0 0 40px rgba(99,102,241,0.4)',
                        }}
                    >
                        <Zap className="w-8 h-8" style={{ color: '#ffffff' }} />
                    </div>
                    <p className="section-label mb-2">Career Intelligence Portal</p>
                    <h1
                        className="text-3xl font-black tracking-tight mb-2"
                        style={{ color: 'var(--text-primary)' }}
                    >
                        Welcome back
                    </h1>
                    <p style={{ color: 'var(--text-tertiary)', fontSize: '0.9375rem' }}>
                        Sign in to your career dashboard
                    </p>
                </div>

                {/* Form Card */}
                <div
                    className="rounded-2xl p-8"
                    style={{
                        background: 'var(--bg-surface)',
                        border: '1px solid var(--border-primary)',
                        boxShadow: '0 24px 48px rgba(0,0,0,0.4)',
                    }}
                >
                    <form onSubmit={handleSubmit} className="space-y-5">
                        {error && (
                            <div
                                className="flex items-center gap-2.5 p-3.5 rounded-xl"
                                style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}
                            >
                                <AlertCircle className="h-4 w-4 flex-shrink-0" style={{ color: '#f87171' }} />
                                <p className="text-sm" style={{ color: '#f87171' }}>{error}</p>
                            </div>
                        )}

                        <div>
                            <label
                                htmlFor="studentId"
                                className="block text-sm font-semibold mb-2"
                                style={{ color: 'var(--text-secondary)' }}
                            >
                                User ID
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                    <User className="h-4 w-4" style={{ color: 'var(--text-tertiary)' }} />
                                </div>
                                <input
                                    id="studentId"
                                    type="text"
                                    required
                                    value={studentId}
                                    onChange={(e) => setStudentId(e.target.value)}
                                    placeholder="S00001"
                                    className="block w-full pl-10 pr-4 py-3 rounded-xl text-sm transition-all"
                                    style={{
                                        background: 'rgba(255,255,255,0.04)',
                                        border: '1px solid var(--border-primary)',
                                        color: 'var(--text-primary)',
                                        outline: 'none',
                                    }}
                                    onFocus={(e) => {
                                        e.target.style.borderColor = 'rgba(0,212,180,0.5)';
                                        e.target.style.boxShadow = '0 0 0 3px rgba(0,212,180,0.08)';
                                    }}
                                    onBlur={(e) => {
                                        e.target.style.borderColor = 'var(--border-primary)';
                                        e.target.style.boxShadow = 'none';
                                    }}
                                />
                            </div>
                        </div>

                        <div>
                            <label
                                htmlFor="password"
                                className="block text-sm font-semibold mb-2"
                                style={{ color: 'var(--text-secondary)' }}
                            >
                                Password
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                    <Lock className="h-4 w-4" style={{ color: 'var(--text-tertiary)' }} />
                                </div>
                                <input
                                    id="password"
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    className="block w-full pl-10 pr-4 py-3 rounded-xl text-sm transition-all"
                                    style={{
                                        background: 'rgba(255,255,255,0.04)',
                                        border: '1px solid var(--border-primary)',
                                        color: 'var(--text-primary)',
                                        outline: 'none',
                                    }}
                                    onFocus={(e) => {
                                        e.target.style.borderColor = 'rgba(0,212,180,0.5)';
                                        e.target.style.boxShadow = '0 0 0 3px rgba(0,212,180,0.08)';
                                    }}
                                    onBlur={(e) => {
                                        e.target.style.borderColor = 'var(--border-primary)';
                                        e.target.style.boxShadow = 'none';
                                    }}
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-bold text-sm transition-all"
                            style={{
                                    background: isLoading ? 'rgba(99,102,241,0.5)' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                                    color: '#ffffff',
                                    boxShadow: '0 4px 20px rgba(99,102,241,0.35)',
                                    cursor: isLoading ? 'not-allowed' : 'pointer',
                                }}
                        >
                            {isLoading ? (
                                <>
                                    <div
                                        className="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin"
                                        style={{ borderColor: '#0a0e1a', borderTopColor: 'transparent' }}
                                    />
                                    <span>Signing in...</span>
                                </>
                            ) : (
                                <>
                                    <LogIn className="w-4 h-4" />
                                    <span>Sign In</span>
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-5 text-center">
                        <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
                            New user?{' '}
                            <button
                                onClick={() => navigate('/register')}
                                className="font-semibold transition-colors"
                                style={{ color: 'var(--brand-primary)' }}
                            >
                                Register here
                            </button>
                        </p>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default Login;
