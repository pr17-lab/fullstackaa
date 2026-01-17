import React from 'react';

export const SkeletonStatCard: React.FC = () => {
    return (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-zinc-800 transition-colors">
            <div className="flex items-center justify-between mb-4">
                {/* Icon skeleton */}
                <div className="h-12 w-12 rounded-xl bg-gray-200 dark:bg-zinc-800 animate-pulse"></div>
            </div>
            <div>
                {/* Title skeleton */}
                <div className="h-4 w-24 bg-gray-200 dark:bg-zinc-800 rounded animate-pulse mb-2"></div>
                {/* Value skeleton */}
                <div className="h-9 w-16 bg-gray-200 dark:bg-zinc-800 rounded animate-pulse mb-1"></div>
                {/* Subtitle skeleton */}
                <div className="h-3 w-20 bg-gray-200 dark:bg-zinc-800 rounded animate-pulse"></div>
            </div>
        </div>
    );
};
