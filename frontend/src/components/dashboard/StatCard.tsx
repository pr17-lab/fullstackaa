import React, { useEffect, useState } from 'react';
import { LucideIcon } from 'lucide-react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

interface StatCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    color?: 'teal' | 'blue' | 'purple' | 'amber' | 'indigo' | 'emerald';
    subtitle?: string;
    progress?: number;
}

const colorMap: Record<string, string> = {
    indigo:  '#818cf8',
    blue:    '#3b82f6',
    purple:  '#8b5cf6',
    amber:   '#f59e0b',
    teal:    '#818cf8', // remapped to indigo
    emerald: '#10b981',
    violet:  '#a78bfa',
};

export const StatCard: React.FC<StatCardProps> = ({
    title,
    value,
    icon: Icon,
    color = 'teal',
    subtitle,
    progress,
}) => {
    const accentColor = colorMap[color] || colorMap.teal;

    const numericStr = typeof value === 'string' ? value.replace(/[^0-9.]/g, '') : value;
    const numericValue = parseFloat(numericStr as string);
    const isAnimated = !isNaN(numericValue);

    const motionValue = useMotionValue(0);
    const springValue = useSpring(motionValue, { duration: 1200, bounce: 0 });
    const [displayValue, setDisplayValue] = useState(value);

    useEffect(() => {
        if (isAnimated) motionValue.set(numericValue);
    }, [numericValue, isAnimated, motionValue]);

    useEffect(() => {
        if (isAnimated) {
            return springValue.on('change', (latest) => {
                if (typeof value === 'string' && value.includes('%')) {
                    setDisplayValue(Math.round(latest) + '%');
                } else {
                    setDisplayValue(Math.round(latest));
                }
            });
        }
    }, [springValue, isAnimated, value]);

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            whileHover={{ y: -3, transition: { duration: 0.2 } }}
            className="stat-card"
        >
            {/* Icon */}
            <div className="flex items-start justify-between mb-3">
                <div
                    className="h-9 w-9 rounded-xl flex items-center justify-center"
                    style={{ background: `${accentColor}18`, border: `1px solid ${accentColor}28` }}
                >
                    <Icon className="h-4 w-4" style={{ color: accentColor }} />
                </div>
            </div>

            {/* Value */}
            <p
                className="text-2xl font-black tracking-tight mb-0.5"
                style={{ color: accentColor, lineHeight: 1.1 }}
            >
                {displayValue}
            </p>
            <p className="text-xs font-semibold mb-0.5" style={{ color: 'var(--text-primary)', opacity: 0.85 }}>
                {title}
            </p>
            {subtitle && (
                <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                    {subtitle}
                </p>
            )}

            {progress !== undefined && (
                <div className="mt-2.5 progress-track">
                    <div
                        className="progress-fill"
                        style={{ width: `${progress}%`, background: `linear-gradient(90deg, ${accentColor}, ${accentColor}99)` }}
                    />
                </div>
            )}
        </motion.div>
    );
};
