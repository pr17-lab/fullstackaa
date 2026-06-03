import React from 'react';

export const SkeletonStatCard: React.FC = () => {
    return (
        <div className="stat-card">
            <div className="flex items-center justify-between mb-3">
                <div className="h-9 w-9 skeleton rounded-xl" />
            </div>
            <div className="h-6 w-14 skeleton mb-1" />
            <div className="h-3 w-20 skeleton mb-1" />
            <div className="h-3 w-16 skeleton" />
        </div>
    );
};
