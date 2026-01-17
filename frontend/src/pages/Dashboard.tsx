import { useEffect, useState } from 'react';
import { Award, BookOpen, Target, TrendingUp } from 'lucide-react';
import { StudentService, AnalyticsService } from '../services/api';
import { AcademicRecordSummary, GPATrend, StudentAnalyticsSummary } from '../api/types';
import { ErrorDisplay } from '../components/common/Loading';
import { SkeletonStatCard } from '../components/common/SkeletonStatCard';
import { StatCard } from '../components/dashboard/StatCard';
import { GPADonutChart } from '../components/dashboard/GPADonutChart';
import { WeakStrongSubjects } from '../components/dashboard/WeakStrongSubjects';
import { MyCoursesCard } from '../components/dashboard/MyCoursesCard';
import { SemesterProgressCard } from '../components/dashboard/SemesterProgressCard';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '../contexts/AuthContext';

const Dashboard = () => {
    const { user } = useAuth();
    const [records, setRecords] = useState<AcademicRecordSummary | null>(null);
    const [trend, setTrend] = useState<GPATrend | null>(null);
    const [summary, setSummary] = useState<StudentAnalyticsSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async () => {
        if (!user?.id) {
            setError('User not authenticated');
            setLoading(false);
            return;
        }

        setLoading(true);
        setError(null);
        try {
            const [recordsData, trendData, summaryData] = await Promise.all([
                StudentService.getAcademicRecords(user.id),
                AnalyticsService.getGPATrend(user.id),
                AnalyticsService.getStudentSummary(user.id),
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
        if (user?.id) {
            fetchData();
        }
    }, [user?.id]);

    if (loading) {
        return (
            <div className="space-y-6">
                {/* Welcome Header Skeleton */}
                <div>
                    <div className="h-9 w-64 bg-gray-200 dark:bg-zinc-800 rounded animate-pulse mb-2"></div>
                    <div className="h-5 w-48 bg-gray-200 dark:bg-zinc-800 rounded animate-pulse"></div>
                </div>

                {/* Skeleton Stat Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <SkeletonStatCard />
                    <SkeletonStatCard />
                    <SkeletonStatCard />
                    <SkeletonStatCard />
                </div>

                {/* Skeleton Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2 space-y-6">
                        <div className="h-96 bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 animate-pulse"></div>
                        <div className="h-80 bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 animate-pulse"></div>
                    </div>
                    <div className="space-y-6">
                        <div className="h-64 bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 animate-pulse"></div>
                        <div className="h-48 bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 animate-pulse"></div>
                    </div>
                </div>
            </div>
        );
    }

    if (error) return <ErrorDisplay message={error} onRetry={fetchData} />;
    if (!records || !summary) return null;

    // Prepare data
    const passRate = summary.total_subjects > 0 ? 100 : 0;

    const allSubjects = records.terms.flatMap(term =>
        term.subjects?.map(subject => ({
            id: subject.id,
            name: subject.subject_name,
            code: subject.subject_code,
            marks: Number(subject.marks),
            credits: subject.credits
        })) || []
    );

    const sortedByMarks = [...allSubjects].sort((a, b) => a.marks - b.marks);

    const weakestSubjects = sortedByMarks.slice(0, 3).map((subject, idx) => ({
        id: subject.id,
        rank: idx + 1,
        name: subject.name,
        percentage: Math.round((subject.marks / 100) * 100)
    }));

    const strongestSubjects = sortedByMarks.slice(-3).reverse().map((subject, idx) => ({
        id: subject.id,
        rank: idx + 1,
        name: subject.name,
        percentage: Math.round((subject.marks / 100) * 100)
    }));

    const courses = allSubjects.map(subject => ({
        id: subject.id,
        name: subject.name,
        code: subject.code,
        credits: subject.credits
    }));

    const gpaChartData = trend?.data_points.map(point => ({
        semester: `S${point.semester}`,
        gpa: Number(point.gpa)
    })) || [];

    return (
        <div className="space-y-6">
            {/* Welcome Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-zinc-100">Welcome back, {user?.name?.split(' ')[0] || 'Student'}! 👋</h1>
                <p className="text-gray-500 dark:text-zinc-400 mt-1">Here's your academic overview</p>
            </div>

            {/* Stat Cards Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Overall GPA"
                    value={Number(records.overall_gpa).toFixed(2)}
                    icon={Award}
                    color="indigo"
                    subtitle="Cumulative"
                />
                <StatCard
                    title="Credits Earned"
                    value={records.total_credits}
                    icon={BookOpen}
                    color="violet"
                    subtitle={`${records.total_terms} semesters`}
                />
                <StatCard
                    title="Subjects"
                    value={summary.total_subjects}
                    icon={TrendingUp}
                    color="blue"
                    subtitle="Completed"
                />
                <StatCard
                    title="Pass Rate"
                    value={`${passRate}%`}
                    icon={Target}
                    color="emerald"
                    subtitle="All cleared"
                />
            </div>

            {/* 2-Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Column (2/3 width) */}
                <div className="lg:col-span-2 space-y-6">
                    {/* GPA Donut */}
                    <GPADonutChart gpa={Number(records.overall_gpa)} maxGpa={10} />

                    {/* GPA Trend Chart */}
                    <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-zinc-800 transition-colors">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-4">GPA Trend</h3>
                        <ResponsiveContainer width="100%" height={250}>
                            <LineChart data={gpaChartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="dark:stroke-zinc-700" />
                                <XAxis dataKey="semester" stroke="#6b7280" className="dark:stroke-zinc-400" style={{ fontSize: '12px' }} />
                                <YAxis domain={[0, 10]} stroke="#6b7280" className="dark:stroke-zinc-400" style={{ fontSize: '12px' }} />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#fff',
                                        border: '1px solid #e5e7eb',
                                        borderRadius: '8px'
                                    }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="gpa"
                                    stroke="#6366f1"
                                    strokeWidth={3}
                                    dot={{ fill: '#6366f1', r: 4 }}
                                    activeDot={{ r: 6 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Weak and Strong Subjects */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <WeakStrongSubjects
                            title="Weakest Subjects"
                            subjects={weakestSubjects}
                            type="weak"
                        />
                        <WeakStrongSubjects
                            title="Strongest Subjects"
                            subjects={strongestSubjects}
                            type="strong"
                        />
                    </div>
                </div>

                {/* Right Sidebar (1/3 width) */}
                <div className="space-y-6">
                    <MyCoursesCard courses={courses} />
                    <SemesterProgressCard
                        currentSemester={summary.current_semester}
                        totalCredits={records.total_credits}
                        totalTerms={records.total_terms}
                    />
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
