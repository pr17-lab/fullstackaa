import { useState, useEffect, useRef } from 'react';

export function useWebSocketInterview(sessionId: string, onCompleted: () => void) {
    const [socket, setSocket] = useState<WebSocket | null>(null);
    const [connected, setConnected] = useState(false);
    const [questions, setQuestions] = useState<any[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [secondsLeft, setSecondsLeft] = useState(90); // QUESTION_TIME_SEC default
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [evalResult, setEvalResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [currentStreamedText, setCurrentStreamedText] = useState("");

    const questionsRef = useRef<any[]>([]);
    useEffect(() => {
        questionsRef.current = questions;
    }, [questions]);

    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws';
        const wsUrl = `${protocol}://${window.location.host}/api/interview/ws/interview/${sessionId}`;
        console.log("Connecting WebSocket to URL:", wsUrl);
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log("WebSocket connection established");
            setConnected(true);
            setError(null);
        };

        ws.onmessage = (event) => {
            const rawData = event.data;
            try {
                if (typeof rawData === 'string' && rawData.trim().startsWith('{') && rawData.trim().endsWith('}')) {
                    const msg = JSON.parse(rawData);
                    console.log("WebSocket event received:", msg.event, msg.data);
                    
                    if (msg.event === 'question_complete' || msg.event === 'session_ready') {
                        setCurrentStreamedText("");
                        setQuestions(msg.data.questions);
                        // Find first unanswered question
                        const unansweredIdx = msg.data.questions.findIndex((q: any) => !q.user_answer);
                        if (unansweredIdx !== -1) {
                            setCurrentIndex(unansweredIdx);
                        }
                    } else if (msg.event === 'answer_evaluated') {
                        setIsEvaluating(false);
                        setEvalResult(msg.data);
                        // Advance to next question after a 3 second delay showing results
                        setTimeout(() => {
                            setCurrentIndex(idx => {
                                const currentQuestions = questionsRef.current;
                                if (idx < currentQuestions.length - 1) {
                                    return idx + 1;
                                }
                                return idx;
                            });
                        }, 3000);
                    } else if (msg.event === 'session_completed') {
                        console.log("WebSocket session completed!");
                        onCompleted();
                    } else if (msg.event === 'error') {
                        setError(msg.data.message || 'An error occurred during interview generation');
                    }
                } else {
                    // Raw stream chunk!
                    setCurrentStreamedText(prev => prev + rawData);
                }
            } catch (err) {
                // Parse failed, fallback to treating as raw text token chunk
                setCurrentStreamedText(prev => prev + rawData);
            }
        };

        ws.onerror = (err) => {
            console.error("WebSocket connection error:", err);
            setError("Connection to interview server failed. Make sure server is running.");
        };

        ws.onclose = () => {
            console.log("WebSocket connection closed");
            setConnected(false);
        };

        setSocket(ws);

        return () => {
            ws.close();
        };
    }, [sessionId, onCompleted]);

    return {
        socket,
        connected,
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
    };
}
