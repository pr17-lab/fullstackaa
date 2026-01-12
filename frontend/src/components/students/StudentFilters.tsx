import React from 'react';
import { Filter, X } from 'lucide-react';
import { Card, CardContent } from '../common/Card';

interface StudentFiltersProps {
    filters: {
        branch: string;
        semester: number | '';
    };
    onFilterChange: (key: string, value: string | number) => void;
}

export const StudentFilters: React.FC<StudentFiltersProps> = ({ filters, onFilterChange }) => {
    const branches = ['Computer Science', 'Electronics', 'Mechanical', 'Civil Engineering', 'Electrical'];
    const semesters = [1, 2, 3, 4, 5, 6, 7, 8];

    const hasActiveFilters = filters.branch || filters.semester;

    const clearFilters = () => {
        onFilterChange('branch', '');
        onFilterChange('semester', '');
    };

    return (
        <Card>
            <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <Filter className="h-5 w-5 text-[var(--brand-primary)]" />
                        <h3 className="font-semibold text-[var(--text-primary)]">Filters</h3>
                    </div>
                    {hasActiveFilters && (
                        <button
                            onClick={clearFilters}
                            className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent-rose)] transition-colors flex items-center gap-1"
                        >
                            <X className="h-4 w-4" />
                            Clear all
                        </button>
                    )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Branch Filter */}
                    <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                            Branch
                        </label>
                        <select
                            value={filters.branch}
                            onChange={(e) => onFilterChange('branch', e.target.value)}
                            className="
                w-full px-4 py-2.5 rounded-lg
                bg-[var(--bg-tertiary)] border border-[var(--border-secondary)]
                text-[var(--text-primary)] text-sm
                focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)] focus:border-transparent
                transition-all duration-200
                cursor-pointer
              "
                        >
                            <option value="">All Branches</option>
                            {branches.map((branch) => (
                                <option key={branch} value={branch}>
                                    {branch}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Semester Filter */}
                    <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                            Semester
                        </label>
                        <select
                            value={filters.semester}
                            onChange={(e) => onFilterChange('semester', e.target.value ? Number(e.target.value) : '')}
                            className="
                w-full px-4 py-2.5 rounded-lg
                bg-[var(--bg-tertiary)] border border-[var(--border-secondary)]
                text-[var(--text-primary)] text-sm
                focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)] focus:border-transparent
                transition-all duration-200
                cursor-pointer
              "
                        >
                            <option value="">All Semesters</option>
                            {semesters.map((sem) => (
                                <option key={sem} value={sem}>
                                    Semester {sem}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};
