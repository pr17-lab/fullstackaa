import { useEffect, useState } from 'react';
import { BookOpen, TrendingUp, Award, Calendar } from 'lucide-react';
import { StudentService } from '../services/api';
import { AcademicRecordSummary } from '../api/types';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner, ErrorDisplay } from '../components/common/Loading';
import { Skeleton, SkeletonTable } from '../components/common/Skeleton';

// Hardcoded student ID
const STUDENT_ID = 'd0c97f9a-5b6b-4dd7-9248-b12d835448d6';

const Performance = () => {
    const [records, setRecords] = useState<AcademicRecordSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await StudentService.getAcademicRecords(STUDENT_ID);
            setRecords(data);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch your performance data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="space-y-6 animate-fade-in max-w-6xl mx-auto">
                <Skeleton width="300px" height="36px" />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <Card key={i}>
                            <CardContent className="p-6">
                                <Skeleton count={3} />
                            </CardContent>
                        </Card>
                    ))}
                </div>
                <Card>
                    <CardHeader><CardTitle>Semester History</CardTitle></CardHeader>
                    <CardContent>
                        <SkeletonTable rows={5} columns={4} />
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (error) return <ErrorDisplay message={error} onRetry={fetchData} />;
    if (!records) return null;

    return (
        <div className="space-y-6 animate-slide-up max-w-6xl mx-auto">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-2">My Performance</h1>
                <p className="text-lg text-[var(--text-secondary)]">
                    Detailed view of your academic journey
                </p>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card variant="elevated">
                    <CardContent className="p-6">
                        <div className="flex items-center gap-4">
                            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center shadow-lg">
                                <Award className="h-6 w-6 text-white" />
                            </div>
                            <div>
                                <p className="text-sm font-medium text-[var(--text-tertiary)] mb-1">Overall CGPA</p>
                                <p className="text-2xl font-bold text-[var(--text-primary)]">
                                    {Number(records.overall_gpa).toFixed(2)}
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card variant="elevated">
                    <CardContent className="p-6">
                        <div className="flex items-center gap-4">
                            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg">
                                <BookOpen className="h-6 w-6 text-white" />
                            </div>
                            <div>
                                <p className="text-sm font-medium text-[var(--text-tertiary)] mb-1">Total Credits</p>
                                <p className="text-2xl font-bold text-[var(--text-primary)]">
                                    {records.total_credits}
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card variant="elevated">
                    <CardContent className="p-6">
                        <div className="flex items-center gap-4">
                            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center shadow-lg">
                                <Calendar className="h-6 w-6 text-white" />
                            </div>
                            <div>
                                <p className="text-sm font-medium text-[var(--text-tertiary)] mb-1">Semesters</p>
                                <p className="text-2xl font-bold text-[var(--text-primary)]">
                                    {records.terms.length}
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Semester-wise Performance */}
            <div>
                <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-4">Semester History</h2>
                <div className="space-y-4">
                    {records.terms.map((term) => (
                        <Card key={term.id} variant="elevated">
                            <div className="px-6 py-4 bg-[var(--bg-tertiary)]/50 flex justify-between items-center border-b border-[var(--border-primary)]">
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

export default Performance;
