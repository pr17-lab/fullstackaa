import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, BookOpen, ChevronRight, ChevronLeft, Search, Filter as FilterIcon } from 'lucide-react';
import { StudentService } from '../services/api';
import { StudentListResponse } from '../api/types';
import { StudentFilters } from '../components/students/StudentFilters';
import { Card, CardContent } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { LoadingSpinner, ErrorDisplay, EmptyState } from '../components/common/Loading';
import { SkeletonCard } from '../components/common/Skeleton';

const Students = () => {
    const navigate = useNavigate();
    const [data, setData] = useState<StudentListResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showFilters, setShowFilters] = useState(false);

    const [filters, setFilters] = useState({
        branch: '',
        semester: '' as number | '',
    });
    const [page, setPage] = useState(1);
    const pageSize = 12;

    const fetchStudents = async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await StudentService.getStudents(
                page,
                pageSize,
                filters.branch || undefined,
                filters.semester || undefined
            );
            setData(result);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch students');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStudents();
    }, [page, filters]);

    const handleFilterChange = (key: string, value: string | number) => {
        setFilters((prev) => ({ ...prev, [key]: value }));
        setPage(1);
    };

    const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

    return (
        <div className="space-y-6 animate-slide-up">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-2">Students</h1>
                    <p className="text-[var(--text-secondary)]">
                        Manage and view student academic profiles
                        {data && (
                            <span className="ml-2 text-[var(--text-primary)] font-medium">
                                · {data.total} total
                            </span>
                        )}
                    </p>
                </div>
                <Button
                    variant="secondary"
                    leftIcon={<FilterIcon className="h-4 w-4" />}
                    onClick={() => setShowFilters(!showFilters)}
                >
                    {showFilters ? 'Hide' : 'Show'} Filters
                </Button>
            </div>

            {/* Filters */}
            {showFilters && (
                <div className="animate-slide-up">
                    <StudentFilters filters={filters} onFilterChange={handleFilterChange} />
                </div>
            )}

            {/* Loading State */}
            {loading && !data && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                        <SkeletonCard key={i} />
                    ))}
                </div>
            )}

            {/* Error State */}
            {error && !data && <ErrorDisplay message={error} onRetry={fetchStudents} />}

            {/* Empty State */}
            {!loading && data?.students.length === 0 && (
                <EmptyState
                    icon={<User className="h-12 w-12" />}
                    title="No students found"
                    description="Try adjusting your filters or check back later"
                    action={
                        <Button
                            variant="secondary"
                            onClick={() => {
                                setFilters({ branch: '', semester: '' });
                                setPage(1);
                            }}
                        >
                            Clear Filters
                        </Button>
                    }
                />
            )}

            {/* Student Grid */}
            {data && data.students.length > 0 && (
                <>
                    <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 ${loading ? 'opacity-50 pointer-events-none' : ''}`}>
                        {data.students.map((student) => (
                            <Card
                                key={student.id}
                                variant="interactive"
                                onClick={() => navigate(`/students/${student.id}`)}
                            >
                                <CardContent className="p-6">
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="h-12 w-12 rounded-full bg-gradient-to-br from-[var(--brand-primary)] to-[var(--brand-secondary)] flex items-center justify-center shadow-lg">
                                            <User className="h-6 w-6 text-white" />
                                        </div>
                                        <Badge variant="info" size="sm">
                                            Sem {student.semester}
                                        </Badge>
                                    </div>

                                    <h3 className="font-semibold text-lg text-[var(--text-primary)] mb-2 truncate">
                                        {student.name}
                                    </h3>

                                    <div className="flex items-center text-sm text-[var(--text-secondary)] mb-4">
                                        <BookOpen className="h-4 w-4 mr-1.5 flex-shrink-0" />
                                        <span className="truncate">{student.branch}</span>
                                    </div>

                                    <div className="pt-4 border-t border-[var(--border-primary)] flex justify-between items-center text-xs text-[var(--text-tertiary)]">
                                        <span>{new Date(student.created_at).toLocaleDateString()}</span>
                                        <ChevronRight className="h-4 w-4 text-[var(--brand-primary)]" />
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="flex items-center justify-center gap-4 pt-4">
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setPage((p) => Math.max(1, p - 1))}
                                disabled={page === 1}
                                leftIcon={<ChevronLeft className="h-4 w-4" />}
                            >
                                Previous
                            </Button>

                            <div className="flex items-center gap-2">
                                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                    let pageNum;
                                    if (totalPages <= 5) {
                                        pageNum = i + 1;
                                    } else if (page <= 3) {
                                        pageNum = i + 1;
                                    } else if (page >= totalPages - 2) {
                                        pageNum = totalPages - 4 + i;
                                    } else {
                                        pageNum = page - 2 + i;
                                    }

                                    return (
                                        <button
                                            key={pageNum}
                                            onClick={() => setPage(pageNum)}
                                            className={`
                        h-10 w-10 rounded-lg font-medium text-sm transition-all
                        ${page === pageNum
                                                    ? 'bg-[var(--brand-primary)] text-white shadow-md'
                                                    : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]'
                                                }
                      `}
                                        >
                                            {pageNum}
                                        </button>
                                    );
                                })}
                            </div>

                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setPage((p) => p + 1)}
                                disabled={page >= totalPages}
                                rightIcon={<ChevronRight className="h-4 w-4" />}
                            >
                                Next
                            </Button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default Students;
