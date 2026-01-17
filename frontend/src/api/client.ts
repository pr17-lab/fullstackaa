import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
    baseURL: '/api', // Proxy will handle forwarding to backend
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add JWT token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // Standardize error format
        const message = error.response?.data?.detail || error.message || 'An unknown error occurred';
        console.error('API Error:', message);
        return Promise.reject(new Error(message));
    }
);

export default api;
