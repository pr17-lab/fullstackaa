import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface User {
    id: string;
    email: string;
    student_id?: string;
    name?: string;
    branch?: string;
    semester?: number;
}

interface AuthContextType {
    user: User | null;
    login: (studentId: string, password: string) => Promise<void>;
    logout: () => void;
    updateUser: (updated: Partial<User>) => void;
    isAuthenticated: boolean;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const navigate = useNavigate();

    // Check authentication on mount
    useEffect(() => {
        fetchCurrentUser();
    }, []);

    const fetchCurrentUser = async () => {
        try {
            const response = await fetch('/api/auth/me', {
                credentials: 'include',
            });

            if (response.ok) {
                const text = await response.text();
                if (text) {
                    const userData = JSON.parse(text);
                    setUser(userData);
                } else {
                    setUser(null);
                }
            } else {
                setUser(null);
            }
        } catch (error) {
            console.error('Failed to fetch user:', error);
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    };

    const login = async (studentId: string, password: string) => {
        const formData = new FormData();
        formData.append('username', studentId);
        formData.append('password', password);

        const response = await fetch('/api/auth/login', {
            method: 'POST',
            body: formData,
            credentials: 'include',
        });

        if (!response.ok) {
            let errorMessage = 'Login failed';
            try {
                const text = await response.text();
                if (text) {
                    const data = JSON.parse(text);
                    errorMessage = data.detail || data.message || errorMessage;
                } else {
                    errorMessage = `Server response empty (${response.status}). The server may be starting up.`;
                }
            } catch {
                if (response.status === 502 || response.status === 504) {
                    errorMessage = 'Backend server is waking up (cold start). Please wait 30 seconds and try again.';
                } else {
                    errorMessage = `Server error (${response.status}). Please try again shortly.`;
                }
            }
            throw new Error(errorMessage);
        }

        await fetchCurrentUser();
        navigate('/');
    };

    const logout = async () => {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include',
            });
        } catch (error) {
            console.error('Failed to logout on server:', error);
        }
        setUser(null);
        navigate('/login');
    };

    const updateUser = (updated: Partial<User>) => {
        setUser((prev) => prev ? { ...prev, ...updated } : prev);
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                login,
                logout,
                updateUser,
                isAuthenticated: !!user,
                isLoading,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
