import React, { useEffect, useState } from 'react';
import { LucideIcon } from 'lucide-react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

interface StatCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    color?: 'indigo' | 'violet' | 'blue' | 'emerald' | 'teal';
    subtitle?: string;
}

const colorClasses = {
    indigo: 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400',
    violet: 'bg-violet-50 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400',
    blue: 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
    emerald: 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400',
    teal: 'bg-teal-50 dark:bg-teal-900/30 text-teal-600 dark:text-teal-400',
};

const borderClasses = {
    indigo: 'border-l-4 border-l-indigo-500',
    violet: 'border-l-4 border-l-violet-500',
    blue: 'border-l-4 border-l-blue-500',
    emerald: 'border-l-4 border-l-emerald-500',
    teal: 'border-l-4 border-l-teal-500',
};

export const StatCard: React.FC<StatCardProps> = ({
    title,
    value,
    icon: Icon,
    color = 'indigo',
    subtitle
}) => {
    // If it's a string, try extracting numeric part (e.g. '92%')
    const numericStr = typeof value === 'string' ? value.replace(/[^0-9.]/g, '') : value;
    const numericValue = parseFloat(numericStr as string);
    const isAnimated = !isNaN(numericValue);

    const motionValue = useMotionValue(0);
    const springValue = useSpring(motionValue, { duration: 1200, bounce: 0 });
    const [displayValue, setDisplayValue] = useState(value);

    useEffect(() => {
        if (isAnimated) {
            motionValue.set(numericValue);
        }
    }, [numericValue, isAnimated, motionValue]);

    useEffect(() => {
        if (isAnimated) {
            return springValue.on('change', (latest) => {
                if (title.toLowerCase().includes('gpa')) {
                    setDisplayValue(latest.toFixed(2));
                } else if (title.toLowerCase().includes('rate') || typeof value === 'string' && value.includes('%')) {
                    setDisplayValue(Math.round(latest) + '%');
                } else {
                    setDisplayValue(Math.round(latest));
                }
            });
        }
    }, [springValue, isAnimated, title, value]);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
            className={`bg-white dark:bg-zinc-900 rounded-2xl shadow-sm hover:shadow-lg hover:border-white/10 hover:shadow-black/20 p-6 border border-gray-100 dark:border-zinc-800 transition-all duration-200 ${borderClasses[color]}`}
        >
            <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl ${colorClasses[color]} transition-colors`}>
                    <Icon className="h-6 w-6" />
                </div>
            </div>
            <div>
                <p className="text-sm font-medium text-gray-500 dark:text-zinc-400 mb-1">{title}</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-zinc-100">{displayValue}</p>
                {subtitle && (
                    <p className="text-xs text-gray-400 dark:text-zinc-500 mt-1">{subtitle}</p>
                )}
            </div>
        </motion.div>
    );
};
