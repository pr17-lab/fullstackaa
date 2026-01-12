import { useEffect, useState } from 'react';
import { Award, BookOpen, TrendingUp, Target, Sparkles, Trophy, Clock } from 'lucide-react';
import { StudentService, AnalyticsService } from '../services/api';
import { AcademicRecordSummary, GPATrend, StudentAnalyticsSummary } from '../api/types';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { LoadingSpinner, ErrorDisplay } from '../components/common/Loading';
import { Skeleton, SkeletonCard } from '../components/common/Skeleton';
import { Badge } from '../components/common/Badge';
import { GPATrendChart } from '../components/analytics/AnalyticsCharts';

// Hardcoded student ID (in real app, this would come from auth context)
const STUDENT_ID = 'd0c97f9a-5b6b-4dd7-9248-b12d835448d6';

interface PersonalStatCardProps {
    title: string;
    value: string | number;
    subtext?: string;
    icon: React.ElementType;
    gradient: string;
    trend?: 'up' | 'down' | 'stable';
}

const PersonalStatCard = ({ title, value, subtext, icon: Icon, gradient, trend }: PersonalStatCardProps) => (
    <Card variant="elevated" className="group hover:scale-[1.02] transition-transform duration-200">
        <CardContent className="p-6">
            <div className="flex items-start justify-between mb-4">
                <div className={`h-12 w-12 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center shadow-lg group-hover:shadow-xl transition-shadow`}>
                    <Icon className="h-6 w-6 text-white" />
                </div>
                {trend && (
                    <Badge variant={trend === 'up' ? 'success' : trend === 'down' ? 'warning' : 'default'} size="sm">
                        {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trend}
                    </Badge>
                )}
            </div>
            <div>
                <p className="text-sm font-medium text-[var(--text-tertiary)] mb-1">{title}</p>
                <h3 className="text-3xl font-bold text-[var(--text-primary)] mb-1">{value}</h3>
                {subtext && (
                    <p className="text-xs text-[var(--text-secondary)]">{subtext}</p>
                )}
            </div>
        </CardContent>
    </Card>
);

