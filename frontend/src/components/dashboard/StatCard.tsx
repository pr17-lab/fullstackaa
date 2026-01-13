import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    color?: 'indigo' | 'violet' | 'blue' | 'emerald';
    subtitle?: string;
}

const colorClasses = {
    indigo: 'bg-indigo-50 text-indigo-600',
    violet: 'bg-violet-50 text-violet-600',
    blue: 'bg-blue-50 text-blue-600',
    emerald: 'bg-emerald-50 text-emerald-600',
};

export const StatCard: React.FC<StatCardProps> = ({
    title,
    value,
    icon: Icon,
    color = 'indigo',
    subtitle
}) => {
    return (
        <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl ${colorClasses[color]}`}>
                    <Icon className="h-6 w-6" />
                </div>
            </div>
            <div>
                <p className="text-sm font-medium text-gray-500 mb-1">{title}</p>
                <p className="text-3xl font-bold text-gray-900">{value}</p>
                {subtitle && (
                    <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
                )}
            </div>
        </div>
    );
};
