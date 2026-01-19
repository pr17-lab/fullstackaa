import { useEffect, useState } from 'react';
import { Award, BookOpen, Calendar, User } from 'lucide-react';
import { StudentService } from '../services/api';
import { AcademicRecordSummary } from '../api/types';
import { LoadingSpinner, ErrorDisplay } from '../components/common/Loading';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '../contexts/AuthContext';
import GPATrendChart from '../components/dashboard/GPATrendChart';
import { convertGPATo10Scale } from '../utils/gpa';

const Performance = () => {
    const { user } = useAuth();
    const [records, setRecords] = useState<AcademicRecordSummary | null>(null);
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
            const data = await StudentService.getAcademicRecords(user.id);
            setRecords(data);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch performance data');
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
            <div className="flex items-center justify-center min-h-[400px]">
                <LoadingSpinner />
            </div>
        );
    }

    if (error) return <ErrorDisplay message={error} onRetry={fetchData} />;
    if (!records) return null;

    // Prepare credit distribution
    const creditData = records.terms.map(term => ({
        semester: `S${term.semester}`,
        credits: term.subjects?.reduce((sum, subject) => sum + (subject.credits || 0), 0) || 0
    }));

    // Prepare subject performance
    const allSubjects = records.terms.flatMap(term =>
        term.subjects?.map(subject => ({
            name: subject.subject_name.length > 25 ? subject.subject_name.substring(0, 25) + '...' : subject.subject_name,
            marks: Number(subject.marks),
            grade: subject.grade
        })) || []
    );

    const topSubjects = [...allSubjects]
        .sort((a, b) => b.marks - a.marks)
        .slice(0, 8);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-zinc-800 transition-colors">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100 mb-4">My Academic Performance</h1>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-50 dark:bg-indigo-900/30 rounded-lg transition-colors">
                            <User className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 dark:text-zinc-400">Student</p>
                            <p className="text-sm font-semibold text-gray-900 dark:text-zinc-100">{user?.name || 'Student'}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-violet-50 dark:bg-violet-900/30 rounded-lg transition-colors">
                            <BookOpen className="h-5 w-5 text-violet-600 dark:text-violet-400" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 dark:text-zinc-400">Branch</p>
                            <p className="text-sm font-semibold text-gray-900 dark:text-zinc-100">{user?.branch || 'N/A'}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg transition-colors">
                            <Calendar className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 dark:text-zinc-400">Current Semester</p>
                            <p className="text-sm font-semibold text-gray-900 dark:text-zinc-100">{user?.semester || 'N/A'}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-emerald-50 dark:bg-emerald-900/30 rounded-lg transition-colors">
                            <Award className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 dark:text-zinc-400">Overall GPA</p>
                            <p className="text-sm font-semibold text-gray-900 dark:text-zinc-100">{convertGPATo10Scale(records.overall_gpa).toFixed(2)}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* GPA Trend - New Chart.js Component */}
            {user?.id && <GPATrendChart studentId={user.id} />}

            {/* Credit Distribution and Subject Performance */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Credit Distribution */}
                <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-zinc-800 transition-colors">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-4">Credit Distribution</h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={creditData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis dataKey="semester" stroke="#6b7280" style={{ fontSize: '12px' }} />
                            <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#fff',
                                    border: '1px solid #e5e7eb',
                                    borderRadius: '8px'
                                }}
                            />
                            <Bar dataKey="credits" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Subject Performance */}
                <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-zinc-800 transition-colors">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-4">Top Subject Performance</h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={topSubjects} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis type="number" domain={[0, 100]} stroke="#6b7280" style={{ fontSize: '12px' }} />
                            <YAxis type="category" dataKey="name" width={120} stroke="#6b7280" style={{ fontSize: '10px' }} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#fff',
                                    border: '1px solid #e5e7eb',
                                    borderRadius: '8px'
                                }}
                            />
                            <Bar dataKey="marks" fill="#6366f1" radius={[0, 8, 8, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Semester Details Table */}
            <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-zinc-800 transition-colors">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-4">Semester Summary</h3>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-200 dark:border-zinc-700">
                                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-zinc-300">Semester</th>
                                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-zinc-300">Year</th>
                                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-zinc-300">GPA</th>
                                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-zinc-300">Subjects</th>
                                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-zinc-300">Credits</th>
                            </tr>
                        </thead>
                        <tbody>
                            {records.terms.map((term, index) => (
                                <tr key={term.id} className="border-b border-gray-100 dark:border-zinc-800 hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors">
                                    <td className="py-3 px-4 text-sm text-gray-900 dark:text-zinc-100">Semester {term.semester}</td>
                                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-zinc-400">{term.year}</td>
                                    <td className="py-3 px-4">
                                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300 transition-colors">
                                            {Number(term.gpa).toFixed(2)}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-zinc-400">{term.subjects?.length || 0}</td>
                                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-zinc-400">
                                        {term.subjects?.reduce((sum, s) => sum + (s.credits || 0), 0) || 0}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Performance;
