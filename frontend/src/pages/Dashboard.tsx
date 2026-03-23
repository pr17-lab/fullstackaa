import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Award, BookOpen, Target, TrendingUp, Briefcase, ChevronRight, Map } from 'lucide-react';
import { StudentService, AnalyticsService } from '../services/api';
import { ErrorDisplay } from '../components/common/Loading';
import { SkeletonStatCard } from '../components/common/SkeletonStatCard';
import { StatCard } from '../components/dashboard/StatCard';
import GPATrendChart from '../components/dashboard/GPATrendChart';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../api/client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell } from 'recharts';
import { PageTransition } from '../components/layout/PageTransition';

const Dashboard = () => {
    const { user } = useAuth();

    const { data: records, isLoading: recordsLoading, error: recordsError, refetch: refetchRecords } = useQuery({
        queryKey: ['academic-records', user?.id],
        queryFn: () => StudentService.getAcademicRecords(user!.id),
        enabled: !!user?.id,
        staleTime: 5 * 60 * 1000,
    });

    const { data: summary, isLoading: summaryLoading, error: summaryError } = useQuery({
        queryKey: ['analytics-summary', user?.id],
        queryFn: () => AnalyticsService.getStudentSummary(user!.id),
        enabled: !!user?.id,
        staleTime: 5 * 60 * 1000,
    });

    const { data: careerRec, isLoading: careerLoading } = useQuery({
        queryKey: ['career-recommendation'],
        queryFn: async () => {
            const res = await apiClient.get('/skills/recommendation');
            return res.data;
        },
        retry: false,
        staleTime: 5 * 60 * 1000,
    });

    const loading = recordsLoading || summaryLoading;
    const error = recordsError || summaryError;

    if (loading) {
        return (
            <div className="space-y-5">
                <div>
                    <div className="h-9 w-64 bg-gray-200 dark:bg-zinc-800/50 rounded animate-pulse mb-2"></div>
                    <div className="h-4 w-48 bg-gray-200 dark:bg-zinc-800/50 rounded animate-pulse"></div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
                    <SkeletonStatCard /><SkeletonStatCard /><SkeletonStatCard /><SkeletonStatCard />
                </div>
            </div>
        );
    }

    if (error) return <ErrorDisplay message={(error as Error).message || 'Failed to fetch your academic data'} onRetry={() => refetchRecords()} />;
    if (!records || !summary) return null;

    // Derived Logic
    const passRate = summary.total_subjects > 0 ? 100 : 0;
    const allSubjects = records.terms.flatMap(term =>
        term.subjects?.map(subject => ({
            id: subject.id,
            name: subject.subject_name.length > 25 ? subject.subject_name.substring(0, 25) + '...' : subject.subject_name,
            code: subject.subject_code,
            marks: Number(subject.marks),
            credits: subject.credits,
            grade: subject.grade
        })) || []
    );

    const subjectAverages = allSubjects.reduce((acc, subject) => {
        if (!acc[subject.name]) {
            acc[subject.name] = { name: subject.name, totalMarks: 0, count: 0 };
        }
        acc[subject.name].totalMarks += subject.marks;
        acc[subject.name].count += 1;
        return acc;
    }, {} as Record<string, { name: string; totalMarks: number; count: number }>);

    const uniqueSubjects = Object.values(subjectAverages).map(s => ({
        name: s.name,
        averageMarks: s.totalMarks / s.count,
    }));

    const sortedByMarks = [...uniqueSubjects].sort((a, b) => a.averageMarks - b.averageMarks);
    const weakestSubjects = sortedByMarks.slice(0, 3);
    const strongestSubjects = sortedByMarks.slice(-3).reverse();
    const topSubjectsChart = [...allSubjects].sort((a, b) => b.marks - a.marks).slice(0, 5);

    const creditData = records.terms.map(term => ({
        semester: `S${term.semester}`,
        credits: term.subjects?.reduce((sum, subject) => sum + (subject.credits || 0), 0) || 0
    }));

    const coursesList = allSubjects.map(subject => ({
        id: subject.id,
        name: subject.name,
        code: subject.code,
        credits: subject.credits
    }));

    const overallGPA10 = Number(records.overall_gpa) || 0;

    return (
        <PageTransition className="space-y-5">
            {/* SECTION 1 - Header Strip */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-zinc-100 tracking-tight">Welcome back, {user?.name?.split(' ')[0] || 'Student'}! 👋</h1>
                <p className="text-gray-500 dark:text-zinc-400 mt-1.5 text-sm font-medium">
                    {user?.branch || 'Department'} • Semester {user?.semester || 'N/A'}
                </p>
            </div>

            {/* SECTION 2 - Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
                <StatCard title="Overall GPA" value={overallGPA10.toFixed(2)} icon={Award} color="indigo" subtitle="Cumulative" />
                <StatCard title="Credits Earned" value={records.total_credits} icon={BookOpen} color="blue" subtitle={`${records.total_terms} semesters`} />
                <StatCard title="Subjects" value={summary.total_subjects} icon={TrendingUp} color="teal" subtitle="Completed" />
                <StatCard title="Pass Rate" value={`${passRate}%`} icon={Target} color="emerald" subtitle="All cleared" />
            </div>

            {/* SECTION 3 - Two column layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                {/* LEFT COLUMN (65%) */}
                <div className="lg:col-span-2 space-y-5">
                    <GPATrendChart studentId={user!.id} />

                    {/* Semester Summary Table */}
                    <div className="bg-white/50 dark:bg-zinc-900/30 rounded-xl p-5 border border-gray-100 dark:border-white/5 transition-colors">
                        <h3 className="text-sm font-semibold text-gray-500 dark:text-white/60 uppercase tracking-wider mb-4">Semester Summary</h3>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left whitespace-nowrap">
                                <thead>
                                    <tr className="text-gray-500 dark:text-zinc-400 border-b border-gray-100 dark:border-zinc-800">
                                        <th className="pb-3 font-medium px-2">Semester</th>
                                        <th className="pb-3 font-medium px-2">Year</th>
                                        <th className="pb-3 font-medium px-2">GPA</th>
                                        <th className="pb-3 font-medium px-2">Subjects</th>
                                        <th className="pb-3 font-medium px-2">Credits</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {records.terms.map((term, i) => {
                                        const gpaNum = Number(term.gpa);
                                        const bgClass = i % 2 === 0 ? 'bg-gray-50/50 dark:bg-white/[0.02]' : '';
                                        return (
                                            <tr key={term.id} className={`${bgClass} border-b border-gray-50 dark:border-zinc-800/50 last:border-0`}>
                                                <td className="py-2.5 px-2 text-gray-900 dark:text-zinc-100">Sem {term.semester}</td>
                                                <td className="py-2.5 px-2 text-gray-600 dark:text-zinc-400">{term.year}</td>
                                                <td className="py-2.5 px-2">
                                                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
                                                        gpaNum >= 7.5 ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' :
                                                        gpaNum >= 6.0 ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400' :
                                                        gpaNum >= 5.0 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                                                        'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                                                    }`}>
                                                        {gpaNum.toFixed(2)}
                                                    </span>
                                                </td>
                                                <td className="py-2.5 px-2 text-gray-600 dark:text-zinc-400">{term.subjects?.length || 0}</td>
                                                <td className="py-2.5 px-2 text-gray-600 dark:text-zinc-400">{term.subjects?.reduce((sum, s) => sum + (s.credits || 0), 0) || 0}</td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* RIGHT COLUMN (35%) */}
                <div className="space-y-5">
                    {/* Quick Stats Compact */}
                    <div className="bg-white/50 dark:bg-zinc-900/30 rounded-xl p-5 border border-gray-100 dark:border-white/5 flex flex-col justify-center transition-colors shadow-[0_4px_24px_-8px_rgba(0,0,0,0.1)]">
                        <h3 className="text-sm font-semibold text-gray-500 dark:text-white/60 uppercase tracking-wider mb-4">Academic Progress</h3>
                        <div className="w-full bg-gray-100 dark:bg-zinc-800 rounded-full h-2 mb-2">
                            <div className="bg-indigo-500 h-2 rounded-full" style={{ width: `${Math.min(100, ((summary.current_semester - 1) / 8) * 100)}%` }}></div>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-zinc-300 font-medium mb-4">
                            Semester {summary.current_semester} of 8
                        </p>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <p className="text-xs text-gray-500 dark:text-zinc-500">Total Credits</p>
                                <p className="text-lg font-bold text-gray-900 dark:text-zinc-100">{records.total_credits}</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500 dark:text-zinc-500">Completed</p>
                                <p className="text-lg font-bold text-gray-900 dark:text-zinc-100">{records.total_terms} Terms</p>
                            </div>
                        </div>
                    </div>

                    {/* Unified Subject Performance */}
                    <div className="bg-white/50 dark:bg-zinc-900/30 rounded-xl p-5 border border-gray-100 dark:border-white/5 transition-colors">
                        <h3 className="text-sm font-semibold text-gray-500 dark:text-white/60 uppercase tracking-wider mb-4">Subject Performance</h3>
                        <div className="grid grid-cols-2 gap-5 divide-x divide-gray-100 dark:divide-white/5">
                            {/* Weak */}
                            <div className="pr-1">
                                <p className="text-[11px] font-semibold text-gray-500 dark:text-zinc-500 uppercase tracking-widest mb-3">Needs Polish</p>
                                <div className="space-y-4">
                                    {weakestSubjects.map((s, i) => (
                                        <div key={i}>
                                            <div className="flexjustify-between text-xs mb-1">
                                                <span className="text-gray-700 dark:text-zinc-300 truncate block max-w-full" title={s.name}>{s.name}</span>
                                                <span className="font-bold text-gray-900 dark:text-zinc-100">{Math.round(s.averageMarks)}%</span>
                                            </div>
                                            <div className="w-full bg-red-50 dark:bg-red-900/20 rounded-full h-1.5">
                                                <div className="bg-red-500 dark:bg-red-400 h-1.5 rounded-full" style={{ width: `${s.averageMarks}%` }}></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            {/* Strong */}
                            <div className="pl-5">
                                <p className="text-[11px] font-semibold text-gray-500 dark:text-zinc-500 uppercase tracking-widest mb-3">Strongest</p>
                                <div className="space-y-4">
                                    {strongestSubjects.map((s, i) => (
                                        <div key={i}>
                                            <div className="flexjustify-between text-xs mb-1">
                                                <span className="text-gray-700 dark:text-zinc-300 truncate block max-w-full" title={s.name}>{s.name}</span>
                                                <span className="font-bold text-gray-900 dark:text-zinc-100">{Math.round(s.averageMarks)}%</span>
                                            </div>
                                            <div className="w-full bg-emerald-50 dark:bg-emerald-900/20 rounded-full h-1.5">
                                                <div className="bg-emerald-500 dark:bg-emerald-400 h-1.5 rounded-full" style={{ width: `${s.averageMarks}%` }}></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Career Intelligence */}
                    <div className="bg-gradient-to-br from-indigo-50/50 to-white/50 dark:from-indigo-950/20 dark:to-zinc-900/30 rounded-xl p-5 border border-indigo-100/50 dark:border-indigo-500/10 shadow-[0_4px_24px_-8px_rgba(99,102,241,0.15)] relative overflow-hidden transition-colors">
                        <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                            <Briefcase size={80} />
                        </div>
                        <h3 className="text-sm font-semibold text-indigo-700/80 dark:text-indigo-400/80 uppercase tracking-wider mb-4 flex items-center gap-2">
                            <Briefcase className="h-4 w-4" /> Career Intelligence
                        </h3>
                        
                        {careerLoading ? (
                            <div className="animate-pulse space-y-2">
                                <div className="h-6 w-3/4 bg-indigo-100 dark:bg-indigo-900/30 rounded"></div>
                                <div className="h-4 w-1/2 bg-indigo-50 dark:bg-indigo-900/10 rounded"></div>
                            </div>
                        ) : careerRec?.primary_role ? (
                            <div>
                                <p className="text-xl font-bold text-gray-900 dark:text-zinc-100 mb-1">{careerRec.primary_role}</p>
                                {careerRec.match_score != null && (
                                    <span className="inline-flex items-center gap-1 mb-4 px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-400">
                                        ✨ {Math.round(careerRec.match_score)}% MATCH
                                    </span>
                                )}
                                <div className="flex gap-2">
                                    <Link to="/skills" className="flex-1 flex items-center justify-center gap-1 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg py-2 transition-colors">
                                        Analysis <ChevronRight className="h-3 w-3" />
                                    </Link>
                                    <Link to="/roadmap" className="flex items-center justify-center text-xs font-semibold bg-white dark:bg-zinc-800 border border-gray-200 dark:border-white/10 text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-700 rounded-lg px-3 transition-colors">
                                        <Map className="h-3.5 w-3.5" />
                                    </Link>
                                </div>
                            </div>
                        ) : (
                            <div>
                                <p className="text-sm text-gray-600 dark:text-zinc-400 mb-4 line-clamp-2">Complete your academic profile to unlock personalized AI career insights.</p>
                                <div className="flex gap-2">
                                    <Link to="/skills" className="flex-1 flex items-center justify-center gap-1 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg py-2 transition-colors">
                                        View Skills <ChevronRight className="h-3 w-3" />
                                    </Link>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* SECTION 4 - Full Width 3 Columns */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                {/* Credit Distribution (From Performance.tsx) */}
                <div className="bg-white/50 dark:bg-zinc-900/30 rounded-xl p-5 border border-gray-100 dark:border-white/5 transition-colors">
                    <h3 className="text-sm font-semibold text-gray-500 dark:text-white/60 uppercase tracking-wider mb-4">Credit Distribution</h3>
                    <div className="h-[220px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={creditData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(156, 163, 175, 0.1)" vertical={false} />
                                <XAxis dataKey="semester" stroke="rgba(156, 163, 175, 0.5)" tick={{fill: 'rgba(156, 163, 175, 0.8)', fontSize: 11}} axisLine={false} tickLine={false} />
                                <YAxis stroke="rgba(156, 163, 175, 0.5)" tick={{fill: 'rgba(156, 163, 175, 0.8)', fontSize: 11}} axisLine={false} tickLine={false} />
                                <RechartsTooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} contentStyle={{ backgroundColor: 'rgba(24,24,27,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }} itemStyle={{ color: '#fff' }} />
                                <Bar dataKey="credits" fill="#8b5cf6" radius={[4, 4, 0, 0]}>
                                    {creditData.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={index === creditData.length - 1 ? '#6366f1' : '#8b5cf6'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Top Subjects (From Performance.tsx) */}
                <div className="bg-white/50 dark:bg-zinc-900/30 rounded-xl p-5 border border-gray-100 dark:border-white/5 transition-colors">
                    <h3 className="text-sm font-semibold text-gray-500 dark:text-white/60 uppercase tracking-wider mb-4">Top Scores</h3>
                    <div className="h-[220px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={topSubjectsChart} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(156, 163, 175, 0.1)" horizontal={false} />
                                <XAxis type="number" domain={[0, 100]} stroke="rgba(156, 163, 175, 0.5)" tick={{fill: 'rgba(156, 163, 175, 0.8)', fontSize: 11}} axisLine={false} tickLine={false} />
                                <YAxis type="category" dataKey="name" width={110} stroke="rgba(156, 163, 175, 0.5)" tick={{fill: 'rgba(156, 163, 175, 0.8)', fontSize: 10}} axisLine={false} tickLine={false} />
                                <RechartsTooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} contentStyle={{ backgroundColor: 'rgba(24,24,27,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }} itemStyle={{ color: '#fff' }} />
                                <Bar dataKey="marks" fill="#10b981" radius={[0, 4, 4, 0]} barSize={16}>
                                    {topSubjectsChart.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={index === 0 ? '#10b981' : 'rgba(16, 185, 129, 0.6)'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* My Courses */}
                <div className="bg-white/50 dark:bg-zinc-900/30 rounded-xl p-5 border border-gray-100 dark:border-white/5 transition-colors">
                    <h3 className="text-sm font-semibold text-gray-500 dark:text-white/60 uppercase tracking-wider mb-4">My Courses</h3>
                    <div className="space-y-2.5 overflow-y-auto max-h-[220px] pr-1">
                        {coursesList.slice(0, 5).map(course => (
                            <div key={course.id} className="flex justify-between items-center p-3 bg-white/60 dark:bg-white/[0.02] border border-gray-100 dark:border-white/5 rounded-lg">
                                <div>
                                    <p className="text-xs font-semibold text-gray-900 dark:text-zinc-100 truncate w-48">{course.name}</p>
                                    <p className="text-[10px] text-gray-500 mt-0.5">{course.code} • {course.credits} cr</p>
                                </div>
                                <ChevronRight className="h-3.5 w-3.5 text-gray-400" />
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </PageTransition>
    );
};

export default Dashboard;
