import React, { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
    leftIcon?: React.ReactNode;
    rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
    children,
    variant = 'primary',
    size = 'md',
    isLoading = false,
    leftIcon,
    rightIcon,
    className = '',
    disabled,
    ...props
}) => {
    const baseStyles = `
    inline-flex items-center justify-center font-medium
    transition-all duration-200 ease-out
    focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[var(--brand-primary)]
    disabled:opacity-50 disabled:cursor-not-allowed
    ${isLoading ? 'cursor-wait' : ''}
  `;

    const variantStyles = {
        primary: `
      bg-gradient-to-r from-[var(--brand-primary)] to-[var(--brand-secondary)]
      text-white shadow-md hover:shadow-lg hover:brightness-110
      active:scale-95
    `,
        secondary: `
      bg-transparent border-2 border-[var(--border-secondary)]
      text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] hover:border-[var(--border-accent)]
      active:scale-95
    `,
        ghost: `
      bg-transparent text-[var(--text-secondary)]
      hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]
      active:scale-95
    `,
        danger: `
      bg-[var(--accent-rose)] text-white shadow-md
      hover:brightness-110 active:scale-95
    `,
    };

    const sizeStyles = {
        sm: 'px-3 py-1.5 text-sm rounded-md gap-1.5',
        md: 'px-4 py-2 text-base rounded-lg gap-2',
        lg: 'px-6 py-3 text-lg rounded-lg gap-2.5',
    };

    return (
        <button
            className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
            disabled={disabled || isLoading}
            {...props}
        >
            {isLoading && (
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            )}
            {!isLoading && leftIcon && <span>{leftIcon}</span>}
            {children}
            {!isLoading && rightIcon && <span>{rightIcon}</span>}
        </button>
    );
};
