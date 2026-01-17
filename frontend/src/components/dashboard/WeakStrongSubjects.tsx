import React from 'react';
import { TrendingDown, TrendingUp } from 'lucide-react';

interface SubjectItem {
    id: string | number;
    rank: number;
    name: string;
    percentage: number;
}

interface WeakStrongSubjectsProps {
    title: string;
    subjects: SubjectItem[];
    type: 'weak' | 'strong';
}

export const WeakStrongSubjects: React.FC<WeakStrongSubjectsProps> = ({
    title,
    subjects,
    type
}) => {
    const Icon = type === 'weak' ? TrendingDown : TrendingUp;
    const iconColor = type === 'weak' ? 'text-rose-500' : 'text-emerald-500';
    const barColor = type === 'weak' ? 'bg-rose-500' : 'bg-emerald-500';
    const bgColor = type === 'weak' ? 'bg-rose-50' : 'bg-emerald-50';

    return (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-zinc-800 transition-colors">
            <div className="flex items-center gap-2 mb-4">
                <Icon className={`h-5 w-5 ${iconColor}`} />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100">{title}</h3>
            </div>
            <div className="space-y-4">
                {subjects.map((subject) => (
                    <div key={subject.id}>
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-medium text-gray-400 dark:text-zinc-500 w-6">
                                    #{subject.rank}
                                </span>
                                <span className="text-sm font-medium text-gray-700 dark:text-zinc-300">
                                    {subject.name}
                                </span>
                            </div>
                            <span className="text-sm font-semibold text-gray-900 dark:text-zinc-100">
                                {subject.percentage}%
                            </span>
                        </div>
                        <div className={`w-full h-2 ${bgColor} rounded-full overflow-hidden`}>
                            <div
                                className={`h-full ${barColor} rounded-full transition-all duration-300`}
                                style={{ width: `${subject.percentage}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
