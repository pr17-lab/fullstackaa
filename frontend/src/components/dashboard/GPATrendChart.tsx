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
import { convertGPATo10Scale } from '../../utils/gpa';

// Register Chart.js components
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

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
            console.log('Fetching GPA trend for student:', studentId);
            try {
                const response = await api.get(`/analytics/gpa-trend/${studentId}`);
                console.log('GPA trend response:', response.data);
                return response.data;
            } catch (err: any) {
                console.error('GPA trend error:', err.response?.data || err.message);
                throw err;
            }
        },
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <LoadingSpinner />
            </div>
        );
    }

    if (error) {
        console.error('Query error:', error);
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                <p className="text-red-600">Failed to load GPA trend data</p>
                <p className="text-sm text-red-500 mt-2">{error instanceof Error ? error.message : 'Unknown error'}</p>
            </div>
        );
    }

    if (!data || data.data_points.length === 0) {
        return (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-8 text-center">
                <p className="text-blue-600">No GPA trend data available yet</p>
            </div>
        );
    }

    // Prepare chart data - CONVERT GPAs to 10-point scale
    const labels = data.data_points.map(
        (point) => `Sem ${point.semester} (${point.year})`
    );
    const gpas = data.data_points.map((point) => convertGPATo10Scale(point.gpa));

    const chartData = {
        labels,
        datasets: [
            {
                label: 'GPA',
                data: gpas,
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 6,
                pointHoverRadius: 8,
                pointBackgroundColor: 'rgb(59, 130, 246)',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
            },
        ],
    };

    const options: ChartOptions<'line'> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            },
            title: {
                display: false,
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12,
                titleFont: {
                    size: 14,
                    weight: 'bold',
                },
                bodyFont: {
                    size: 13,
                },
                callbacks: {
                    label: (context) => {
                        const value = context.parsed.y;
                        return `GPA: ${value !== null ? value.toFixed(2) : 'N/A'}`;
                    },
                },
            },
        },
        scales: {
            y: {
                beginAtZero: true,
                min: 0,
                max: 10.0,
                ticks: {
                    stepSize: 1.0,
                    callback: (value) => {
                        return Number(value).toFixed(1);
                    },
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)',
                },
            },
            x: {
                grid: {
                    display: false,
                },
            },
        },
    };

    // Determine trend indicator
    const getTrendInfo = () => {
        const trend = data.trend;
        if (trend === 'improving') {
            return {
                icon: '📈',
                text: 'Improving',
                color: 'text-green-600',
                bgColor: 'bg-green-50',
            };
        } else if (trend === 'declining') {
            return {
                icon: '📉',
                text: 'Needs Attention',
                color: 'text-orange-600',
                bgColor: 'bg-orange-50',
            };
        } else {
            return {
                icon: '➡️',
                text: 'Stable',
                color: 'text-blue-600',
                bgColor: 'bg-blue-50',
            };
        }
    };

    const trendInfo = getTrendInfo();

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-lg font-semibold text-gray-900">GPA Trend Analysis</h3>
                    <p className="text-sm text-gray-500 mt-1">
                        Average: {convertGPATo10Scale(data.average_gpa).toFixed(2)} • {data.data_points.length} Semesters
                    </p>
                </div>
                <div className={`${trendInfo.bgColor} ${trendInfo.color} px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2`}>
                    <span>{trendInfo.icon}</span>
                    <span>{trendInfo.text}</span>
                </div>
            </div>

            <div className="h-64">
                <Line data={chartData} options={options} />
            </div>
        </div>
    );
};

export default GPATrendChart;
