import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { WifiOff, Loader2, AlertTriangle, ShieldAlert, RefreshCw, LogIn, ArrowLeft } from 'lucide-react';
import type { WsConnState, WsErrorKind } from '../../hooks/useWebSocketInterview';

interface WsConnectionBannerProps {
    connState: WsConnState;
    retryAttempt: number;
    elapsedMs: number;
    wsError: WsErrorKind;
    retryNow: () => void;
    onGoToLobby?: () => void;
    onGoToLogin?: () => void;
}

const MAX_RETRIES = 7;
const WAKING_UP_SECONDARY_MS = 10_000;

export function WsConnectionBanner({
    connState,
    retryAttempt,
    elapsedMs,
    wsError,
    retryNow,
    onGoToLobby,
    onGoToLogin,
}: WsConnectionBannerProps) {
    const [showSecondary, setShowSecondary] = useState(false);

    // Show "Still waking up…" line after 10s in connecting state
    useEffect(() => {
        if (connState === 'connecting') {
            setShowSecondary(false);
            const t = setTimeout(() => setShowSecondary(true), WAKING_UP_SECONDARY_MS);
            return () => clearTimeout(t);
        } else {
            setShowSecondary(false);
        }
    }, [connState]);

    const visible = connState !== 'connected' && connState !== 'closed' && connState !== 'idle';

    return (
        <AnimatePresence>
            {visible && (
                <motion.div
                    key="ws-banner"
                    initial={{ opacity: 0, y: -12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -12 }}
                    transition={{ duration: 0.25 }}
                    className="w-full mb-6"
                >
                    {connState === 'connecting' && (
                        <div className="rounded-2xl border border-indigo-500/25 bg-indigo-950/60 backdrop-blur-sm px-5 py-4 flex items-start gap-4 shadow-lg">
                            <span className="mt-0.5 shrink-0">
                                <Loader2 className="h-5 w-5 text-indigo-400 animate-spin" />
                            </span>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-semibold text-indigo-200">
                                    Waking up the server — this can take up to a minute on first connect.
                                </p>
                                <AnimatePresence>
                                    {showSecondary && (
                                        <motion.p
                                            initial={{ opacity: 0, height: 0 }}
                                            animate={{ opacity: 1, height: 'auto' }}
                                            exit={{ opacity: 0, height: 0 }}
                                            className="text-xs text-indigo-400/80 mt-1"
                                        >
                                            Still waking up… almost there
                                            <span className="inline-block ml-1.5 text-indigo-400 animate-pulse">●●●</span>
                                        </motion.p>
                                    )}
                                </AnimatePresence>
                                <p className="text-[11px] text-indigo-500/60 mt-1.5">
                                    {Math.round(elapsedMs / 1000)}s elapsed
                                </p>
                            </div>
                            {/* Shimmer progress bar */}
                            <div className="absolute bottom-0 left-0 right-0 h-0.5 overflow-hidden rounded-b-2xl">
                                <div className="h-full w-1/3 bg-indigo-500/50 animate-[shimmer_2s_linear_infinite] rounded-full" />
                            </div>
                        </div>
                    )}

                    {connState === 'reconnecting' && (
                        <div className="rounded-2xl border border-amber-500/30 bg-amber-950/50 backdrop-blur-sm px-5 py-4 flex items-start gap-4 shadow-lg">
                            <span className="mt-0.5 shrink-0">
                                <WifiOff className="h-5 w-5 text-amber-400" />
                            </span>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-semibold text-amber-200">
                                    Connection lost, reconnecting…
                                    <span className="ml-2 text-amber-400/80 font-mono text-xs">
                                        (attempt {retryAttempt} of {MAX_RETRIES})
                                    </span>
                                </p>
                                <p className="text-xs text-amber-400/70 mt-1">
                                    Your answers are safe — we'll pick up where you left off.
                                </p>
                                <div className="mt-2 flex gap-1">
                                    {Array.from({ length: MAX_RETRIES }).map((_, i) => (
                                        <div
                                            key={i}
                                            className={`h-1 flex-1 rounded-full transition-all duration-500 ${
                                                i < retryAttempt
                                                    ? 'bg-amber-500'
                                                    : i === retryAttempt - 1
                                                    ? 'bg-amber-400 animate-pulse'
                                                    : 'bg-amber-950'
                                            }`}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {connState === 'failed' && wsError === 'auth_expired' && (
                        <div className="rounded-2xl border border-red-500/30 bg-red-950/50 backdrop-blur-sm px-5 py-4 flex items-start gap-4 shadow-lg">
                            <span className="mt-0.5 shrink-0">
                                <ShieldAlert className="h-5 w-5 text-red-400" />
                            </span>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-semibold text-red-200">
                                    Your session expired — please log in again.
                                </p>
                                <p className="text-xs text-red-400/70 mt-1">
                                    Your progress is saved. Log in to continue.
                                </p>
                            </div>
                            {onGoToLogin && (
                                <button
                                    onClick={onGoToLogin}
                                    className="shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition shadow"
                                >
                                    <LogIn className="h-3.5 w-3.5" />
                                    Log In
                                </button>
                            )}
                        </div>
                    )}

                    {connState === 'failed' && wsError === 'session_invalid' && (
                        <div className="rounded-2xl border border-red-500/30 bg-red-950/50 backdrop-blur-sm px-5 py-4 flex items-start gap-4 shadow-lg">
                            <span className="mt-0.5 shrink-0">
                                <AlertTriangle className="h-5 w-5 text-red-400" />
                            </span>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-semibold text-red-200">
                                    This session can't be resumed.
                                </p>
                                <p className="text-xs text-red-400/70 mt-1">
                                    Your previous answers are saved. Start a new interview from the lobby.
                                </p>
                            </div>
                            {onGoToLobby && (
                                <button
                                    onClick={onGoToLobby}
                                    className="shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition shadow"
                                >
                                    <ArrowLeft className="h-3.5 w-3.5" />
                                    Back to Lobby
                                </button>
                            )}
                        </div>
                    )}

                    {connState === 'failed' && wsError === 'connection_failed' && (
                        <div className="rounded-2xl border border-red-500/30 bg-red-950/50 backdrop-blur-sm px-5 py-4 flex items-start gap-4 shadow-lg">
                            <span className="mt-0.5 shrink-0">
                                <WifiOff className="h-5 w-5 text-red-400" />
                            </span>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-semibold text-red-200">
                                    Connection failed after {MAX_RETRIES} attempts.
                                </p>
                                <p className="text-xs text-red-400/70 mt-1">
                                    Your session progress is saved in the database. Check your network and retry.
                                </p>
                            </div>
                            <button
                                onClick={retryNow}
                                className="shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition shadow"
                            >
                                <RefreshCw className="h-3.5 w-3.5" />
                                Retry
                            </button>
                        </div>
                    )}
                </motion.div>
            )}
        </AnimatePresence>
    );
}
