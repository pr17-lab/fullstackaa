import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    ChartOptions,
} from 'chart.js';
import { useQuery } from '@tanstack/react-query';
import api from '../../api/client';
import { LoadingSpinner } from '../common/Loading';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

interface GPATrendPoint {
    semester: number;
    year: number;
    gpa: number;
}

interface GPATrendData {
    student_id: string;
    data_points: GPATrendPoint[];
    average_gpa: number;
    trend: string;
}

interface GPATrendChartProps {
    studentId: string;
}

const GPATrendChart = ({ studentId }: GPATrendChartProps) => {
    const { data, isLoading, error } = useQuery<GPATrendData>({
        queryKey: ['gpa-trend', studentId],
        queryFn: async () => {
            const response = await api.get(`/analytics/gpa-trend/${studentId}`);
            return response.data;
        },
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64 bg-white/50 dark:bg-zinc-900/50 rounded-xl border border-gray-100 dark:border-white/5">
                <LoadingSpinner />
            </div>
        );
    }

    if (error || !data || data.data_points.length === 0) {
        return (
            <div className="bg-white/50 dark:bg-zinc-900/50 rounded-xl border border-gray-100 dark:border-white/5 p-5 text-center flex items-center justify-center h-64">
                <p className="text-gray-500 dark:text-zinc-500 text-sm">No GPA trend data available</p>
            </div>
        );
    }

    const labels = data.data_points.map((point) => `Sem ${point.semester} (${point.year})`);
    const gpas = data.data_points.map((point) => point.gpa);

    const chartData = {
        labels,
        datasets: [
            {
                label: 'GPA',
                data: gpas,
                borderColor: '#6366f1', // indigo-500
                backgroundColor: (context: any) => {
                    const ctx = context.chart.ctx;
                    const gradient = ctx.createLinearGradient(0, 0, 0, 250);
                    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
                    gradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');
                    return gradient;
                },
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#6366f1',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
            },
        ],
    };

    const options: ChartOptions<'line'> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            title: { display: false },
            tooltip: {
                backgroundColor: 'rgba(24, 24, 27, 0.9)', // zinc-900
                padding: 10,
                titleFont: { size: 12, weight: 'bold' },
                bodyFont: { size: 13 },
                borderColor: 'rgba(255,255,255,0.1)',
                borderWidth: 1,
                callbacks: {
                    label: (context) => `GPA: ${context.parsed.y?.toFixed(2) ?? 'N/A'}`
                },
            },
        },
        scales: {
            y: {
                beginAtZero: false,
                min: Math.max(0, Math.min(...gpas) - 1.0),
                max: 10.0,
                ticks: {
                    stepSize: 1.0,
                    color: 'rgba(156, 163, 175, 0.8)', // gray-400
                    font: { size: 10 }
                },
                grid: { color: 'rgba(156, 163, 175, 0.1)' },
                border: { display: false }
            },
            x: {
                ticks: {
                    color: 'rgba(156, 163, 175, 0.8)',
                    font: { size: 10 }
                },
                grid: { display: false },
                border: { display: false }
            },
        },
    };

    const getTrendInfo = () => {
        if (data.trend === 'improving') {
            return { icon: '📈', text: 'Improving', colors: 'text-emerald-700 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-800/50' };
        } else if (data.trend === 'declining') {
            return { icon: '📉', text: 'Needs Attention', colors: 'text-red-700 bg-red-50 dark:text-red-400 dark:bg-red-900/30 border border-red-200 dark:border-red-800/50' };
        }
        return { icon: '➡️', text: 'On Track', colors: 'text-indigo-700 bg-indigo-50 dark:text-indigo-400 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-800/50' };
    };

    const trendInfo = getTrendInfo();

    return (
        <div className="bg-white/50 dark:bg-zinc-900/30 rounded-xl p-5 border border-gray-100 dark:border-white/5 transition-colors duration-300">
            <div className="flex items-start justify-between mb-4">
                <h3 className="text-sm font-semibold text-gray-500 dark:text-white/60 uppercase tracking-wider">
                    GPA Trend • {data.data_points.length} Semesters
                </h3>
                <div className={`${trendInfo.colors} px-2.5 py-1 rounded-full font-medium text-[11px] flex items-center gap-1.5`}>
                    <span>{trendInfo.icon}</span>
                    <span>{trendInfo.text}</span>
                </div>
            </div>

            <div className="h-48">
                <Line data={chartData} options={options} />
            </div>
        </div>
    );
};

export default GPATrendChart;
