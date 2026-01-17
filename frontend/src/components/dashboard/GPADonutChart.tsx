import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface GPADonutChartProps {
    gpa: number;
    maxGpa?: number;
}

export const GPADonutChart: React.FC<GPADonutChartProps> = ({ gpa, maxGpa = 10 }) => {
    const percentage = (gpa / maxGpa) * 100;

    const data = [
        { name: 'GPA', value: gpa },
        { name: 'Remaining', value: maxGpa - gpa }
    ];

    const COLORS = ['#6366f1', '#e5e7eb']; // indigo and gray

    return (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-zinc-800 transition-colors">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-4">Overall Performance</h3>
            <div className="flex items-center justify-center">
                <div className="relative w-48 h-48">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={data}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                dataKey="value"
                                startAngle={90}
                                endAngle={-270}
                            >
                                {data.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index]} />
                                ))}
                            </Pie>
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <p className="text-4xl font-bold text-gray-900 dark:text-zinc-100">{gpa.toFixed(2)}</p>
                        <p className="text-sm text-gray-500 dark:text-zinc-400">out of {maxGpa}</p>
                    </div>
                </div>
            </div>
            <div className="mt-6 text-center">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-50 dark:bg-indigo-900/30 rounded-full transition-colors">
                    <div className="w-2 h-2 rounded-full bg-indigo-600 dark:bg-indigo-400"></div>
                    <span className="text-sm font-medium text-indigo-700 dark:text-indigo-400">
                        {percentage.toFixed(1)}% Performance
                    </span>
                </div>
            </div>
        </div>
    );
};
