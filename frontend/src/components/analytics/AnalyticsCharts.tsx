import React from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    Cell, LineChart, Line, Legend
} from 'recharts';
import { GradeDistribution, GPATrendPoint, SubjectPerformanceItem } from '../../api/types';

// ... (previous GradeDistributionChart code)

interface GradeDistChartProps {
    data: GradeDistribution[];
}

export const GradeDistributionChart: React.FC<GradeDistChartProps> = ({ data }) => {
    const COLORS = ['#10b981', '#34d399', '#6366f1', '#8b5cf6', '#f59e0b', '#f97316', '#ef4444'];
    // ... (same as before)
    return (
        <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} vertical={false} />
                    <XAxis dataKey="grade" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} tickLine={false} axisLine={false} />
                    <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#fff' }} cursor={{ fill: '#334155', opacity: 0.2 }} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                        {data.map((_, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};

interface GPATrendProps {
    data: GPATrendPoint[];
}

export const GPATrendChart: React.FC<GPATrendProps> = ({ data }) => {
    return (
        <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 20, right: 30, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                    <XAxis
                        dataKey="semester"
                        stroke="#94a3b8"
                        tickFormatter={(value) => `Sem ${value}`}
                        tick={{ fill: '#94a3b8', fontSize: 12 }}
                    />
                    <YAxis
                        domain={[0, 10]}
                        stroke="#94a3b8"
                        tick={{ fill: '#94a3b8', fontSize: 12 }}
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#fff' }}
                        labelFormatter={(value) => `Semester ${value}`}
                    />
                    <Legend />
                    <Line
                        type="monotone"
                        dataKey="gpa"
                        name="GPA"
                        stroke="#6366f1"
                        strokeWidth={3}
                        dot={{ fill: '#6366f1', r: 4, strokeWidth: 0 }}
                        activeDot={{ r: 6 }}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};

interface SubjectPerfProps {
    data: SubjectPerformanceItem[];
}

export const SubjectPerformanceChart: React.FC<SubjectPerfProps> = ({ data }) => {
    // Sort by average marks and take top 5 + bottom 5 or just top 10?
    // Let's show top 10 most frequent subjects or all if small number.
    const chartData = [...data].sort((a, b) => b.average_marks - a.average_marks).slice(0, 10);

    return (
        <div className="h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 60, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} horizontal={true} vertical={false} />
                    <XAxis type="number" domain={[0, 100]} stroke="#94a3b8" />
                    <YAxis
                        type="category"
                        dataKey="subject_code"
                        stroke="#94a3b8"
                        tick={{ fill: '#94a3b8', fontSize: 11 }}
                        width={60}
                    />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#fff' }} />
                    <Bar dataKey="average_marks" name="Avg Marks" fill="#8b5cf6" radius={[0, 4, 4, 0]} barSize={20} />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};