const Dashboard = () => {
    const [records, setRecords] = useState<AcademicRecordSummary | null>(null);
    const [trend, setTrend] = useState<GPATrend | null>(null);
    const [summary, setSummary] = useState<StudentAnalyticsSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [recordsData, trendData, summaryData] = await Promise.all([
                StudentService.getAcademicRecords(STUDENT_ID),
                AnalyticsService.getGPATrend(STUDENT_ID),
                AnalyticsService.getStudentSummary(STUDENT_ID),
            ]);

            setRecords(recordsData);
            setTrend(trendData);
            setSummary(summaryData);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch your academic data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="space-y-8 animate-fade-in max-w-6xl mx-auto">
                <div>
                    <Skeleton width="400px" height="36px" className="mb-2" />
                    <Skeleton width="300px" height="20px" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {[1, 2, 3, 4].map((i) => (
                        <SkeletonCard key={i} />
                    ))}
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <SkeletonCard className="lg:col-span-2" />
                    <SkeletonCard />
                </div>
            </div>
        );
    }

    if (error) return <ErrorDisplay message={error} onRetry={fetchData} />;
    if (!records || !summary) return null;

    // Calculate pass rate (assuming all passed for now)
    const totalSubjects = summary.total_subjects || 0;
    const passRate = totalSubjects > 0 ? 100 : 0;

    // Calculate rank percentile
    const rankPercentile = summary.performance_percentile ? Number(summary.performance_percentile) : 0;
    const topPercentage = rankPercentile > 0 ? 100 - rankPercentile : 0;

    // Get current time of day for greeting
    const hour = new Date().getHours();
    const greeting = hour < 12 ? 'Good Morning' : hour < 18 ? 'Good Afternoon' : 'Good Evening';

    return (
        <div className="space-y-8 animate-slide-up max-w-6xl mx-auto">
            {/* Welcome Header */}
            <div>
                <div className="flex items-center gap-3 mb-2">
                    <h1 className="text-4xl font-bold text-[var(--text-primary)]">
                        {greeting}, Priya! 👋
                    </h1>
                </div>
                <p className="text-lg text-[var(--text-secondary)]">
                    Here's your academic progress overview
                </p>
            </div>

            {/* Personal Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <PersonalStatCard
                    title="My GPA"
                    value={Number(records.overall_gpa).toFixed(2)}
                    subtext="Overall CGPA"
                    icon={Award}
                    gradient="from-blue-500 to-cyan-600"
                    trend={summary.gpa_trend === 'improving' ? 'up' : summary.gpa_trend === 'declining' ? 'down' : 'stable'}
                />
                <PersonalStatCard
                    title="My Rank"
                    value={`Top ${topPercentage.toFixed(0)}%`}
                    subtext="Among peers"
                    icon={Trophy}
                    gradient="from-amber-500 to-orange-600"
                />
                <PersonalStatCard
                    title="Credits Earned"
                    value={records.total_credits}
                    subtext={`${summary.total_subjects} subjects`}
                    icon={BookOpen}
                    gradient="from-emerald-500 to-teal-600"
                />
                <PersonalStatCard
                    title="Pass Rate"
                    value={`${passRate}%`}
                    subtext="All subjects cleared"
                    icon={Target}
                    gradient="from-purple-500 to-pink-600"
                />
            </div>

            {/* Charts & Insights */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* GPA Trend Chart */}
                <Card variant="elevated" className="lg:col-span-2">
                    <CardHeader>
                        <CardTitle>My GPA Progression</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {trend && <GPATrendChart data={trend.data_points} />}
                    </CardContent>
                </Card>

                {/* Insights Card */}
                <Card variant="elevated">
                    <CardHeader>
                        <CardTitle>Insights</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-start gap-3 p-4 bg-[var(--bg-tertiary)] rounded-lg">
                            <Sparkles className="h-5 w-5 text-[var(--brand-primary)] mt-0.5 flex-shrink-0" />
                            <div>
                                <p className="text-sm font-medium text-[var(--text-primary)] mb-1">
                                    {summary.gpa_trend === 'improving'
                                        ? 'Excellent Progress!'
                                        : summary.gpa_trend === 'declining'
                                            ? 'Room for Improvement'
                                            : 'Steady Performance'}
                                </p>
                                <p className="text-xs text-[var(--text-secondary)]">
                                    {summary.gpa_trend === 'improving'
                                        ? 'Your GPA is trending upward. Keep up the great work!'
                                        : summary.gpa_trend === 'declining'
                                            ? 'Consider seeking help for challenging subjects.'
                                            : 'Maintaining consistent academic performance.'}
                                </p>
                            </div>
                        </div>

                        <div className="flex items-start gap-3 p-4 bg-[var(--bg-tertiary)] rounded-lg">
                            <TrendingUp className="h-5 w-5 text-[var(--accent-emerald)] mt-0.5 flex-shrink-0" />
                            <div>
                                <p className="text-sm font-medium text-[var(--text-primary)] mb-1">Strong Performance</p>
                                <p className="text-xs text-[var(--text-secondary)]">
                                    You're in the top {topPercentage.toFixed(0)}% of your class
                                </p>
                            </div>
                        </div>

                        <div className="flex items-start gap-3 p-4 bg-[var(--bg-tertiary)] rounded-lg">
                            <Clock className="h-5 w-5 text-[var(--accent-amber)] mt-0.5 flex-shrink-0" />
                            <div>
                                <p className="text-sm font-medium text-[var(--text-primary)] mb-1">Current Semester</p>
                                <p className="text-xs text-[var(--text-secondary)]">
                                    Semester {summary.current_semester} • {records.total_credits} credits
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Recent Activity */}
            <Card variant="elevated">
                <CardHeader>
                    <CardTitle>Semester Overview</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="bg-[var(--bg-tertiary)] rounded-lg p-6 text-center">
                            <p className="text-sm text-[var(--text-tertiary)] mb-2">Current Semester</p>
                            <p className="text-3xl font-bold text-[var(--text-primary)] mb-1">
                                {summary.current_semester}
                            </p>
                            <p className="text-xs text-[var(--text-secondary)]">Electronics Engineering</p>
                        </div>
                        <div className="bg-[var(--bg-tertiary)] rounded-lg p-6 text-center">
                            <p className="text-sm text-[var(--text-tertiary)] mb-2">Total Subjects</p>
                            <p className="text-3xl font-bold text-[var(--text-primary)] mb-1">
                                {summary.total_subjects}
                            </p>
                            <p className="text-xs text-[var(--text-secondary)]">Across all semesters</p>
                        </div>
                        <div className="bg-[var(--bg-tertiary)] rounded-lg p-6 text-center">
                            <p className="text-sm text-[var(--text-tertiary)] mb-2">Total Credits</p>
                            <p className="text-3xl font-bold text-[var(--text-primary)] mb-1">
                                {records.total_credits}
                            </p>
                            <p className="text-xs text-[var(--text-secondary)]">Credits earned</p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default Dashboard;
