import React from 'react';
import { BookOpen, ChevronRight } from 'lucide-react';

interface CourseItem {
    id: string;
    name: string;
    code: string;
    credits: number;
}

interface MyCoursesCardProps {
    courses: CourseItem[];
}

export const MyCoursesCard: React.FC<MyCoursesCardProps> = ({ courses }) => {
    return (
        <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center gap-2 mb-4">
                <BookOpen className="h-5 w-5 text-indigo-600" />
                <h3 className="text-lg font-semibold text-gray-900">My Courses</h3>
            </div>
            <div className="space-y-3">
                {courses.slice(0, 5).map((course) => (
                    <div
                        key={course.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer group"
                    >
                        <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">{course.name}</p>
                            <div className="flex items-center gap-2 mt-1">
                                <span className="text-xs text-gray-500">{course.code}</span>
                                <span className="text-xs text-gray-400">•</span>
                                <span className="text-xs text-gray-500">{course.credits} credits</span>
                            </div>
                        </div>
                        <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-gray-600" />
                    </div>
                ))}
            </div>
            {courses.length > 5 && (
                <button className="w-full mt-4 text-sm font-medium text-indigo-600 hover:text-indigo-700">
                    View all {courses.length} courses
                </button>
            )}
        </div>
    );
};
