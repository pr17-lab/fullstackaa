import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
    BookOpen, Search, ChevronDown, ChevronUp,
    Pencil, X, Save, CheckCircle2, AlertCircle,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { EmptyState, LoadingSpinner, ErrorDisplay } from '../components/common/Loading';
import { StudentService, SubjectService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { PageTransition } from '../components/layout/PageTransition';

// ─── Grade colour helper ───────────────────────────────────────────────────
const gradeVariant = (grade: string): 'success' | 'warning' | 'danger' | 'default' => {
    if (!grade) return 'default';
    if (['O', 'A+', 'A'].includes(grade)) return 'success';
    if (['B+', 'B', 'C'].includes(grade)) return 'warning';
    if (['F', 'U'].includes(grade)) return 'danger';
    return 'default';
};

// ─── Toast ────────────────────────────────────────────────────────────────
type ToastVariant = 'success' | 'error';
interface ToastMsg { variant: ToastVariant; text: string }

const Toast = ({ toast, onClose }: { toast: ToastMsg; onClose: () => void }) => (
    <div
        className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-4 rounded-xl shadow-2xl border animate-slide-up
            ${toast.variant === 'success'
                ? 'bg-[var(--bg-secondary)] border-[var(--accent-emerald)]/40 text-[var(--accent-emerald)]'
                : 'bg-[var(--bg-secondary)] border-red-500/40 text-red-400'}`}
        style={{ minWidth: 280 }}
    >
        {toast.variant === 'success'
            ? <CheckCircle2 className="h-5 w-5 shrink-0" />
            : <AlertCircle className="h-5 w-5 shrink-0" />}
        <p className="text-sm font-medium flex-1">{toast.text}</p>
        <button onClick={onClose} className="opacity-60 hover:opacity-100 transition-opacity">
            <X className="h-4 w-4" />
        </button>
    </div>
);

// ─── Edit Modal ───────────────────────────────────────────────────────────
interface EditSubjectModalProps {
    subject: {
        id: string;
        name: string;
        code: string;
        credits: number;
        marks: number;
        grade: string;
    };
    onClose: () => void;
    onSaved: (updated: { id: string; marks: number; grade: string; term_gpa: number }) => void;
}

const EditSubjectModal = ({ subject, onClose, onSaved }: EditSubjectModalProps) => {
    const [marks, setMarks] = useState(String(subject.marks));
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const marksNum = parseFloat(marks);
    const valid = !isNaN(marksNum) && marksNum >= 0 && marksNum <= 100;

    const handleSave = async () => {
        if (!valid) { setError('Marks must be between 0 and 100'); return; }
        setLoading(true);
        setError('');
        try {
            const result = await SubjectService.updateSubject(subject.id, { marks: marksNum });
            onSaved({ id: subject.id, marks: result.marks, grade: result.grade, term_gpa: result.term_gpa });
            onClose();
        } catch (err: any) {
            setError(err.message || 'Failed to update subject');
        } finally {
            setLoading(false);
        }
    };

    return (
        /* Backdrop */
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
            <div className="bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-2xl shadow-2xl w-full max-w-md mx-4 animate-slide-up">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)]">
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-[var(--brand-primary)] to-[var(--brand-secondary)] flex items-center justify-center shadow-md">
                            <BookOpen className="h-5 w-5 text-white" />
                        </div>
                        <div>
                            <h2 className="font-semibold text-[var(--text-primary)] text-sm">{subject.name}</h2>
                            <p className="text-xs text-[var(--text-tertiary)]">{subject.code} · {subject.credits} credits</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="h-8 w-8 rounded-lg flex items-center justify-center text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>

                {/* Body */}
                <div className="px-6 py-5 space-y-5">
                    {/* Current */}
                    <div className="flex items-center justify-between p-3 bg-[var(--bg-tertiary)] rounded-lg">
                        <span className="text-sm text-[var(--text-secondary)]">Current Marks</span>
                        <span className="text-sm font-semibold text-[var(--text-primary)]">{subject.marks}/100</span>
                    </div>

                    {/* New Marks Input */}
                    <div className="space-y-1.5">
                        <label className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wide">
                            New Marks (0 – 100)
                        </label>
                        <input
                            id="input-subject-marks"
                            type="number"
                            min={0}
                            max={100}
                            step={0.5}
                            value={marks}
                            onChange={(e) => { setMarks(e.target.value); setError(''); }}
                            className="w-full bg-[var(--bg-tertiary)] border border-[var(--border-primary)] rounded-lg px-3 py-2.5 text-[var(--text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)]/50 transition"
                            placeholder="e.g. 78"
                        />
                        {/* Live grade preview */}
                        {valid && (
                            <p className="text-xs text-[var(--text-secondary)] mt-1">
                                Grade preview:{' '}
                                <span className="font-semibold text-[var(--brand-primary)]">
                                    {marksNum >= 91 ? 'O' : marksNum >= 81 ? 'A+' : marksNum >= 71 ? 'A' : marksNum >= 61 ? 'B+' : marksNum >= 51 ? 'B' : marksNum >= 45 ? 'C' : marksNum >= 40 ? 'D' : 'F'}
                                </span>
                                {' '}· {marksNum >= 40 ? '✓ Pass' : '✗ Fail'}
                            </p>
                        )}
                        {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
                    </div>
                </div>

                {/* Footer */}
                <div className="flex gap-3 px-6 pb-5">
                    <Button id="btn-cancel-edit-subject" variant="ghost" size="md" onClick={onClose} disabled={loading} className="flex-1">
                        Cancel
                    </Button>
                    <Button
                        id="btn-save-subject"
                        variant="primary"
                        size="md"
                        leftIcon={<Save className="h-4 w-4" />}
                        onClick={handleSave}
                        disabled={loading || !valid}
                        className="flex-1"
                    >
                        {loading ? 'Saving…' : 'Save Marks'}
                    </Button>
                </div>
            </div>
        </div>
    );
};

// ─── Main Page ────────────────────────────────────────────────────────────
const Subjects = () => {
    const { user } = useAuth();
    const queryClient = useQueryClient();
    const [searchTerm, setSearchTerm] = useState('');
    const [expandedSemesters, setExpandedSemesters] = useState<Set<number>>(new Set([1]));
    const [editingSubject, setEditingSubject] = useState<null | {
        id: string; name: string; code: string; credits: number; marks: number; grade: string;
    }>(null);
    const [toast, setToast] = useState<ToastMsg | null>(null);

    const showToast = (variant: ToastVariant, text: string) => {
        setToast({ variant, text });
        setTimeout(() => setToast(null), 4000);
    };

    const { data: records, isLoading, error, refetch } = useQuery({
        queryKey: ['academic-records', user?.id],
        queryFn: () => StudentService.getAcademicRecords(user!.id),
        enabled: !!user?.id,
        staleTime: 5 * 60 * 1000,
    });

    const toggleSemester = (semester: number) => {
        setExpandedSemesters(prev => {
            const newSet = new Set(prev);
            newSet.has(semester) ? newSet.delete(semester) : newSet.add(semester);
            return newSet;
        });
    };

    const handleSaved = (updated: { id: string; marks: number; grade: string; term_gpa: number }) => {
        // Invalidate the cache so GPA charts etc. refresh
        queryClient.invalidateQueries({ queryKey: ['academic-records', user?.id] });
        queryClient.invalidateQueries({ queryKey: ['gpa-trend', user?.id] });
        showToast('success', `Marks updated → Grade: ${updated.grade} · Term GPA: ${updated.term_gpa.toFixed(2)}`);
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <LoadingSpinner />
            </div>
        );
    }

    if (error) return <ErrorDisplay message={(error as Error).message || 'Failed to fetch subjects'} onRetry={() => refetch()} />;

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
            gpa: term.gpa,
        })) || []
    ) || [];

    const filteredSubjects = allSubjects.filter(subject =>
        subject.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        subject.code.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const subjectsBySemester = filteredSubjects.reduce((acc, subject) => {
        if (!acc[subject.semester]) acc[subject.semester] = [];
        acc[subject.semester].push(subject);
        return acc;
    }, {} as Record<number, typeof filteredSubjects>);

    const sortedSemesters = Object.keys(subjectsBySemester).map(Number).sort((a, b) => a - b);

    return (
        <PageTransition className="space-y-6 max-w-6xl mx-auto">
            {toast && <Toast toast={toast} onClose={() => setToast(null)} />}
            {editingSubject && (
                <EditSubjectModal
                    subject={editingSubject}
                    onClose={() => setEditingSubject(null)}
                    onSaved={handleSaved}
                />
            )}

            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-2">My Subjects</h1>
                    <p className="text-lg text-[var(--text-secondary)]">All courses organised by semester</p>
                </div>
                <div className="hidden md:flex items-center gap-2 text-xs text-[var(--text-tertiary)] bg-[var(--bg-tertiary)] px-3 py-2 rounded-lg border border-[var(--border-primary)]">
                    <Pencil className="h-3.5 w-3.5" />
                    Click the pencil to edit marks
                </div>
            </div>

            {/* Search */}
            <Card>
                <CardContent className="p-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-[var(--text-tertiary)]" />
                        <input
                            type="text"
                            placeholder="Search subjects by name or code..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-[var(--bg-tertiary)] border border-[var(--border-secondary)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)] focus:border-transparent"
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Count */}
            <div className="text-sm text-[var(--text-secondary)]">
                Showing {filteredSubjects.length} of {allSubjects.length} subjects across {sortedSemesters.length} semester{sortedSemesters.length !== 1 ? 's' : ''}
            </div>

            {/* Semesters */}
            {sortedSemesters.length > 0 ? (
                <div className="space-y-6">
                    {sortedSemesters.map((semester) => {
                        const semesterSubjects = subjectsBySemester[semester];
                        const semesterGPA = semesterSubjects[0]?.gpa || 0;
                        const totalCredits = semesterSubjects.reduce((sum, s) => sum + s.credits, 0);
                        const isExpanded = expandedSemesters.has(semester);

                        return (
                            <div key={semester} className="space-y-4">
                                {/* Semester header */}
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
                                                        <CardTitle className="text-xl">Semester {semester}</CardTitle>
                                                        <p className="text-sm text-[var(--text-secondary)] mt-0.5">
                                                            {semesterSubjects.length} subjects · {totalCredits} credits
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
                                                        {isExpanded
                                                            ? <ChevronUp className="h-6 w-6 text-[var(--text-secondary)]" />
                                                            : <ChevronDown className="h-6 w-6 text-[var(--text-secondary)]" />}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </CardHeader>
                                </Card>

                                {/* Subject cards */}
                                {isExpanded && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-slide-up">
                                        {semesterSubjects.map((subject) => (
                                            <Card key={subject.id} variant="interactive" className="group relative">
                                                {/* Edit button */}
                                                <button
                                                    id={`btn-edit-subject-${subject.id}`}
                                                    title="Edit marks"
                                                    onClick={() => setEditingSubject({
                                                        id: subject.id,
                                                        name: subject.name,
                                                        code: subject.code,
                                                        credits: subject.credits,
                                                        marks: subject.marks,
                                                        grade: subject.grade,
                                                    })}
                                                    className="absolute top-3 right-3 h-7 w-7 rounded-lg flex items-center justify-center
                                                        bg-[var(--bg-tertiary)] text-[var(--text-tertiary)]
                                                        opacity-0 group-hover:opacity-100
                                                        hover:bg-[var(--brand-primary)] hover:text-white
                                                        transition-all duration-200 z-10 shadow-md"
                                                >
                                                    <Pencil className="h-3.5 w-3.5" />
                                                </button>

                                                <CardContent className="p-5">
                                                    <div className="flex items-start justify-between mb-3">
                                                        <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-[var(--brand-primary)] to-[var(--brand-secondary)] flex items-center justify-center shadow-md">
                                                            <BookOpen className="h-5 w-5 text-white" />
                                                        </div>
                                                        <Badge variant={gradeVariant(subject.grade)} size="sm">
                                                            {subject.grade || 'N/A'}
                                                        </Badge>
                                                    </div>

                                                    <h3 className="font-semibold text-base text-[var(--text-primary)] mb-3 line-clamp-2 pr-6" title={subject.name}>
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

                                                    {/* Marks progress bar */}
                                                    <div className="mt-3">
                                                        <div className="h-1.5 w-full bg-[var(--bg-primary)] rounded-full overflow-hidden">
                                                            <div
                                                                className={`h-full rounded-full transition-all duration-500 ${
                                                                    subject.marks >= 75 ? 'bg-[var(--accent-emerald)]'
                                                                    : subject.marks >= 50 ? 'bg-amber-500'
                                                                    : 'bg-red-500'
                                                                }`}
                                                                style={{ width: `${Math.min(subject.marks, 100)}%` }}
                                                            />
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
                            title={searchTerm ? 'No Subjects Found' : 'No Subjects Yet'}
                            description={searchTerm ? 'Try adjusting your search term' : 'Your academic subjects will appear here once enrolled'}
                        />
                    </CardContent>
                </Card>
            )}
        </PageTransition>
    );
};

export default Subjects;
