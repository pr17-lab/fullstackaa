import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Button } from './Button';

interface LoadingSpinnerProps {
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'md', className = '' }) => {
    const sizeStyles = {
        sm: 'h-4 w-4',
        md: 'h-8 w-8',
        lg: 'h-12 w-12',
    };

    return (
        <div className={`flex items-center justify-center ${className}`}>
            <div className="relative">
                <div className={`${sizeStyles[size]} rounded-full border-2 border-[var(--bg-tertiary)]`}></div>
                <div className={`${sizeStyles[size]} rounded-full border-2 border-[var(--brand-primary)] border-t-transparent absolute top-0 left-0 animate-spin`}></div>
            </div>
        </div>
    );
};

interface ErrorDisplayProps {
    message: string;
    onRetry?: () => void;
    className?: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ message, onRetry, className = '' }) => {
    return (
        <div className={`flex flex-col items-center justify-center p-8 ${className}`}>
            <div className="bg-[var(--accent-rose)]/10 rounded-full p-4 mb-4">
                <AlertCircle className="h-8 w-8 text-[var(--accent-rose)]" />
            </div>
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Something went wrong</h3>
            <p className="text-sm text-[var(--text-secondary)] text-center mb-6 max-w-md">
                {message}
            </p>
            {onRetry && (
                <Button variant="secondary" onClick={onRetry}>
                    Try Again
                </Button>
            )}
        </div>
    );
};

interface EmptyStateProps {
    icon?: React.ReactNode;
    title: string;
    description?: string;
    action?: React.ReactNode;
    className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
    icon,
    title,
    description,
    action,
    className = ''
}) => {
    return (
        <div className={`flex flex-col items-center justify-center p-12 ${className}`}>
            {icon && (
                <div className="bg-[var(--bg-tertiary)] rounded-full p-6 mb-4 opacity-50">
                    {icon}
                </div>
            )}
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">{title}</h3>
            {description && (
                <p className="text-sm text-[var(--text-secondary)] text-center mb-6 max-w-md">
                    {description}
                </p>
            )}
            {action && <div>{action}</div>}
        </div>
    );
};
