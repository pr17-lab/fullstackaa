import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft, GraduationCap, BookOpen, Clock, Calendar, TrendingUp, Award, Target } from 'lucide-react';
import { StudentService, AnalyticsService } from '../services/api';
import { Student, AcademicRecordSummary, GPATrend, StudentAnalyticsSummary } from '../api/types';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { LoadingSpinner, ErrorDisplay } from '../components/common/Loading';
import { Skeleton, SkeletonTable } from '../components/common/Skeleton';
import { GPATrendChart } from '../components/analytics/AnalyticsCharts';

const StudentProfile = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const [student, setStudent] = useState<Student | null>(null);
    const [records, setRecords] = useState<AcademicRecordSummary | null>(null);
    const [trend, setTrend] = useState<GPATrend | null>(null);
    const [summary, setSummary] = useState<StudentAnalyticsSummary | null>(null);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchStudentData = async () => {
        if (!id) return;
        setLoading(true);
        setError(null);
        try {
            const [studentData, recordsData, trendData, summaryData] = await Promise.all([
                StudentService.getStudent(id),
                StudentService.getAcademicRecords(id),
                AnalyticsService.getGPATrend(id),
                AnalyticsService.getStudentSummary(id),
            ]);

            setStudent(studentData);
            setRecords(recordsData);
            setTrend(trendData);
            setSummary(summaryData);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch student profile');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStudentData();
    }, [id]);

    if (loading) {
        return (
            <div className="space-y-6 animate-fade-in">
                <Skeleton width="120px" height="40px" />
                <Card>
                    <div className="h-32 bg-gradient-to-r from-[var(--brand-primary)] to-[var(--brand-secondary)] opacity-20" />
                    <CardContent className="p-6">
                        <div className="flex items-start gap-6">
                            <Skeleton variant="circular" width={96} height={96} />
                            <div className="flex-1 space-y-3">
                                <Skeleton width="60%" height={32} />
                                <Skeleton width="40%" height={20} />
                                <div className="flex gap-4 mt-4">
                                    {[1, 2, 3, 4].map((i) => (
                                        <Skeleton key={i} width={120} height={60} />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <Card className="lg:col-span-2">
                        <CardHeader><CardTitle>GPA Progression</CardTitle></CardHeader>
                        <CardContent><Skeleton height={300} /></CardContent>
                    </Card>
                    <Card>
                        <CardHeader><CardTitle>Stats</CardTitle></CardHeader>
                        <CardContent><Skeleton count={3} /></CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    if (error) return <ErrorDisplay message={error} onRetry={fetchStudentData} />;
    if (!student) return <ErrorDisplay message="Student not found" />;

    return (
        <div className="space-y-6 animate-slide-up">
            {/* Back Button */}
            <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/students')}
                leftIcon={<ChevronLeft className="h-4 w-4" />}
            >
                Back to Students
            </Button>

            {/* Profile Header */}
            <Card variant="elevated">
                <div className="h-32 bg-gradient-to-r from-[var(--brand-primary)] to-[var(--brand-secondary)] rounded-t-xl" />
                <CardContent className="relative pt-0 px-8 pb-8">
                    <div className="flex flex-col md:flex-row md:items-end gap-6 -mt-12">
                        {/* Avatar */}
                        <div className="h-24 w-24 rounded-2xl bg-gradient-to-br from-[var(--brand-primary)] to-[var(--brand-secondary)] border-4 border-[var(--bg-secondary)] flex items-center justify-center shadow-2xl">
                            <GraduationCap className="h-12 w-12 text-white" />
                        </div>

                        {/* Info */}
                        <div className="flex-1">
                            <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-2">{student.name}</h1>
                            <div className="flex flex-wrap gap-4 text-sm text-[var(--text-secondary)]">
                                <span className="flex items-center gap-1.5">
                                    <BookOpen className="h-4 w-4" />
                                    {student.branch}
                                </span>
                                <span className="flex items-center gap-1.5">
                                    <Clock className="h-4 w-4" />
                                    Semester {student.semester}
                                </span>
                                <span className="flex items-center gap-1.5">
                                    <Calendar className="h-4 w-4" />
                                    Joined {new Date(student.created_at).getFullYear()}
                                </span>
                            </div>
                        </div>

                        {/* CGPA Display */}
                        <div className="bg-gradient-to-br from-[var(--accent-emerald)] to-[var(--accent-cyan)] rounded-xl p-6 text-center shadow-xl">
                            <p className="text-sm font-medium text-white/80 mb-1">CGPA</p>
                            <p className="text-4xl font-bold text-white">{Number(records?.overall_gpa || 0).toFixed(2)}</p>
                        </div>
                    </div>

                    {/* Quick Stats */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 pt-8 border-t border-[var(--border-primary)]">
                        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4">
                            <p className="text-xs text-[var(--text-tertiary)] uppercase mb-1">Status</p>
                            <Badge variant="success">Active</Badge>
                        </div>
                        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4">
                            <p className="text-xs text-[var(--text-tertiary)] uppercase mb-1">Total Credits</p>
                            <p className="text-lg font-semibold text-[var(--text-primary)]">{records?.total_credits}</p>
                        </div>
                        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4">
                            <p className="text-xs text-[var(--text-tertiary)] uppercase mb-1">Performance</p>
                            <p className="text-lg font-semibold text-[var(--text-primary)]">
                                Top {summary ? 100 - Math.round(Number(summary.performance_percentile)) : 0}%
                            </p>
                        </div>
                        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4">
                            <p className="text-xs text-[var(--text-tertiary)] uppercase mb-1">Trend</p>
                            <Badge variant={summary?.gpa_trend === 'improving' ? 'success' : summary?.gpa_trend === 'declining' ? 'warning' : 'default'}>
                                {summary ? summary.gpa_trend.charAt(0).toUpperCase() + summary.gpa_trend.slice(1) : 'Stable'}
                            </Badge>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Charts & Stats */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card variant="elevated" className="lg:col-span-2">
                    <CardHeader>
                        <CardTitle>GPA Progression</CardTitle>
                    </CardHeader>
                    <CardContent>{trend && <GPATrendChart data={trend.data_points} />}</CardContent>
                </Card>

                <Card variant="elevated">
                    <CardHeader><CardTitle>Achievements</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-start gap-3 p-4 bg-[var(--bg-tertiary)] rounded-lg">
                            <Award className="h-5 w-5 text-[var(--accent-amber)] mt-0.5" />
                            <div>
                                <p className="text-sm font-medium text-[var(--text-primary)] mb-1">Consistent Excellence</p>
                                <p className="text-xs text-[var(--text-secondary)]">Maintain high GPA across all semesters</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3 p-4 bg-[var(--bg-tertiary)] rounded-lg">
                            <Target className="h-5 w-5 text-[var(--brand-primary)] mt-0.5" />
                            <div>
                                <p className="text-sm font-medium text-[var(--text-primary)] mb-1">On Track</p>
                                <p className="text-xs text-[var(--text-secondary)]">Meeting all academic milestones</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Academic History */}
            <div>
                <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-4">Academic History</h2>
                <div className="space-y-4">
                    {records?.terms.map((term) => (
                        <Card key={term.id} variant="elevated">
                            <div className="px-6 py-4 bg-[var(--bg-tertiary)]/50 flex justify-between items-center">
                                <div className="flex items-center gap-3">
                                    <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-[var(--brand-primary)] to-[var(--brand-secondary)] flex items-center justify-center text-white font-bold shadow-md">
                                        S{term.semester}
                                    </div>
                                    <div>
                                        <span className="font-semibold text-[var(--text-primary)]">Semester {term.semester}</span>
                                        <span className="text-sm text-[var(--text-tertiary)] ml-3">{term.year}</span>
                                    </div>
                                </div>
                                <Badge variant="primary" size="lg">SGPA: {Number(term.gpa).toFixed(2)}</Badge>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="text-xs text-[var(--text-tertiary)] uppercase bg-[var(--bg-primary)]">
                                        <tr>
                                            <th className="px-6 py-3 text-left font-medium">Subject Code</th>
                                            <th className="px-6 py-3 text-left font-medium">Subject Name</th>
                                            <th className="px-6 py-3 text-center font-medium">Credits</th>
                                            <th className="px-6 py-3 text-right font-medium">Marks</th>
                                            <th className="px-6 py-3 text-center font-medium">Grade</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-[var(--border-primary)]">
                                        {term.subjects?.map((subject) => (
                                            <tr key={subject.id} className="hover:bg-[var(--bg-tertiary)]/30 transition-colors">
                                                <td className="px-6 py-4 font-medium text-[var(--brand-primary)]">{subject.subject_code}</td>
                                                <td className="px-6 py-4 text-[var(--text-primary)]">{subject.subject_name}</td>
                                                <td className="px-6 py-4 text-center text-[var(--text-secondary)]">{subject.credits}</td>
                                                <td className="px-6 py-4 text-right font-medium text-[var(--text-primary)]">
                                                    {Number(subject.marks).toFixed(1)}
                                                </td>
                                                <td className="px-6 py-4 text-center">
                                                    <Badge variant={subject.grade === 'P' ? 'success' : 'danger'} size="sm">
                                                        {subject.grade}
                                                    </Badge>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </Card>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default StudentProfile;
