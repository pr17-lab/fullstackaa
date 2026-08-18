import { useState, useEffect, useRef, useCallback } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type WsConnState = 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'failed' | 'closed';
export type WsErrorKind = 'auth_expired' | 'session_invalid' | 'connection_failed' | null;

// ---------------------------------------------------------------------------
// Backoff config
// ---------------------------------------------------------------------------

const BASE_DELAY_MS            = 1_000;
const MAX_DELAY_MS             = 15_000;
const JITTER_FACTOR            = 0.2;
const MAX_RETRIES              = 7;
const FIRST_CONNECT_TIMEOUT_MS = 75_000; // cold-start aware — server can take up to ~60s
const RECONNECT_TIMEOUT_MS     = 20_000;
const PING_INTERVAL_MS         = 6 * 60 * 1_000; // 6 minutes keep-alive
const STUCK_EVAL_POLL_DELAY_MS = 18_000;          // Item 4 — above typical LLM eval latency

function calcBackoffDelay(attempt: number): number {
    const base = Math.min(BASE_DELAY_MS * Math.pow(2, attempt), MAX_DELAY_MS);
    const jitter = base * JITTER_FACTOR * (Math.random() * 2 - 1);
    return Math.max(500, Math.round(base + jitter));
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useWebSocketInterview(sessionId: string, onCompleted: () => void) {
    // ---- connection state ----
    const [connState, setConnState]       = useState<WsConnState>('idle');
    const [retryAttempt, setRetryAttempt] = useState(0);
    const [elapsedMs, setElapsedMs]       = useState(0);
    const [wsError, setWsError]           = useState<WsErrorKind>(null);

    // ---- interview state ----
    const [socket, setSocket]                     = useState<WebSocket | null>(null);
    const [questions, setQuestions]               = useState<any[]>([]);
    const [currentIndex, setCurrentIndex]         = useState(0);
    const [secondsLeft, setSecondsLeft]           = useState(90);
    const [isEvaluating, setIsEvaluating]         = useState(false);
    const [evalResult, setEvalResult]             = useState<any>(null);
    const [error, setError]                       = useState<string | null>(null);
    const [currentStreamedText, setCurrentStreamedText] = useState('');

    // ---- stable refs (survive re-renders and async closures) ----
    const isIntentionalCloseRef       = useRef<boolean>(false);
    const hasHadSuccessfulConnection  = useRef<boolean>(false); // Item 1
    const isEvaluatingRef             = useRef<boolean>(false); // mirrors isEvaluating for closures
    const lastSubmittedQuestionIdRef  = useRef<string | null>(null);
    const sessionIdRef                = useRef<string>(sessionId); // kept current for async poll closure
    const stuckEvalPollTimerRef       = useRef<ReturnType<typeof setTimeout> | null>(null); // Item 4

    const retryAttemptRef             = useRef<number>(0);
    const questionsRef                = useRef<any[]>([]);
    const onCompletedRef              = useRef(onCompleted);
    const wsRef                       = useRef<WebSocket | null>(null);
    const wsErrorRef                  = useRef<WsErrorKind>(null); // mirrors wsError for onclose closure

    // timers
    const retryTimerRef               = useRef<ReturnType<typeof setTimeout> | null>(null);
    const connectTimeoutRef           = useRef<ReturnType<typeof setTimeout> | null>(null);
    const pingIntervalRef             = useRef<ReturnType<typeof setInterval> | null>(null);
    const elapsedIntervalRef          = useRef<ReturnType<typeof setInterval> | null>(null);

    // ---- keep refs in sync ----
    useEffect(() => { questionsRef.current = questions; }, [questions]);
    useEffect(() => { onCompletedRef.current = onCompleted; }, [onCompleted]);
    useEffect(() => { isEvaluatingRef.current = isEvaluating; }, [isEvaluating]);
    useEffect(() => { sessionIdRef.current = sessionId; }, [sessionId]);
    useEffect(() => { wsErrorRef.current = wsError; }, [wsError]);

    // ---- helpers ----
    const clearRetryTimer = () => {
        if (retryTimerRef.current) { clearTimeout(retryTimerRef.current); retryTimerRef.current = null; }
    };
    const clearConnectTimeout = () => {
        if (connectTimeoutRef.current) { clearTimeout(connectTimeoutRef.current); connectTimeoutRef.current = null; }
    };
    const stopPingInterval = () => {
        if (pingIntervalRef.current) { clearInterval(pingIntervalRef.current); pingIntervalRef.current = null; }
    };
    const stopElapsedInterval = () => {
        if (elapsedIntervalRef.current) { clearInterval(elapsedIntervalRef.current); elapsedIntervalRef.current = null; }
    };
    const clearStuckEvalPoll = () => {
        if (stuckEvalPollTimerRef.current) { clearTimeout(stuckEvalPollTimerRef.current); stuckEvalPollTimerRef.current = null; }
    };
    const clearAllTimers = () => {
        clearRetryTimer();
        clearConnectTimeout();
        stopPingInterval();
        stopElapsedInterval();
        clearStuckEvalPoll();
    };

    const startPingInterval = (ws: WebSocket) => {
        stopPingInterval();
        pingIntervalRef.current = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ event: 'ping', data: {} }));
            }
        }, PING_INTERVAL_MS);
    };

    const startElapsedTimer = () => {
        stopElapsedInterval();
        const start = Date.now();
        setElapsedMs(0);
        elapsedIntervalRef.current = setInterval(() => {
            setElapsedMs(Date.now() - start);
        }, 500);
    };

    // ---- Item 4: bounded one-shot stuck-eval poll ----
    const scheduleStuckEvalPoll = useCallback(() => {
        clearStuckEvalPoll();
        stuckEvalPollTimerRef.current = setTimeout(async () => {
            if (!isEvaluatingRef.current || !lastSubmittedQuestionIdRef.current) return;
            try {
                const res = await fetch(`/api/interview/sessions/${sessionIdRef.current}`);
                if (!res.ok) return;
                const data = await res.json();
                const q = data.questions?.find(
                    (q: any) => (q.question_id ?? q.id) === lastSubmittedQuestionIdRef.current
                );
                if (q?.ai_score != null) {
                    setEvalResult({
                        technical_score: q.ai_score,
                        verdict: q.ai_verdict,
                        feedback: q.ai_feedback ?? 'Score recovered via status check.',
                        _fromReconnect: true,
                    });
                    setIsEvaluating(false);
                    isEvaluatingRef.current = false;
                    lastSubmittedQuestionIdRef.current = null;
                }
                // If still null — do NOT reschedule. Next-submit path is the final fallback.
            } catch {
                // Silent — best-effort safety net.
            }
        }, STUCK_EVAL_POLL_DELAY_MS);
    }, []);

    // ---- connect ----
    const connect = useCallback((isReconnect: boolean) => {
        // Reset intentional-close flag at the start of every new connect attempt
        isIntentionalCloseRef.current = false;

        const isFirstConnect = !isReconnect;
        if (isFirstConnect) {
            hasHadSuccessfulConnection.current = false;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const token = localStorage.getItem('access_token') || '';
        const wsUrl = `${protocol}//${window.location.host}/api/interview/ws/interview/${sessionIdRef.current}${token ? `?token=${token}` : ''}`;

        console.log(`[WS] ${isReconnect ? 'Reconnecting' : 'Connecting'} attempt ${retryAttemptRef.current + 1} → ${wsUrl}`);

        setConnState(isReconnect ? 'reconnecting' : 'connecting');
        startElapsedTimer();

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;
        setSocket(ws);

        // ---- connection timeout ----
        const timeoutMs = isFirstConnect ? FIRST_CONNECT_TIMEOUT_MS : RECONNECT_TIMEOUT_MS;
        connectTimeoutRef.current = setTimeout(() => {
            if (ws.readyState !== WebSocket.OPEN) {
                console.warn(`[WS] Connection timeout after ${timeoutMs}ms`);
                isIntentionalCloseRef.current = false; // ensure drop is treated as unintentional
                ws.close();
            }
        }, timeoutMs);

        ws.onopen = () => {
            console.log('[WS] Connected');
            clearConnectTimeout();
            stopElapsedInterval();
            hasHadSuccessfulConnection.current = true;
            retryAttemptRef.current = 0;
            setRetryAttempt(0);
            setConnState('connected');
            setWsError(null);
            setError(null);
            startPingInterval(ws);
        };

        ws.onmessage = (event) => {
            const rawData = event.data;
            try {
                const isJson = typeof rawData === 'string' && rawData.trim().startsWith('{') && rawData.trim().endsWith('}');
                if (!isJson) {
                    // Raw stream chunk for question generation
                    setCurrentStreamedText(prev => prev + rawData);
                    return;
                }

                const msg = JSON.parse(rawData);
                console.log('[WS] Event:', msg.event);

                if (msg.event === 'pong') {
                    // keep-alive ack — no-op
                    return;
                }

                if (msg.event === 'session_ready' || msg.event === 'question_complete') {
                    setCurrentStreamedText('');
                    const incomingQs = msg.data.questions;
                    setQuestions(incomingQs);

                    // Items 3 + 4: reconcile pending eval result after a reconnect
                    if (isEvaluatingRef.current && lastSubmittedQuestionIdRef.current) {
                        const evaluated = incomingQs.find(
                            (q: any) => (q.question_id ?? q.id) === lastSubmittedQuestionIdRef.current
                        );
                        if (evaluated?.ai_score != null) {
                            // Item 3: score already committed to DB — clear spinner immediately
                            clearStuckEvalPoll(); // cancel pending poll, no longer needed
                            setEvalResult({
                                technical_score: evaluated.ai_score,
                                verdict: evaluated.ai_verdict,
                                feedback: evaluated.ai_feedback ?? 'Score recovered after reconnect.',
                                _fromReconnect: true,
                            });
                            setIsEvaluating(false);
                            isEvaluatingRef.current = false;
                            lastSubmittedQuestionIdRef.current = null;
                        } else {
                            // Item 4: score still null — eval genuinely in-flight on server.
                            // Schedule single one-shot poll as safety net.
                            scheduleStuckEvalPoll();
                        }
                    }

                    const unansweredIdx = incomingQs.findIndex((q: any) => !q.user_answer);
                    if (unansweredIdx !== -1) setCurrentIndex(unansweredIdx);
                    return;
                }

                if (msg.event === 'session_created') {
                    // No questions yet — server expects us to send start_interview
                    // (handled by WebSocketInterviewRoom sending the event after connect)
                    return;
                }

                if (msg.event === 'answer_evaluated') {
                    // Gate on question_id before clearing poll timer.
                    // See plan §Site 3 comment: in current server behavior this branch is
                    // effectively a defensive no-op for the tracked question (the old socket's
                    // coroutine pushes to the dead socket, so the new socket never receives
                    // answer_evaluated for the question the poll is tracking). The guard is here
                    // to stay correct if server behavior changes or events arrive out of order.
                    const incomingQid = msg.data?.question_id;
                    if (incomingQid === lastSubmittedQuestionIdRef.current) {
                        clearStuckEvalPoll(); // gated clear — same question
                        setIsEvaluating(false);
                        isEvaluatingRef.current = false;
                        setEvalResult(msg.data);
                        lastSubmittedQuestionIdRef.current = null;
                    } else {
                        // answer_evaluated for a different question — leave poll timer running
                        setEvalResult(msg.data);
                    }
                    // Advance to next question after 3s delay showing score
                    setTimeout(() => {
                        setCurrentIndex(idx => {
                            const qs = questionsRef.current;
                            return idx < qs.length - 1 ? idx + 1 : idx;
                        });
                    }, 3000);
                    return;
                }

                if (msg.event === 'session_completed') {
                    console.log('[WS] Session completed');
                    // Mark intentional before the component unmounts / onCompleted fires,
                    // so the onclose handler doesn't trigger a reconnect.
                    isIntentionalCloseRef.current = true;
                    onCompletedRef.current();
                    return;
                }

                if (msg.event === 'error') {
                    const message = msg.data?.message || 'An error occurred during interview generation';
                    console.error('[WS] Server error event:', message);
                    // Non-retryable server-level error messages (before backend close-code changes)
                    if (message === 'Unauthorized') {
                        setWsError('auth_expired');
                    } else if (message === 'Session not found') {
                        setWsError('session_invalid');
                    } else {
                        setError(message);
                    }
                    return;
                }
            } catch {
                // JSON parse failed — treat as raw stream chunk
                setCurrentStreamedText(prev => prev + rawData);
            }
        };

        ws.onerror = () => {
            console.error('[WS] Socket error');
            // onerror is always followed by onclose — handle state transition there
        };

        ws.onclose = (event) => {
            console.log(`[WS] Closed: code=${event.code} reason="${event.reason}"`);
            clearConnectTimeout();
            stopPingInterval();
            stopElapsedInterval();

            // 1. Intentional close — go to closed, no retry
            if (isIntentionalCloseRef.current) {
                isIntentionalCloseRef.current = false;
                setConnState('closed');
                setSocket(null);
                return;
            }

            // 2. Non-retryable: backend auth failure (close code set by backend §Backend Changes)
            if (event.code === 4001 || wsErrorRef.current === 'auth_expired') {
                setWsError('auth_expired');
                wsErrorRef.current = 'auth_expired';
                setConnState('failed');
                setSocket(null);
                return;
            }

            // 3. Non-retryable: session not found (close code set by backend §Backend Changes)
            if (event.code === 4004 || wsErrorRef.current === 'session_invalid') {
                setWsError('session_invalid');
                wsErrorRef.current = 'session_invalid';
                setConnState('failed');
                setSocket(null);
                return;
            }

            // 4. Transitional fallback — see plan §Item 2 TODO comment.
            // TODO: remove once backend close-code changes (4001/4004) are deployed — see Backend Changes §3.
            // This branch is a transitional fallback for distinguishing auth/session failures from normal
            // closes before the backend emits distinct close codes.
            if (event.code === 1000 && !hasHadSuccessfulConnection.current) {
                setWsError('session_invalid');
                setConnState('failed');
                setSocket(null);
                return;
            }

            // 5. Retryable: 1006 (network loss), 1011 (server error), 1001 (going away), etc.
            const nextAttempt = retryAttemptRef.current + 1;
            if (nextAttempt > MAX_RETRIES) {
                console.warn(`[WS] Exhausted ${MAX_RETRIES} retries`);
                setWsError('connection_failed');
                setConnState('failed');
                setSocket(null);
                return;
            }

            retryAttemptRef.current = nextAttempt;
            setRetryAttempt(nextAttempt);
            setConnState('reconnecting');
            setSocket(null);

            const delay = calcBackoffDelay(nextAttempt - 1);
            console.log(`[WS] Scheduling retry ${nextAttempt}/${MAX_RETRIES} in ${delay}ms`);
            retryTimerRef.current = setTimeout(() => {
                connect(true);
            }, delay);
        };
    }, [scheduleStuckEvalPoll]);

    // ---- manual retry (called from WsConnectionBanner Retry button) ----
    const retryNow = useCallback(() => {
        clearAllTimers();
        retryAttemptRef.current = 0;
        setRetryAttempt(0);
        setWsError(null);
        setError(null);
        connect(false);
    }, [connect]);

    // ---- mark intentional close (called by WebSocketInterviewRoom) ----
    const markIntentionalClose = useCallback(() => {
        isIntentionalCloseRef.current = true;
    }, []);

    // ---- initial connection ----
    useEffect(() => {
        // Reset per-session state on a new sessionId
        hasHadSuccessfulConnection.current = false;
        retryAttemptRef.current = 0;
        setRetryAttempt(0);
        setWsError(null);
        setError(null);
        setConnState('idle');
        setQuestions([]);
        setCurrentIndex(0);
        setCurrentStreamedText('');

        connect(false);

        return () => {
            console.log('[WS] Unmounting — closing socket');
            isIntentionalCloseRef.current = true; // suppress reconnect on unmount
            clearAllTimers();
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
        };
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sessionId]);

    // ---- submit helper (sets tracking refs before sending) ----
    const sendAnswer = useCallback((questionId: string, answerText: string) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

        // Cancel any stale poll from a previous question's reconnect cycle
        clearStuckEvalPoll();
        lastSubmittedQuestionIdRef.current = questionId;
        setIsEvaluating(true);
        isEvaluatingRef.current = true;

        wsRef.current.send(JSON.stringify({
            event: 'submit_answer',
            data: { question_id: questionId, answer_text: answerText },
        }));
    }, []);

    const sendStartInterview = useCallback((jdText: string) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        wsRef.current.send(JSON.stringify({
            event: 'start_interview',
            data: { jd_text: jdText, limit: 5 },
        }));
    }, []);

    return {
        // connection
        connState,
        retryAttempt,
        elapsedMs,
        wsError,
        retryNow,
        markIntentionalClose,
        // interview
        socket,
        questions,
        setQuestions,
        currentIndex,
        setCurrentIndex,
        secondsLeft,
        setSecondsLeft,
        isEvaluating,
        setIsEvaluating,
        evalResult,
        setEvalResult,
        error,
        setError,
        currentStreamedText,
        setCurrentStreamedText,
        sendAnswer,
        sendStartInterview,
        // legacy compat
        connected: connState === 'connected',
    };
}
