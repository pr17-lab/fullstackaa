import React from 'react';

interface SkeletonProps {
    className?: string;
    variant?: 'text' | 'circular' | 'rectangular';
    width?: string | number;
    height?: string | number;
    count?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
    className = '',
    variant = 'rectangular',
    width,
    height,
    count = 1
}) => {
    const baseStyles: React.CSSProperties = {
        backgroundColor: 'var(--bg-tertiary)',
        backgroundImage: 'linear-gradient(90deg, var(--bg-tertiary) 0%, var(--bg-hover) 50%, var(--bg-tertiary) 100%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 2s infinite',
        width: width || '100%',
        height: height || (variant === 'text' ? '1em' : variant === 'circular' ? '40px' : '20px'),
    };

    const variantStyles: React.CSSProperties = {
        borderRadius: variant === 'circular' ? '50%' : variant === 'text' ? '4px' : 'var(--radius-md)',
    };

    const combinedStyles = { ...baseStyles, ...variantStyles };

    if (count > 1) {
        return (
            <div className={`space-y-2 ${className}`}>
                {Array.from({ length: count }).map((_, i) => (
                    <div key={i} style={combinedStyles} />
                ))}
            </div>
        );
    }

    return <div className={className} style={combinedStyles} />;
};

interface SkeletonCardProps {
    className?: string;
}

export const SkeletonCard: React.FC<SkeletonCardProps> = ({ className = '' }) => {
    return (
        <div className={`p-6 bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-xl ${className}`}>
            <div className="flex items-start justify-between mb-4">
                <Skeleton variant="circular" width={48} height={48} />
                <Skeleton width={60} height={24} />
            </div>
            <Skeleton width="70%" height={24} className="mb-2" />
            <Skeleton width="50%" height={16} className="mb-4" />
            <div className="pt-4 border-t border-[var(--border-primary)]">
                <Skeleton width="40%" height={14} />
            </div>
        </div>
    );
};

interface SkeletonTableProps {
    rows?: number;
    columns?: number;
}

export const SkeletonTable: React.FC<SkeletonTableProps> = ({ rows = 5, columns = 4 }) => {
    return (
        <div className="space-y-3">
            {/* Header */}
            <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
                {Array.from({ length: columns }).map((_, i) => (
                    <Skeleton key={`header-${i}`} height={16} width="80%" />
                ))}
            </div>
            {/* Rows */}
            {Array.from({ length: rows }).map((_, rowIndex) => (
                <div key={`row-${rowIndex}`} className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
                    {Array.from({ length: columns }).map((_, colIndex) => (
                        <Skeleton key={`cell-${rowIndex}-${colIndex}`} height={20} />
                    ))}
                </div>
            ))}
        </div>
    );
};
