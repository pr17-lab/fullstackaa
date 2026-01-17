import { useEffect, useState } from 'react';
import { Award, BookOpen, Calendar, User } from 'lucide-react';
import { StudentService } from '../services/api';
import { AcademicRecordSummary } from '../api/types';
import { LoadingSpinner, ErrorDisplay } from '../components/common/Loading';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useAuth } from '../contexts/AuthContext';

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

    // Prepare GPA trend data
    const gpaData = records.terms.map(term => ({
        semester: `Sem ${term.semester}`,
        year: term.year,
        gpa: Number(term.gpa),
        subjects: term.subjects?.length || 0
    }));

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

    const COLORS = ['#6366f1', '#8b5cf6', '#3b82f6', '#10b981'];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
                <h1 className="text-2xl font-bold text-gray-900 mb-4">My Academic Performance</h1>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-50 rounded-lg">
                            <User className="h-5 w-5 text-indigo-600" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500">Student</p>
                            <p className="text-sm font-semibold text-gray-900">{user?.name || 'Student'}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-violet-50 rounded-lg">
                            <BookOpen className="h-5 w-5 text-violet-600" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500">Branch</p>
                            <p className="text-sm font-semibold text-gray-900">{user?.branch || 'N/A'}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-50 rounded-lg">
                            <Calendar className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500">Current Semester</p>
                            <p className="text-sm font-semibold text-gray-900">{user?.semester || 'N/A'}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-emerald-50 rounded-lg">
                            <Award className="h-5 w-5 text-emerald-600" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500">Overall GPA</p>
                            <p className="text-sm font-semibold text-gray-900">{Number(records.overall_gpa).toFixed(2)}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* GPA Trend */}
            <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">GPA Trend Over Time</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={gpaData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis dataKey="semester" stroke="#6b7280" style={{ fontSize: '12px' }} />
                        <YAxis domain={[0, 10]} stroke="#6b7280" style={{ fontSize: '12px' }} />
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
                            dot={{ fill: '#6366f1', r: 5 }}
                            activeDot={{ r: 7 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Credit Distribution and Subject Performance */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Credit Distribution */}
                <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Credit Distribution</h3>
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
                <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Subject Performance</h3>
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
            <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Semester Summary</h3>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-200">
                                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Semester</th>
                                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Year</th>
                                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">GPA</th>
                                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Subjects</th>
                                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Credits</th>
                            </tr>
                        </thead>
                        <tbody>
                            {records.terms.map((term, index) => (
                                <tr key={term.id} className="border-b border-gray-100 hover:bg-gray-50">
                                    <td className="py-3 px-4 text-sm text-gray-900">Semester {term.semester}</td>
                                    <td className="py-3 px-4 text-sm text-gray-600">{term.year}</td>
                                    <td className="py-3 px-4">
                                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                                            {Number(term.gpa).toFixed(2)}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-sm text-gray-600">{term.subjects?.length || 0}</td>
                                    <td className="py-3 px-4 text-sm text-gray-600">
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
