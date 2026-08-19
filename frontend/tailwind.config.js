/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class', // Enable dark mode with class strategy
    theme: {
        extend: {
            colors: {
                // Map standard tailwind color palettes to our custom design system tokens
                gray: {
                    50: '#e8f0fe',
                    100: '#e8f0fe',
                    200: '#c5d1e8',
                    300: '#a3b5d6',
                    400: '#8a9fc0',
                    500: '#6a7fa0',
                    600: '#4a6080',
                    700: 'var(--border-primary)',
                    800: 'var(--border-secondary)',
                    900: 'var(--bg-card)',
                    950: 'var(--bg-page)',
                },
                zinc: {
                    50: '#e8f0fe',
                    100: '#e8f0fe',
                    200: '#c5d1e8',
                    300: '#a3b5d6',
                    400: '#8a9fc0',
                    500: '#6a7fa0',
                    600: '#4a6080',
                    700: 'var(--border-primary)',
                    800: 'var(--border-secondary)',
                    900: 'var(--bg-card)',
                    950: 'var(--bg-page)',
                },
            },
        },
    },
    plugins: [],
}
