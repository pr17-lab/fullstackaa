import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
    title: string;
    value: string | number;
    subtitle?: string;
    icon?: LucideIcon;
    iconBgColor?: string;
    progress?: number;
}

export const MetricCard: React.FC<MetricCardProps> = ({
    title,
    value,
    subtitle,
    icon: Icon,
    iconBgColor = 'from-purple-500 to-violet-500',
    progress
}) => {
    return (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-all">
            <div className="flex items-start justify-between mb-4">
                {Icon && (
                    <div className={`h-12 w-12 rounded-xl bg-gradient-to-br ${iconBgColor} flex items-center justify-center shadow-md`}>
                        <Icon className="h-6 w-6 text-white" />
                    </div>
                )}
            </div>
            <div>
                <p className="text-sm font-medium text-gray-500 mb-1">{title}</p>
                <p className="text-3xl font-bold text-gray-900 mb-1">{value}</p>
                {subtitle && (
                    <p className="text-xs text-gray-400">{subtitle}</p>
                )}
                {progress !== undefined && (
                    <div className="mt-3">
                        <div className="w-full bg-gray-100 rounded-full h-2">
                            <div
                                className="bg-gradient-to-r from-purple-600 to-violet-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

interface ListCardProps {
    title: string;
    items: Array<{
        id: string | number;
        rank: number;
        name: string;
        value: string | number;
        percentage?: number;
    }>;
    actionIcon?: LucideIcon;
}

export const ListCard: React.FC<ListCardProps> = ({ title, items, actionIcon: ActionIcon }) => {
    return (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900">{title}</h3>
                {ActionIcon && (
                    <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                        <ActionIcon className="h-5 w-5 text-gray-400" />
                    </button>
                )}
            </div>
            <div className="space-y-3">
                {items.map((item) => (
                    <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
                        <div className="flex items-center gap-3 flex-1">
                            <span className="text-sm font-medium text-gray-400 w-6">{String(item.rank).padStart(2, '0')}</span>
                            <span className="text-sm font-medium text-gray-900">{item.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            {item.percentage !== undefined && (
                                <span className="px-3 py-1 bg-purple-100 text-purple-700 text-sm font-semibold rounded-full">
                                    {item.percentage}%
                                </span>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

interface ChartCardProps {
    title: string;
    children: React.ReactNode;
    actionIcon?: LucideIcon;
}

export const ChartCard: React.FC<ChartCardProps> = ({ title, children, actionIcon: ActionIcon }) => {
    return (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-gray-900">{title}</h3>
                {ActionIcon && (
                    <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                        <ActionIcon className="h-5 w-5 text-gray-400" />
                    </button>
                )}
            </div>
            <div>{children}</div>
        </div>
    );
};

interface InfoCardProps {
    title: string;
    stats: Array<{
        id: string | number;
        icon: LucideIcon;
        label: string;
        value: string | number;
    }>;
}

export const InfoCard: React.FC<InfoCardProps> = ({ title, stats }) => {
    return (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <h3 className="text-lg font-bold text-gray-900 mb-4">{title}</h3>
            <div className="space-y-3">
                {stats.map((stat) => (
                    <div key={stat.id} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg transition-colors group">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-purple-50 rounded-lg group-hover:bg-purple-100 transition-colors">
                                <stat.icon className="h-5 w-5 text-purple-600" />
                            </div>
                            <span className="text-sm font-medium text-gray-600">{stat.label}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-gray-900">{stat.value}</span>
                            <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
