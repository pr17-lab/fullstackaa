import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BookOpen, Search, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { EmptyState, LoadingSpinner, ErrorDisplay } from '../components/common/Loading';
import { StudentService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { PageTransition } from '../components/layout/PageTransition';

const Subjects = () => {
    const { user } = useAuth();
    const [searchTerm, setSearchTerm] = useState('');
    const [expandedSemesters, setExpandedSemesters] = useState<Set<number>>(new Set([1])); // Default: first semester expanded

    const { data: records, isLoading, error, refetch } = useQuery({
        queryKey: ['academic-records', user?.id],
        queryFn: () => StudentService.getAcademicRecords(user!.id),
        enabled: !!user?.id,
        staleTime: 5 * 60 * 1000,
    });

    const toggleSemester = (semester: number) => {
        setExpandedSemesters(prev => {
            const newSet = new Set(prev);
            if (newSet.has(semester)) {
                newSet.delete(semester);
            } else {
                newSet.add(semester);
            }
            return newSet;
        });
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <LoadingSpinner />
            </div>
        );
    }

    if (error) return <ErrorDisplay message={(error as Error).message || 'Failed to fetch subjects'} onRetry={() => refetch()} />;

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
            year: term.year,
            gpa: term.gpa
        })) || []
    ) || [];

    // Filter subjects by search term
    const filteredSubjects = allSubjects.filter(subject =>
        subject.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        subject.code.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Group subjects by semester
    const subjectsBySemester = filteredSubjects.reduce((acc, subject) => {
        const key = subject.semester;
        if (!acc[key]) {
            acc[key] = [];
        }
        acc[key].push(subject);
        return acc;
    }, {} as Record<number, typeof filteredSubjects>);

    // Sort semesters in ascending order
    const sortedSemesters = Object.keys(subjectsBySemester)
        .map(Number)
        .sort((a, b) => a - b);

    return (
        <PageTransition className="space-y-6 max-w-6xl mx-auto">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-2">My Subjects</h1>
                <p className="text-lg text-[var(--text-secondary)]">
                    All courses organized by semester
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
                Showing {filteredSubjects.length} of {allSubjects.length} subjects across {sortedSemesters.length} semester{sortedSemesters.length !== 1 ? 's' : ''}
            </div>

            {/* Subjects by Semester */}
            {sortedSemesters.length > 0 ? (
                <div className="space-y-6">
                    {sortedSemesters.map((semester) => {
                        const semesterSubjects = subjectsBySemester[semester];
                        const semesterGPA = semesterSubjects[0]?.gpa || 0;
                        const totalCredits = semesterSubjects.reduce((sum, s) => sum + s.credits, 0);

                        const isExpanded = expandedSemesters.has(semester);

                        return (
                            <div key={semester} className="space-y-4">
                                {/* Semester Header */}
                                <Card variant="elevated">
                                    <CardHeader>
                                        <div
                                            className="cursor-pointer hover:opacity-80 transition-opacity"
                                            onClick={() => toggleSemester(semester)}
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <div className="flex items-center justify-center h-10 w-10 rounded-lg bg-[var(--brand-primary)] text-white font-bold">
                                                        {semester}
                                                    </div>
                                                    <div>
                                                        <CardTitle className="text-xl">
                                                            Semester {semester}
                                                        </CardTitle>
                                                        <p className="text-sm text-[var(--text-secondary)] mt-0.5">
                                                            {semesterSubjects.length} subjects • {totalCredits} credits
                                                        </p>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-6">
                                                    <div className="text-right">
                                                        <div className="text-xs text-[var(--text-secondary)]">GPA</div>
                                                        <div className="text-lg font-bold text-[var(--brand-primary)]">
                                                            {Number(semesterGPA).toFixed(2)}/10
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center justify-center h-10 w-10">
                                                        {isExpanded ? (
                                                            <ChevronUp className="h-6 w-6 text-[var(--text-secondary)]" />
                                                        ) : (
                                                            <ChevronDown className="h-6 w-6 text-[var(--text-secondary)]" />
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </CardHeader>
                                </Card>

                                {/* Semester Subjects Grid - Collapsible */}
                                {isExpanded && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-slide-up">
                                        {semesterSubjects.map((subject) => (
                                            <Card key={subject.id} variant="interactive">
                                                <CardContent className="p-5">
                                                    <div className="flex items-start justify-between mb-3">
                                                        <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-[var(--brand-primary)] to-[var(--brand-secondary)] flex items-center justify-center shadow-md">
                                                            <BookOpen className="h-5 w-5 text-white" />
                                                        </div>
                                                        <Badge
                                                            variant={subject.marks >= 40 ? "success" : "warning"}
                                                            size="sm"
                                                        >
                                                            {subject.grade || 'N/A'}
                                                        </Badge>
                                                    </div>

                                                    <h3 className="font-semibold text-base text-[var(--text-primary)] mb-3 line-clamp-2" title={subject.name}>
                                                        {subject.name}
                                                    </h3>

                                                    <div className="space-y-1.5">
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
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
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
        </PageTransition>
    );
};

export default Subjects;
