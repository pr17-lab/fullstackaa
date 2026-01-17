import React from 'react';
import { Calendar, Award } from 'lucide-react';

interface SemesterProgressCardProps {
    currentSemester: number;
    totalSemesters?: number;
    totalCredits: number;
    totalTerms: number;
}

export const SemesterProgressCard: React.FC<SemesterProgressCardProps> = ({
    currentSemester,
    totalSemesters = 8,
    totalCredits,
    totalTerms
}) => {
    const progress = (currentSemester / totalSemesters) * 100;

    return (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-zinc-800 transition-colors">
            <div className="flex items-center gap-2 mb-4">
                <Calendar className="h-5 w-5 text-violet-600 dark:text-violet-400" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100">Semester Progress</h3>
            </div>

            <div className="space-y-4">
                <div>
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-600 dark:text-zinc-400">Current Semester</span>
                        <span className="text-sm font-semibold text-gray-900 dark:text-zinc-100">
                            {currentSemester} of {totalSemesters}
                        </span>
                    </div>
                    <div className="w-full h-2 bg-violet-50 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-gradient-to-r from-violet-500 to-indigo-500 rounded-full transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>

                <div className="pt-4 border-t border-gray-100 dark:border-zinc-800 space-y-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Award className="h-4 w-4 text-gray-400 dark:text-zinc-500" />
                            <span className="text-sm text-gray-600 dark:text-zinc-400">Total Credits</span>
                        </div>
                        <span className="text-sm font-semibold text-gray-900 dark:text-zinc-100">{totalCredits}</span>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-gray-400 dark:text-zinc-500" />
                            <span className="text-sm text-gray-600 dark:text-zinc-400">Completed Terms</span>
                        </div>
                        <span className="text-sm font-semibold text-gray-900 dark:text-zinc-100">{totalTerms}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};
