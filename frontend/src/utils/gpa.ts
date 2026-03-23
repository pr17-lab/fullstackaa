/**
 * Convert GPA from 10.0 scale to percentage
 */
export const gpaToPercentage = (gpa: number | string): number => {
    const gpaNum = typeof gpa === 'string' ? parseFloat(gpa) : gpa;
    return (gpaNum / 10) * 100;
};

/**
 * Format GPA for display (already on 10-point scale)
 */
export const formatGPA = (gpa: number, decimals: number = 2): string => {
    return gpa.toFixed(decimals);
};
