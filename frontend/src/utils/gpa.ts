/**
 * Convert GPA from 4.0 scale to 10.0 scale
 * Database stores GPAs on 4.0 scale, but UI displays on 10.0 scale
 */
export const convertGPATo10Scale = (gpa: number | string): number => {
    const gpaNum = typeof gpa === 'string' ? parseFloat(gpa) : gpa;
    // Convert: (GPA_4 / 4.0) × 10
    return (gpaNum / 4.0) * 10;
};

/**
 * Convert GPA to percentage
 */
export const gpaToPercentage = (gpa: number | string): number => {
    const gpa10Scale = convertGPATo10Scale(gpa);
    return (gpa10Scale / 10) * 100;
};

/**
 * Format GPA for display (already on 10-point scale)
 */
export const formatGPA = (gpa: number, decimals: number = 2): string => {
    return gpa.toFixed(decimals);
};
