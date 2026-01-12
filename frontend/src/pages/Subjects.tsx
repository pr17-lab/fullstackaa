import { BookOpen, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/Loading';

const Subjects = () => {
    // This is a placeholder page for future implementation
    // In a real app, this would show current semester subjects, resources, etc.

    const placeholderSubjects = [
        { code: 'EC401', name: 'Digital Signal Processing', credits: 4, status: 'ongoing' },
        { code: 'EC402', name: 'VLSI Design', credits: 4, status: 'ongoing' },
        { code: 'EC403', name: 'Microwave Engineering', credits: 3, status: 'ongoing' },
        { code: 'EC404', name: 'Control Systems', credits: 4, status: 'ongoing' },
        { code: 'EC405', name: 'Communication Networks', credits: 3, status: 'ongoing' },
    ];

    return (
        <div className="space-y-6 animate-slide-up max-w-6xl mx-auto">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-2">My Subjects</h1>
                <p className="text-lg text-[var(--text-secondary)]">
                    Current semester courses and materials
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
                            className="w-full pl-10 pr-4 py-2 bg-[var(--bg-tertiary)] border border-[var(--border-secondary)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)] focus:border-transparent"
                            disabled
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Subjects Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {placeholderSubjects.map((subject) => (
                    <Card key={subject.code} variant="interactive">
                        <CardContent className="p-6">
                            <div className="flex items-start justify-between mb-4">
                                <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-[var(--brand-primary)] to-[var(--brand-secondary)] flex items-center justify-center shadow-lg">
                                    <BookOpen className="h-6 w-6 text-white" />
                                </div>
                                <Badge variant="success" size="sm">Active</Badge>
                            </div>

                            <h3 className="font-semibold text-lg text-[var(--text-primary)] mb-2">
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
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Placeholder Note */}
            <Card variant="elevated">
                <CardContent className="p-8">
                    <EmptyState
                        icon={<BookOpen className="h-12 w-12" />}
                        title="Subject Resources Coming Soon"
                        description="This page will include lecture notes, assignments, and study materials for your courses."
                    />
                </CardContent>
            </Card>
        </div>
    );
};

export default Subjects;
