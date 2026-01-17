import { useEffect, useState } from 'react';
import { BookOpen, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { EmptyState, LoadingSpinner, ErrorDisplay } from '../components/common/Loading';
import { StudentService } from '../services/api';
import { AcademicRecordSummary } from '../api/types';
import { useAuth } from '../contexts/AuthContext';

const Subjects = () => {
    const { user } = useAuth();
    const [records, setRecords] = useState<AcademicRecordSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');

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
            setError(err.message || 'Failed to fetch subjects');
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

    // Get all unique subjects from all terms
    const allSubjects = records?.terms.flatMap(term =>
        term.subjects?.map(subject => ({
            id: subject.id,
            code: subject.subject_code,
            name: subject.subject_name,
            credits: subject.credits,
            marks: Number(subject.marks),
            grade: subject.grade,
            semester: term.semester,
            year: term.year
        })) || []
    ) || [];

    // Filter subjects by search term
    const filteredSubjects = allSubjects.filter(subject =>
        subject.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        subject.code.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="space-y-6 animate-slide-up max-w-6xl mx-auto">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-2">My Subjects</h1>
                <p className="text-lg text-[var(--text-secondary)]">
                    All courses from your academic history
                </p>
            </div>

            {/* Search Bar */}
            <Card>
                <CardContent className="p-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-[var(--text-tertiary)]" />
                        <input
                            type="text"
                            placeholder="Search subjects..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-[var(--bg-tertiary)] border border-[var(--border-secondary)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)] focus:border-transparent"
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Subjects Count */}
            <div className="text-sm text-[var(--text-secondary)]">
                Showing {filteredSubjects.length} of {allSubjects.length} subjects
            </div>

            {/* Subjects Grid */}
            {filteredSubjects.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredSubjects.map((subject) => (
                        <Card key={subject.id} variant="interactive">
                            <CardContent className="p-6">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-[var(--brand-primary)] to-[var(--brand-secondary)] flex items-center justify-center shadow-lg">
                                        <BookOpen className="h-6 w-6 text-white" />
                                    </div>
                                    <Badge
                                        variant={subject.marks >= 40 ? "success" : "warning"}
                                        size="sm"
                                    >
                                        {subject.grade || 'N/A'}
                                    </Badge>
                                </div>

                                <h3 className="font-semibold text-lg text-[var(--text-primary)] mb-2 line-clamp-2" title={subject.name}>
                                    {subject.name}
                                </h3>

                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-[var(--text-secondary)]">Code</span>
                                        <span className="text-[var(--text-primary)] font-medium">{subject.code}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-[var(--text-secondary)]">Credits</span>
                                        <span className="text-[var(--text-primary)] font-medium">{subject.credits}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-[var(--text-secondary)]">Marks</span>
                                        <span className="text-[var(--text-primary)] font-medium">{subject.marks}/100</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-[var(--text-secondary)]">Semester</span>
                                        <span className="text-[var(--text-primary)] font-medium">Sem {subject.semester} ({subject.year})</span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            ) : (
                <Card variant="elevated">
                    <CardContent className="p-8">
                        <EmptyState
                            icon={<BookOpen className="h-12 w-12" />}
                            title={searchTerm ? "No Subjects Found" : "No Subjects Yet"}
                            description={searchTerm ? "Try adjusting your search term" : "Your academic subjects will appear here once enrolled"}
                        />
                    </CardContent>
                </Card>
            )}
        </div>
    );
};

export default Subjects;
