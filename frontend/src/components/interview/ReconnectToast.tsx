import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2 } from 'lucide-react';
import type { WsConnState } from '../../hooks/useWebSocketInterview';

interface ReconnectToastProps {
    connState: WsConnState;
}

const TOAST_DURATION_MS = 3000;

export function ReconnectToast({ connState }: ReconnectToastProps) {
    const [visible, setVisible] = useState(false);
    const prevStateRef = useRef<WsConnState>(connState);
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        const prev = prevStateRef.current;
        prevStateRef.current = connState;

        // Fire when transitioning from reconnecting → connected
        if (prev === 'reconnecting' && connState === 'connected') {
            if (timerRef.current) clearTimeout(timerRef.current);
            setVisible(true);
            timerRef.current = setTimeout(() => setVisible(false), TOAST_DURATION_MS);
        }

        return () => {
            if (timerRef.current) clearTimeout(timerRef.current);
        };
    }, [connState]);

    return (
        <AnimatePresence>
            {visible && (
                <motion.div
                    key="reconnect-toast"
                    initial={{ opacity: 0, y: 16, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 16, scale: 0.95 }}
                    transition={{ type: 'spring', stiffness: 400, damping: 28 }}
                    className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2.5 px-5 py-3 rounded-2xl border border-emerald-500/30 bg-emerald-950/90 backdrop-blur-sm shadow-xl shadow-emerald-950/40"
                >
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span className="text-sm font-semibold text-emerald-200">Reconnected successfully</span>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
