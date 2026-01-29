import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import App from './App.tsx';
import { AuthProvider } from './contexts/AuthContext.tsx';
import { ThemeProvider } from './contexts/ThemeContext.tsx';
import './index.css';

// Create React Query client
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 5 * 60 * 1000, // 5 minutes
            retry: 1,
            refetchOnWindowFocus: false,
        },
    },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                <ThemeProvider>
                    <AuthProvider>
                        <App />
                    </AuthProvider>
                </ThemeProvider>
            </BrowserRouter>
        </QueryClientProvider>
    </React.StrictMode>,
);
