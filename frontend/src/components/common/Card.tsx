import React from 'react';

interface CardProps {
    children: React.ReactNode;
    className?: string;
    variant?: 'default' | 'elevated' | 'interactive';
    onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
    children,
    className = '',
    variant = 'default',
    onClick
}) => {
    const baseStyles = 'bg-white dark:bg-zinc-900 border border-[var(--border-primary)] dark:border-zinc-800 rounded-2xl transition-all duration-200';

    const variantStyles = {
        default: 'shadow-sm',
        elevated: 'shadow-md',
        interactive: 'cursor-pointer hover:border-[var(--brand-primary)] hover:shadow-lg hover:translate-y-[-2px]',
    };

    const handleClick = () => {
        if (onClick) onClick();
    };

    return (
        <div
            className={`${baseStyles} ${variantStyles[variant]} ${className}`}
            onClick={handleClick}
            role={onClick ? 'button' : undefined}
            tabIndex={onClick ? 0 : undefined}
        >
            {children}
        </div>
    );
};

interface CardHeaderProps {
    children: React.ReactNode;
    className?: string;
    action?: React.ReactNode;
}

export const CardHeader: React.FC<CardHeaderProps> = ({ children, className = '', action }) => {
    return (
        <div className={`px-6 py-5 border-b border-[var(--border-primary)] flex items-center justify-between ${className}`}>
            {children}
            {action && <div>{action}</div>}
        </div>
    );
};

interface CardTitleProps {
    children: React.ReactNode;
    className?: string;
}

export const CardTitle: React.FC<CardTitleProps> = ({ children, className = '' }) => {
    return (
        <h3 className={`text-lg font-semibold text-[var(--text-primary)] ${className}`}>
            {children}
        </h3>
    );
};

interface CardContentProps {
    children: React.ReactNode;
    className?: string;
    noPadding?: boolean;
}

export const CardContent: React.FC<CardContentProps> = ({ children, className = '', noPadding = false }) => {
    return (
        <div className={`${noPadding ? '' : 'p-6'} ${className}`}>
            {children}
        </div>
    );
};

interface CardFooterProps {
    children: React.ReactNode;
    className?: string;
}

export const CardFooter: React.FC<CardFooterProps> = ({ children, className = '' }) => {
    return (
        <div className={`px-6 py-4 border-t border-[var(--border-primary)] bg-[var(--bg-tertiary)] rounded-b-2xl ${className}`}>
            {children}
        </div>
    );
};
