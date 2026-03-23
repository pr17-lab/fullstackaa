import { motion } from 'framer-motion';
import { ReactNode } from 'react';

export const PageTransition = ({ children, className = '' }: { children: ReactNode, className?: string }) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className={className}
        >
            {children}
        </motion.div>
    );
};
