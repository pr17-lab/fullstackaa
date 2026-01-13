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
        <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center gap-2 mb-4">
                <Calendar className="h-5 w-5 text-violet-600" />
                <h3 className="text-lg font-semibold text-gray-900">Semester Progress</h3>
            </div>

            <div className="space-y-4">
                <div>
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-600">Current Semester</span>
                        <span className="text-sm font-semibold text-gray-900">
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

                <div className="pt-4 border-t border-gray-100 space-y-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Award className="h-4 w-4 text-gray-400" />
                            <span className="text-sm text-gray-600">Total Credits</span>
                        </div>
                        <span className="text-sm font-semibold text-gray-900">{totalCredits}</span>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-gray-400" />
                            <span className="text-sm text-gray-600">Completed Terms</span>
                        </div>
                        <span className="text-sm font-semibold text-gray-900">{totalTerms}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};
