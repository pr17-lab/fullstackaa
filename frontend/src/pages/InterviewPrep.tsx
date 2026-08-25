import React, {
    useState, useRef, useCallback, useEffect, useMemo,
} from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    Cpu, CheckCircle2, Clock, Sparkles,
    BookOpen, AlertCircle, Mic, MicOff, Square,
    Upload, FileText, X, SkipForward, Trophy,
    RotateCcw, Volume2, Trash2, ChevronDown, ChevronUp, RefreshCw, Loader2, Search
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    createSession, listSessions, getSession, submitAnswer, deleteSession, parseResumePdf, evaluateSession,
    getPracticeTopics, createPracticeTopicSession, getStudentProjects, createProjectSession
} from '../api/interview';
import type { InterviewSession, InterviewSessionSummary, EvaluationResult } from '../types/interview';
import type { TaxonomySearchResponse } from '../types/career';
import type { StudentProject } from '../api/interview';
import { Card, CardHeader, CardContent, CardTitle } from '../components/common/Card';
import { PageTransition } from '../components/layout/PageTransition';
import { useWebSocketInterview } from '../hooks/useWebSocketInterview';
import { WsConnectionBanner } from '../components/interview/WsConnectionBanner';
import { ReconnectToast } from '../components/interview/ReconnectToast';

// ---------------------------------------------------------------------------
// Web Speech API type augmentation
// ---------------------------------------------------------------------------
declare global {
    class SpeechRecognition extends EventTarget {
        continuous: boolean;
        interimResults: boolean;
        lang: string;
        onstart: (() => void) | null;
        onend: (() => void) | null;
        onerror: (() => void) | null;
        onresult: ((event: SpeechRecognitionEvent) => void) | null;
        start(): void;
        stop(): void;
        abort(): void;
    }
    class SpeechRecognitionEvent extends Event {
        readonly resultIndex: number;
        readonly results: SpeechRecognitionResultList;
    }
    interface Window {
        SpeechRecognition: typeof SpeechRecognition;
        webkitSpeechRecognition: typeof SpeechRecognition;
    }
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const QUESTION_TIME_SEC = 90;

// Topics removed â€” now JD-based

const DIFFICULTY_COLOR: Record<string, string> = {
    easy: 'text-emerald-400',
    medium: 'text-amber-400',
    hard: 'text-red-400',
};

const STATUS_COLOR: Record<string, string> = {
    active: 'text-indigo-400',
    completed: 'text-emerald-400',
    abandoned: 'text-gray-500 dark:text-zinc-500',
};

// ---------------------------------------------------------------------------
// Voice hook
// ---------------------------------------------------------------------------
interface UseVoiceReturn {
    supported: boolean;
    listening: boolean;
    interimText: string;
    finalText: string;
    startListening: () => void;
    stopListening: () => void;
    clearFinal: () => void;
}

function useVoice(): UseVoiceReturn {
    const recognitionRef = useRef<SpeechRecognition | null>(null);
    const [listening, setListening] = useState(false);
    const [interimText, setInterimText] = useState('');
    const [finalText, setFinalText] = useState('');

    const supported =
        typeof window !== 'undefined' &&
        !!(window.SpeechRecognition || window.webkitSpeechRecognition);

    const stopListening = useCallback(() => {
        recognitionRef.current?.stop();
    }, []);

    const startListening = useCallback(() => {
        if (!supported) return;
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        const rec = new SR();
        rec.continuous = true;
        rec.interimResults = true;
        rec.lang = 'en-US';

        rec.onstart = () => { setListening(true); setInterimText(''); };
        rec.onend = () => { setListening(false); setInterimText(''); };
        rec.onerror = () => { setListening(false); setInterimText(''); };

        rec.onresult = (event: SpeechRecognitionEvent) => {
            let interim = '';
            let final = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const t = event.results[i][0].transcript;
                if (event.results[i].isFinal) final += t + ' ';
                else interim += t;
            }
            setInterimText(interim);
            if (final) setFinalText(prev => {
                const sep = prev && !prev.endsWith(' ') ? ' ' : '';
                return prev + sep + final.trim();
            });
        };

        recognitionRef.current = rec;
        rec.start();
    }, [supported]);

    const clearFinal = useCallback(() => setFinalText(''), []);

    useEffect(() => () => { recognitionRef.current?.abort(); }, []);

    return { supported, listening, interimText, finalText, startListening, stopListening, clearFinal };
}

// ---------------------------------------------------------------------------
// Typewriter hook
// ---------------------------------------------------------------------------
function useTypewriter(text: string, speed = 22) {
    const [displayed, setDisplayed] = useState('');
    const [done, setDone] = useState(false);

    useEffect(() => {
        setDisplayed('');
        setDone(false);
        if (!text) return;
        let i = 0;
        const id = setInterval(() => {
            i++;
            setDisplayed(text.slice(0, i));
            if (i >= text.length) {
                clearInterval(id);
                setDone(true);
            }
        }, speed);
        return () => clearInterval(id);
    }, [text, speed]);

    return { displayed, done };
}

// ---------------------------------------------------------------------------
// Text-to-Speech hook
// ---------------------------------------------------------------------------
function useTTS() {
    const speak = useCallback((text: string, onEnd?: () => void) => {
        if (!window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        const utt = new SpeechSynthesisUtterance(text);
        utt.rate = 0.95;
        utt.pitch = 1;
        utt.lang = 'en-US';
        if (onEnd) {
            utt.onend = () => onEnd();
        }
        window.speechSynthesis.speak(utt);
    }, []);

    const cancel = useCallback(() => {
        window.speechSynthesis?.cancel();
    }, []);

    useEffect(() => () => { window.speechSynthesis?.cancel(); }, []);

    return { speak, cancel };
}

// ---------------------------------------------------------------------------
// Markdown code-block splitter & renderer
// ---------------------------------------------------------------------------
const renderQuestionText = (text: string, done: boolean) => {
    if (!text.includes('```')) {
        return (
            <p className="text-lg text-gray-900 dark:text-zinc-100 leading-relaxed font-medium min-h-[3rem] whitespace-pre-wrap text-left">
                {text}
                {!done && <span className="inline-block w-0.5 h-5 bg-indigo-400 animate-pulse ml-0.5 align-middle" />}
            </p>
        );
    }
    const parts = text.split('```');
    return (
        <div className="text-lg text-gray-900 dark:text-zinc-100 leading-relaxed font-medium min-h-[3rem] text-left">
            {parts.map((part, index) => {
                if (index % 2 === 1) {
                    // Code block
                    const lines = part.split('\n');
                    let lang = '';
                    let code = part;
                    if (lines[0] && /^[a-zA-Z0-9_-]+$/.test(lines[0].trim())) {
                        lang = lines[0].trim();
                        code = lines.slice(1).join('\n');
                    }
                    return (
                        <div key={index} className="my-4 rounded-xl overflow-hidden border border-zinc-200 dark:border-zinc-800 bg-zinc-950 p-4 font-mono text-[11px] sm:text-xs text-indigo-300 whitespace-pre overflow-x-auto text-left shadow-inner">
                            {lang && (
                                <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider mb-2 border-b border-zinc-900 pb-1 select-none">
                                    {lang}
                                </div>
                            )}
                            <code>{code.trim()}</code>
                        </div>
                    );
                }
                const isLastPart = index === parts.length - 1;
                return (
                    <span key={index} className="whitespace-pre-wrap">
                        {part}
                        {isLastPart && !done && (
                            <span className="inline-block w-0.5 h-5 bg-indigo-400 animate-pulse ml-0.5 align-middle" />
                        )}
                    </span>
                );
            })}
        </div>
    );
};

// ---------------------------------------------------------------------------
// Timer ring
// ---------------------------------------------------------------------------
function TimerRing({ seconds, total }: { seconds: number; total: number }) {
    const r = 28;
    const circ = 2 * Math.PI * r;
    const frac = Math.max(0, seconds / total);
    const low = seconds <= 15;
    return (
        <div className="relative flex items-center justify-center w-20 h-20">
            <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 64 64">
                <circle cx="32" cy="32" r={r} stroke="rgba(255,255,255,0.08)" strokeWidth="4" fill="none" />
                <circle
                    cx="32" cy="32" r={r}
                    stroke={low ? '#ef4444' : '#6366f1'}
                    strokeWidth="4" fill="none"
                    strokeDasharray={circ}
                    strokeDashoffset={circ * (1 - frac)}
                    style={{ transition: 'stroke-dashoffset 1s linear, stroke 0.5s' }}
                    strokeLinecap="round"
                />
            </svg>
            <span className={`text-xl font-bold tabular-nums ${low ? 'text-red-400' : 'text-gray-900 dark:text-zinc-100'}`}>
                {seconds}
            </span>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Mic button
// ---------------------------------------------------------------------------
function MicButton({
    listening, onStart, onStop, supported,
}: {
    listening: boolean;
    onStart: () => void;
    onStop: () => void;
    supported: boolean;
}) {
    if (!supported) return (
        <div className="flex flex-col items-center gap-2 opacity-50">
            <div className="w-24 h-24 rounded-full bg-gray-100 dark:bg-zinc-700 flex items-center justify-center">
                <MicOff className="h-10 w-10 text-gray-600 dark:text-zinc-400" />
            </div>
            <p className="text-xs text-gray-500 dark:text-zinc-500">Voice not supported</p>
        </div>
    );

    return (
        <div className="relative">
            {listening && (
                <div className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-75 pointer-events-none scale-105" />
            )}
            <button
                type="button"
                onClick={listening ? onStop : onStart}
                className={`relative w-28 h-28 rounded-full flex flex-col items-center justify-center gap-2 font-semibold text-sm transition-all duration-200 shadow-xl focus:outline-none focus:ring-4 ${listening
                    ? 'bg-red-500 hover:bg-red-600 text-white ring-red-400/40'
                    : 'bg-indigo-600 hover:bg-indigo-500 text-white ring-indigo-400/40'
                    }`}
            >
                {listening
                    ? <><Square className="h-8 w-8 animate-pulse text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]" /><span>Stop</span></>
                    : <><Mic className="h-8 w-8" /><span>Speak</span></>
                }
            </button>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Session history item
// ---------------------------------------------------------------------------
function SessionHistoryItem({
    summary, onClick, active, onDelete, isDeleting,
}: {
    summary: InterviewSessionSummary;
    onClick: () => void;
    active: boolean;
    onDelete: (e: React.MouseEvent) => void;
    isDeleting: boolean;
}) {
    return (
        <div
            className={`relative group w-full text-left px-4 py-3 rounded-xl border transition-all ${active
                ? 'border-indigo-300 dark:border-indigo-500/60 bg-indigo-50 dark:bg-indigo-900/20'
                : 'border-gray-200 dark:border-zinc-700 bg-gray-50/50 dark:bg-zinc-800/50 hover:border-indigo-500/40'
                }`}
        >
            {/* Clickable main area */}
            <button
                id={`session-${summary.id}`}
                onClick={onClick}
                className="w-full text-left"
            >
                <div className="flex items-center justify-between pr-6">
                    <span className="text-sm font-medium text-gray-900 dark:text-zinc-100 truncate">
                        {summary.topic ?? summary.branch}
                    </span>
                    <span className={`text-xs font-semibold ml-2 flex-shrink-0 ${STATUS_COLOR[summary.status] ?? ''}`}>
                        {summary.status}
                    </span>
                </div>
                <div className="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-zinc-500">
                    <span>{summary.question_count} questions</span>
                    {summary.created_at && (
                        <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {new Date(summary.created_at).toLocaleDateString()}
                        </span>
                    )}
                </div>
            </button>

            {/* Delete button â€” visible on hover */}
            <button
                id={`delete-session-${summary.id}`}
                type="button"
                onClick={onDelete}
                disabled={isDeleting}
                title="Delete session"
                className="absolute top-2.5 right-2.5 p-1.5 rounded-lg text-gray-500 dark:text-zinc-600 hover:text-red-400 hover:bg-red-900/20 opacity-0 group-hover:opacity-100 transition-all disabled:opacity-30"
            >
                <Trash2 className="h-3.5 w-3.5" />
            </button>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Phases
// ---------------------------------------------------------------------------
type Phase = 'lobby' | 'interview' | 'results';

// ---------------------------------------------------------------------------
// LOBBY
// -------------------------------------------------------------------
function Lobby({
    jdText, onJdChange,
    onStart, isStarting, startError,
    sessions, sessionsLoading,
    onSelectSession,
    onDelete, deletingId,
    activeSessionId,
    topics,
    topicsLoading,
    onStartTopic,
    projects,
    projectsLoading,
    onStartProject,
}: {
    jdText: string;
    onJdChange: (t: string) => void;
    onStart: () => void;
    isStarting: boolean;
    startError: boolean;
    sessions: InterviewSessionSummary[];
    sessionsLoading: boolean;
    onSelectSession: (id: string) => void;
    onDelete: (id: string) => void;
    deletingId: string | null;
    activeSessionId: string | null;
    topics: TaxonomySearchResponse[];
    topicsLoading: boolean;
    onStartTopic: (skillId: string) => void;
    projects: StudentProject[];
    projectsLoading: boolean;
    onStartProject: (projectId: string) => void;
}) {
    const hasJd = jdText.trim().length > 20;
    const [activeTab, setActiveTab] = useState<'jd' | 'topic' | 'project'>('jd');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null);
    const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

    const filteredTopics = useMemo(() => {
        if (!searchQuery.trim()) return topics;
        return topics.filter(t => 
            t.skill_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            t.category.toLowerCase().includes(searchQuery.toLowerCase())
        );
    }, [topics, searchQuery]);

    const selectedTopic = useMemo(() => {
        return topics.find(t => t.id === selectedTopicId) || null;
    }, [topics, selectedTopicId]);

    const isStartDisabled = useMemo(() => {
        if (activeTab === 'jd') return false;
        if (activeTab === 'topic') return !selectedTopicId;
        if (activeTab === 'project') return !selectedProjectId;
        return true;
    }, [activeTab, selectedTopicId, selectedProjectId]);

    const startHint = useMemo(() => {
        if (activeTab === 'jd') return null;
        if (activeTab === 'topic' && !selectedTopicId) return "Select a topic above to start.";
        if (activeTab === 'project' && !selectedProjectId) return "Select a project above to start.";
        return null;
    }, [activeTab, selectedTopicId, selectedProjectId]);

    const handleStartClick = () => {
        if (activeTab === 'jd') {
            onStart();
        } else if (activeTab === 'topic' && selectedTopicId) {
            onStartTopic(selectedTopicId);
        } else if (activeTab === 'project' && selectedProjectId) {
            onStartProject(selectedProjectId);
        }
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Setup panel */}
            <div className="lg:col-span-2 space-y-5">
                {/* Header */}
                <Card variant="default">
                    <CardHeader className="flex flex-row items-center gap-4">
                        <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center shadow-md">
                            <Cpu className="h-6 w-6 text-white" />
                        </div>
                        <div>
                            <CardTitle>AI Interview</CardTitle>
                            <p className="text-sm text-gray-500 dark:text-zinc-500 dark:text-zinc-400 font-medium">Voice-only &bull; Real-time &bull; Personalised</p>
                        </div>
                    </CardHeader>
                </Card>

                {/* Mode Selector Tabs */}
                <div className="flex border-b border-gray-200 dark:border-zinc-700">
                    <button
                        type="button"
                        onClick={() => setActiveTab('jd')}
                        className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-all ${
                            activeTab === 'jd'
                                ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                                : 'border-transparent text-gray-500 dark:text-zinc-500 hover:text-gray-700 dark:hover:text-zinc-300'
                        }`}
                    >
                        JD-Based
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab('topic')}
                        className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-all ${
                            activeTab === 'topic'
                                ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                                : 'border-transparent text-gray-500 dark:text-zinc-500 hover:text-gray-700 dark:hover:text-zinc-300'
                        }`}
                    >
                        Practice a Topic
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab('project')}
                        className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-all ${
                            activeTab === 'project'
                                ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                                : 'border-transparent text-gray-500 dark:text-zinc-500 hover:text-gray-700 dark:hover:text-zinc-300'
                        }`}
                    >
                        Practice a Project
                    </button>
                </div>

                {/* Mode Description Subtext */}
                <p className="text-xs text-gray-500 dark:text-zinc-400 font-medium leading-none">
                    {activeTab === 'jd' && "Simulate a real interview for a specific job description."}
                    {activeTab === 'topic' && "Practice one skill at a time."}
                    {activeTab === 'project' && "Get asked about a specific project you've built."}
                </p>

                {activeTab === 'jd' && (
                    <Card variant="elevated" className="!bg-[var(--bg-card)] border-indigo-500/30 shadow-none">
                        <CardHeader className="pb-3 flex flex-row items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Sparkles className="h-5 w-5 text-indigo-500 dark:text-indigo-400" />
                                <CardTitle>Job Description</CardTitle>
                            </div>
                            <span className="text-xs font-medium text-gray-500 dark:text-zinc-500 bg-zinc-100 dark:bg-zinc-800 px-2 py-1 rounded-md">Optional</span>
                        </CardHeader>
                        <CardContent className="pt-0">
                            <textarea
                                id="jd-input"
                                rows={8}
                                value={jdText}
                                onChange={e => onJdChange(e.target.value)}
                                placeholder={`Paste the full job description here (optional).

Example:
  We are looking for a Backend Engineer...
  Requirements:
  - 2+ years with Python / FastAPI
  - PostgreSQL, Redis, Docker
  - Understanding of REST API design
  ...

The AI will tailor every question to this JD.`}
                                className="w-full rounded-xl border border-[var(--border-primary)] bg-[var(--bg-surface)] text-[var(--text-primary)] text-sm px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500/60 placeholder:text-[var(--text-tertiary)]"
                            />
                            {hasJd && (
                                <p className="text-xs text-emerald-400 flex items-center gap-1 mt-2">
                                    <CheckCircle2 className="h-3.5 w-3.5" />
                                    JD loaded
                                </p>
                            )}
                        </CardContent>
                    </Card>
                )}

                {activeTab === 'topic' && (
                    <Card variant="elevated" className="!bg-[var(--bg-card)] border-indigo-500/30 shadow-none">
                        <CardHeader className="pb-3">
                            <div className="flex items-center gap-2">
                                <BookOpen className="h-5 w-5 text-indigo-500 dark:text-indigo-400" />
                                <CardTitle>Select a Topic</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="pt-0 space-y-4">
                            <div className="relative">
                                <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Search topics (e.g. React, PostgreSQL, Docker)..."
                                    value={searchQuery}
                                    onChange={e => setSearchQuery(e.target.value)}
                                    className="w-full pl-9 pr-4 py-2 text-sm rounded-xl border border-[var(--border-primary)] bg-[var(--bg-surface)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/60 placeholder:text-[var(--text-tertiary)]"
                                />
                            </div>

                            {topicsLoading ? (
                                <div className="flex flex-col items-center justify-center py-8 space-y-2 text-gray-500 dark:text-zinc-400">
                                    <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
                                    <p className="text-xs">Loading practiceable topics...</p>
                                </div>
                            ) : filteredTopics.length === 0 ? (
                                <div className="text-center py-8 text-sm text-gray-500 dark:text-zinc-500 border border-dashed border-gray-200 dark:border-zinc-700 rounded-xl">
                                    No matching topics found
                                </div>
                            ) : (
                                <div className="max-h-64 overflow-y-auto grid grid-cols-1 sm:grid-cols-2 gap-2 pr-1 custom-scrollbar">
                                    {filteredTopics.map(topic => (
                                        <button
                                            key={topic.id}
                                            type="button"
                                            onClick={() => setSelectedTopicId(topic.id)}
                                            className={`flex flex-col items-start text-left p-3 rounded-xl border transition-all ${
                                                selectedTopicId === topic.id
                                                    ? 'border-indigo-500 bg-indigo-500/10'
                                                    : 'border-[var(--border-primary)] hover:border-indigo-500/40 bg-[var(--bg-surface)]'
                                            }`}
                                        >
                                            <span className="text-sm font-semibold text-[var(--text-primary)]">
                                                {topic.skill_name}
                                            </span>
                                            <span className="text-xs text-[var(--text-secondary)] mt-1 capitalize">
                                                {topic.category}
                                            </span>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )}

                {activeTab === 'project' && (
                    <Card variant="elevated" className="!bg-[var(--bg-card)] border-indigo-500/30 shadow-none">
                        <CardHeader className="pb-3">
                            <div className="flex items-center gap-2">
                                <Cpu className="h-5 w-5 text-indigo-500 dark:text-indigo-400" />
                                <CardTitle>Select a Project</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="pt-0 space-y-4">
                            {projectsLoading ? (
                                <div className="flex flex-col items-center justify-center py-8 space-y-2 text-gray-500 dark:text-zinc-400">
                                    <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
                                    <p className="text-xs">Loading projects...</p>
                                </div>
                            ) : projects.length === 0 ? (
                                <div className="text-center py-8 text-sm text-gray-500 dark:text-zinc-500 border border-dashed border-gray-200 dark:border-zinc-700 rounded-xl">
                                    No projects connected yet.
                                </div>
                            ) : (
                                <div className="max-h-64 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
                                    {projects.map(project => {
                                        const tech = project.extracted_skills || project.tech_stack || [];
                                        return (
                                            <button
                                                key={project.id}
                                                type="button"
                                                onClick={() => setSelectedProjectId(project.id)}
                                                className={`w-full flex flex-col items-start text-left p-4 rounded-xl border transition-all ${
                                                    selectedProjectId === project.id
                                                        ? 'border-indigo-500 bg-indigo-500/10'
                                                        : 'border-[var(--border-primary)] hover:border-indigo-500/40 bg-[var(--bg-surface)]'
                                                }`}
                                            >
                                                <div className="flex items-center justify-between w-full">
                                                    <span className="text-sm font-semibold text-[var(--text-primary)]">
                                                        {project.title}
                                                    </span>
                                                    {project.analyzed_at && (
                                                        <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900/30 flex items-center gap-0.5">
                                                            Structurally Verified
                                                        </span>
                                                    )}
                                                </div>
                                                {tech.length > 0 && (
                                                    <div className="flex flex-wrap gap-1 mt-2">
                                                        {tech.map((t, idx) => (
                                                            <span key={idx} className="px-2 py-0.5 rounded bg-gray-100 dark:bg-zinc-800 text-[10px] font-medium text-gray-600 dark:text-zinc-400 capitalize">
                                                                {t}
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}
                                            </button>
                                        );
                                    })}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Start button */}
                <div className="flex flex-col items-start gap-2">
                    <button
                        id="create-session-btn"
                        onClick={handleStartClick}
                        disabled={isStarting || isStartDisabled}
                        className="flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition shadow-lg shadow-indigo-200 dark:shadow-indigo-900/40 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isStarting ? (
                            <>
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Generating questions...
                            </>
                        ) : (
                            <>
                                <Sparkles className="h-4 w-4" />
                                Start Interview
                            </>
                        )}
                    </button>
                    {startHint && (
                        <p className="text-xs text-red-500 font-semibold mt-1">
                            {startHint}
                        </p>
                    )}
                </div>

                {startError && (
                    <div className="rounded-xl border border-red-700/40 bg-red-900/10 px-4 py-3 text-sm text-red-400 flex items-center gap-2">
                        <AlertCircle className="h-4 w-4 flex-shrink-0" />
                        Failed to start session. Please try again.
                    </div>
                )}

                {/* Instructions */}
                <div className="rounded-2xl border border-[var(--border-primary)] bg-[var(--bg-surface)] p-5 space-y-3">
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">How it works</h3>
                    <div className="grid grid-cols-3 gap-4 text-center">
                        {[
                            { num: '1', label: 'Prepare Topic/JD', sub: 'Select a direct topic, project or paste a JD' },
                            { num: '2', label: 'Speak Answers', sub: 'Voice-only, no typing' },
                            { num: '3', label: 'See Results', sub: 'Full Q&A summary at the end' },
                        ].map((step, i) => (
                            <div key={i} className="rounded-xl bg-[var(--bg-card)] border border-[var(--border-primary)] p-4 space-y-2">
                                <div className="h-8 w-8 rounded-full bg-indigo-500/15 text-indigo-400 flex items-center justify-center font-bold text-sm mx-auto">
                                    {step.num}
                                </div>
                                <p className="text-xs font-semibold text-[var(--text-primary)]">{step.label}</p>
                                <p className="text-xs text-[var(--text-secondary)] mt-1 leading-relaxed">{step.sub}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Session history sidebar */}
            <div className="space-y-3">
                <h2 className="text-sm font-semibold text-gray-600 dark:text-zinc-400 flex items-center gap-2">
                    <BookOpen className="h-4 w-4" /> Past Sessions
                </h2>
                {sessionsLoading ? (
                    <div className="space-y-2">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-16 rounded-xl bg-gray-50 dark:bg-zinc-800 animate-pulse" />
                        ))}
                    </div>
                ) : sessions.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-gray-200 dark:border-zinc-700 p-8 text-center text-gray-500 dark:text-zinc-500 space-y-2">
                        <p className="text-sm font-semibold text-gray-700 dark:text-zinc-300">Your first session will show up here</p>
                        <p className="text-xs text-gray-500 dark:text-zinc-500">Most students start with a topic-based practice interview before a full JD simulation.</p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {sessions.map(s => (
                            <SessionHistoryItem
                                key={s.id}
                                summary={s}
                                active={s.id === activeSessionId}
                                onClick={() => onSelectSession(s.id)}
                                onDelete={(e) => { e.stopPropagation(); onDelete(s.id); }}
                                isDeleting={deletingId === s.id}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div >
    );
}

// ---------------------------------------------------------------------------
// INTERVIEW ROOM
// ---------------------------------------------------------------------------
function InterviewRoom({
    session,
    currentIndex,
    onAnswered,
    onSkip,
}: {
    session: InterviewSession;
    currentIndex: number;
    onAnswered: (qId: string, answer: string, completed: boolean) => void;
    onSkip: () => void;
}) {
    const question = session.questions[currentIndex];
    const total = session.questions.length;

    // Keep onSkip in a ref so the timer effect never needs it as a dependency.
    // Without this, every skip would create a new onSkip â†’ re-trigger the timer
    // effect with secondsLeft still at 0 â†’ immediately skip again (repeat loop).
    const onSkipRef = useRef(onSkip);
    useEffect(() => { onSkipRef.current = onSkip; }, [onSkip]);

    // Timer
    const [secondsLeft, setSecondsLeft] = useState(QUESTION_TIME_SEC);
    useEffect(() => {
        setSecondsLeft(QUESTION_TIME_SEC);
    }, [currentIndex]);

    useEffect(() => {
        if (secondsLeft <= 0) { onSkipRef.current(); return; }
        const t = setTimeout(() => setSecondsLeft(s => s - 1), 1000);
        return () => clearTimeout(t);
    }, [secondsLeft]);

    // Typewriter
    const { displayed, done } = useTypewriter(question?.question ?? '', 20);

    // TTS – speak the question once the typewriter finishes.
    // IMPORTANT: The cancel effect MUST be declared BEFORE the speak effect.
    // React runs effects in declaration order, so cancel fires first on currentIndex
    // change, stopping old speech. Then the speak effect sees done=false (typewriter
    // has already reset) and does nothing. When the typewriter finishes (done=true),
    // the speak effect fires and reads the new question exactly once.
    const { speak, cancel } = useTTS();
    const spokenIndexRef = useRef<number>(-1);
    // 1. Cancel old speech + reset guard when question changes
    useEffect(() => {
        cancel();
        spokenIndexRef.current = -1;
    }, [currentIndex, cancel]);
    // 2. Speak once the typewriter is done, guarded so it only fires once per question
    useEffect(() => {
        if (done && question?.question && spokenIndexRef.current !== currentIndex) {
            spokenIndexRef.current = currentIndex;
            speak(question.question);
        }
    }, [done, question?.question, currentIndex, speak]);

    // Voice
    const { supported, listening, interimText, finalText, startListening, stopListening, clearFinal } = useVoice();

    const answerMutation = useMutation({
        mutationFn: () => submitAnswer(session.id, question.id, finalText.trim()),
        onSuccess: (data) => {
            onAnswered(question.id, finalText.trim(), data.session_completed);
            clearFinal();
            stopListening();
        },
    });

    const canSubmit = finalText.trim().length > 0 && !answerMutation.isPending;

    if (!question) return null;



    return (
        <div className="min-h-[70vh] flex flex-col">
            {/* Top bar */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <span className="text-xs font-semibold text-gray-500 dark:text-zinc-500 uppercase tracking-wider">
                        {session.branch}{session.topic ? ` Â· ${session.topic}` : ''}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${DIFFICULTY_COLOR[question.difficulty] ?? 'text-gray-600 dark:text-zinc-400'} bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700`}>
                        {question.difficulty}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-zinc-500 bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 px-2 py-0.5 rounded-full">
                        {question.topic}
                    </span>
                </div>
                <span className="text-sm font-semibold text-gray-700 dark:text-zinc-300 bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 px-3 py-1 rounded-full">
                    Q {currentIndex + 1} / {total}
                </span>
            </div>

            {/* Progress bar */}
            <div className="h-1 rounded-full bg-gray-50 dark:bg-zinc-800 mb-8 overflow-hidden">
                <div
                    className="h-full rounded-full bg-indigo-500 transition-all duration-500"
                    style={{ width: `${((currentIndex) / total) * 100}%` }}
                />
            </div>

            {/* Main card */}
            <div className="flex-1 flex flex-col items-center justify-center gap-8">
                {/* Question */}
                <div className="w-full max-w-3xl rounded-2xl border border-gray-200 dark:border-zinc-700 bg-gray-50/60 dark:bg-zinc-800/60 p-8">
                    <div className="flex items-start gap-4">
                        <div className="flex-shrink-0 h-9 w-9 rounded-full bg-indigo-50 dark:bg-indigo-900/60 border border-indigo-200 dark:border-indigo-700/50 text-indigo-600 dark:text-indigo-300 flex items-center justify-center text-sm font-bold">
                            {currentIndex + 1}
                        </div>
                        <div className="flex-1">
                            {renderQuestionText(displayed, done)}
                            {done && (
                                <button
                                    type="button"
                                    onClick={() => speak(question.question)}
                                    title="Replay question"
                                    className="mt-3 flex items-center gap-1.5 text-xs text-gray-500 dark:text-zinc-500 hover:text-indigo-400 transition"
                                >
                                    <Volume2 className="h-3.5 w-3.5" /> Replay question
                                </button>
                            )}
                        </div>
                    </div>
                    {/* Follow-up hint — shown once typewriter finishes */}
                    {done && question.follow_up && (
                        <div className="mt-4 flex items-start gap-2 border-t border-gray-200 dark:border-zinc-700 pt-4">
                            <span className="text-xs font-semibold text-indigo-500 dark:text-indigo-400 flex-shrink-0 mt-0.5">Follow-up:</span>
                            <p className="text-sm text-gray-500 dark:text-zinc-400 italic">{question.follow_up}</p>
                        </div>
                    )}
                </div>

                {/* Timer + Mic */}
                <div className="flex flex-col items-center gap-6">
                    <TimerRing seconds={secondsLeft} total={QUESTION_TIME_SEC} />

                    <MicButton
                        listening={listening}
                        onStart={startListening}
                        onStop={stopListening}
                        supported={supported}
                    />

                    {/* Live caption */}
                    <div className="w-full max-w-2xl min-h-[3.5rem] rounded-xl border border-gray-200 dark:border-zinc-700 bg-white/50 dark:bg-zinc-900/50 px-5 py-3 text-sm">
                        {finalText ? (
                            <p className="text-gray-800 dark:text-zinc-200">{finalText}</p>
                        ) : interimText ? (
                            <p className="text-indigo-400 italic">{interimText}</p>
                        ) : (
                            <p className="text-gray-500 dark:text-zinc-600 italic">
                                {listening ? 'Listening... speak your answer' : 'Press Speak to record your answer'}
                            </p>
                        )}
                        {listening && (
                            <span className="inline-flex items-center gap-1 text-xs text-red-400 mt-1">
                                <span className="h-1.5 w-1.5 rounded-full bg-red-500 animate-pulse" /> Recording
                            </span>
                        )}
                    </div>

                    {/* Action row */}
                    <div className="flex items-center gap-4">
                        <button
                            type="button"
                            onClick={() => {
                                stopListening();
                                clearFinal();
                                onSkip();
                            }}
                            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-gray-500 dark:text-zinc-500 hover:text-gray-700 dark:hover:text-gray-700 dark:text-zinc-300 hover:bg-gray-100 dark:hover:bg-gray-50 dark:bg-zinc-800 text-sm font-medium transition"
                        >
                            <SkipForward className="h-4 w-4" /> Skip
                        </button>

                        <button
                            id="submit-answer-btn"
                            type="button"
                            disabled={!canSubmit}
                            onClick={() => {
                                if (listening) stopListening();
                                answerMutation.mutate();
                            }}
                            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition disabled:opacity-40 shadow-lg shadow-indigo-200 dark:shadow-indigo-900/30"
                        >
                            <Volume2 className="h-4 w-4" />
                            {answerMutation.isPending ? 'Saving...' : 'Submit Answer'}
                        </button>

                        {finalText && (
                            <button
                                type="button"
                                onClick={() => { clearFinal(); if (listening) stopListening(); }}
                                className="p-2 rounded-xl text-gray-500 dark:text-zinc-600 hover:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-50 dark:bg-zinc-800 transition"
                                title="Clear recording"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        )}
                    </div>

                    {answerMutation.isError && (
                        <p className="text-xs text-red-400 flex items-center gap-1">
                            <AlertCircle className="h-3.5 w-3.5" /> Failed to save. Try again.
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
}

function QuestionCard({ q, i }: { q: any, i: number }) {
    const [showModel, setShowModel] = useState(false);
    return (
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="rounded-xl border border-gray-200 dark:border-zinc-700 bg-gray-50/40 dark:bg-zinc-800/40 p-5"
        >
            <div className="flex items-start gap-4">
                <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span className="text-sm font-semibold text-gray-900 dark:text-zinc-100">{i + 1}. {q.question}</span>
                    </div>
                    <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs text-gray-500 dark:text-zinc-500 bg-gray-200 dark:bg-zinc-700 px-2 py-0.5 rounded">{q.topic}</span>
                        <span className={`text-xs font-medium ${DIFFICULTY_COLOR[q.difficulty]}`}>{q.difficulty}</span>
                    </div>

                    {/* Follow-up question */}
                    {q.follow_up && (
                        <div className="flex items-start gap-2 rounded-lg bg-indigo-50/60 dark:bg-indigo-900/10 border border-indigo-100 dark:border-indigo-800/30 px-3 py-2">
                            <span className="text-xs font-semibold text-indigo-500 dark:text-indigo-400 flex-shrink-0 mt-0.5">Follow-up:</span>
                            <p className="text-xs text-indigo-800 dark:text-indigo-300 italic">{q.follow_up}</p>
                        </div>
                    )}
                    
                    <div className="rounded-lg bg-gray-100 dark:bg-zinc-900 border border-gray-200/50 dark:border-zinc-700/50 px-3 py-2">
                        <p className="text-xs text-gray-500 dark:text-zinc-500 mb-1">Your Answer:</p>
                        {q.user_answer ? (
                            <p className="text-sm text-gray-700 dark:text-zinc-300 italic">"{q.user_answer}"</p>
                        ) : (
                            <p className="text-sm text-gray-400 dark:text-zinc-600 italic">Skipped</p>
                        )}
                    </div>
                    
                    {q.ai_score != null && (
                        <div className="pt-3 border-t border-gray-200 dark:border-zinc-700 space-y-3">
                            {/* Score + Verdict */}
                            <div className="flex items-center gap-3 flex-wrap">
                                <div className={`flex items-center justify-center h-8 w-8 rounded-full border-2 ${Number(q.ai_score) >= 7 ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400' : Number(q.ai_score) >= 4 ? 'border-amber-500 text-amber-600 dark:text-amber-400' : 'border-red-500 text-red-600 dark:text-red-400'} font-bold text-xs`}>
                                    {q.ai_score}
                                </div>
                                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                                    q.ai_verdict === 'Strong' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400' :
                                    q.ai_verdict === 'Adequate' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400' :
                                    'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400'
                                }`}>
                                    {q.ai_verdict}
                                </span>
                            </div>
                            
                            {/* Feedback */}
                            <p className="text-sm text-gray-800 dark:text-zinc-200">
                                {q.ai_feedback}
                            </p>

                            {/* Mistakes */}
                            {q.mistakes && q.mistakes.length > 0 && (
                                <div className="rounded-lg bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-800/30 p-3 space-y-1">
                                    <p className="text-xs font-semibold text-red-700 dark:text-red-400 uppercase tracking-wide mb-2">Issues Found</p>
                                    <ul className="space-y-1">
                                        {q.mistakes.map((m: string, idx: number) => (
                                            <li key={idx} className="flex items-start gap-2 text-sm text-red-800 dark:text-red-300">
                                                <span className="mt-1 flex-shrink-0 h-1.5 w-1.5 rounded-full bg-red-500" />
                                                {m}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Improvement tip */}
                            {q.improvement && (
                                <div className="rounded-lg bg-amber-50 dark:bg-amber-900/10 border border-amber-100 dark:border-amber-800/30 px-3 py-2.5 flex items-start gap-2">
                                    <span className="text-amber-500 mt-0.5 flex-shrink-0">💡</span>
                                    <p className="text-sm text-amber-900 dark:text-amber-200">{q.improvement}</p>
                                </div>
                            )}
                            
                            <button
                                onClick={() => setShowModel(!showModel)}
                                className="flex items-center gap-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 transition-colors pt-1"
                            >
                                {showModel ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                                See Model Answer
                            </button>
                            
                            <AnimatePresence>
                                {showModel && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        className="overflow-hidden"
                                    >
                                        <div className="mt-2 rounded-lg bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800/30 p-3">
                                            <p className="text-sm text-indigo-900 dark:text-indigo-200">
                                                {q.model_answer}
                                            </p>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
}

function formatExistingEvaluation(session: InterviewSession): EvaluationResult {
    const evaluatedQuestions = session.questions.filter(q => q.ai_score != null);
    const scores = evaluatedQuestions.map(q => Number(q.ai_score));
    const strong_count = evaluatedQuestions.filter(q => q.ai_verdict === 'Strong').length;
    const adequate_count = evaluatedQuestions.filter(q => q.ai_verdict === 'Adequate').length;
    const weak_count = evaluatedQuestions.filter(q => q.ai_verdict === 'Weak').length;
    let avg_score = 0;
    if (scores.length > 0) {
        avg_score = Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10;
    }
    const overall_verdict = avg_score >= 7 ? 'Strong' : avg_score >= 4 ? 'Adequate' : 'Needs Improvement';

    return {
        session_id: session.id,
        total_questions: session.questions.length,
        avg_score,
        strong_count,
        adequate_count,
        weak_count,
        overall_verdict,
        // Derive weak_skills client-side the same way the backend does (score < 5)
        weak_skills: (() => {
            const topicCounts: Record<string, number> = {};
            session.questions.forEach(q => {
                if (q.ai_score !== null && q.ai_score !== undefined && Number(q.ai_score) < 5 && q.topic) {
                    topicCounts[q.topic] = (topicCounts[q.topic] || 0) + 1;
                }
            });
            return Object.entries(topicCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5)
                .map(([topic]) => topic);
        })(),
        questions: session.questions.map(q => ({
            question_id: q.id,
            question: q.question,
            topic: q.topic || '',
            difficulty: q.difficulty,
            follow_up: q.follow_up,
            user_answer: q.user_answer || '',
            ai_score: Number(q.ai_score || 0),
            ai_verdict: q.ai_verdict as any || 'Weak',
            ai_feedback: q.ai_feedback || '',
            model_answer: q.model_answer || '',
            mistakes: q.mistakes,
            improvement: q.improvement,
        }))
    };
}

function ResultsScreen({
    session,
    evaluationData,
    onNewInterview,
    onEvaluate,
    isEvaluating,
    evaluateError,
}: {
    session: InterviewSession;
    evaluationData: EvaluationResult | null;
    onNewInterview: () => void;
    onEvaluate: () => void;
    isEvaluating: boolean;
    evaluateError: boolean;
}) {
    const total = session.questions.length;
    const answered = session.questions.filter(q => q.user_answer).length;
    const pct = Math.round((answered / total) * 100);
    
    // We already have evaluationData if evaluated
    const isEvaluated = !!evaluationData;

    return (
        <div className="max-w-3xl mx-auto space-y-8">
            {/* Score card */}
            <div className="rounded-2xl border border-gray-200 dark:border-zinc-700 bg-gray-50/60 dark:bg-zinc-800/60 p-8 text-center space-y-4">
                <Trophy className="h-12 w-12 text-amber-400 mx-auto" />
                <h2 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">Interview Complete!</h2>
                <div className="flex items-center justify-center gap-6">
                    <div>
                        <p className="text-4xl font-bold text-indigo-400">{answered}<span className="text-gray-500 dark:text-zinc-500 text-2xl">/{total}</span></p>
                        <p className="text-sm text-gray-600 dark:text-zinc-400 mt-1">Questions answered</p>
                    </div>
                    <div className="h-12 w-px bg-gray-100 dark:bg-zinc-700" />
                    <div>
                        <p className="text-4xl font-bold text-emerald-400">{pct}%</p>
                        <p className="text-sm text-gray-600 dark:text-zinc-400 mt-1">Completion rate</p>
                    </div>
                </div>
                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-4">
                    <button
                        onClick={onNewInterview}
                        className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gray-200 dark:bg-zinc-700 hover:bg-gray-300 dark:hover:bg-zinc-600 text-gray-800 dark:text-zinc-200 text-sm font-semibold transition"
                    >
                        <RotateCcw className="h-4 w-4" /> New Interview
                    </button>
                    {!isEvaluated && (
                        <button
                            onClick={onEvaluate}
                            disabled={isEvaluating}
                            className={`inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-white text-sm font-semibold transition disabled:opacity-50 bg-indigo-600 hover:bg-indigo-500`}
                        >
                            {isEvaluating ? (
                                <div className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                            ) : (
                                <Sparkles className="h-4 w-4" />
                            )}
                            {isEvaluating ? 'Evaluating your answers with AI...' : 'Evaluate My Answers'}
                        </button>
                    )}
                </div>
                {evaluateError && (
                    <p className="text-sm text-red-500 dark:text-red-400 mt-3 font-medium flex items-center justify-center gap-2">
                        <AlertCircle className="h-4 w-4" /> AI evaluation is temporarily unavailable. Try again.
                    </p>
                )}
            </div>

            {/* Q&A summary */}
            <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-600 dark:text-zinc-400 flex items-center gap-2">
                    <BookOpen className="h-4 w-4" /> Session Review
                </h3>
                
                {isEvaluating && (
                    <div className="rounded-xl border border-indigo-200 dark:border-indigo-800 bg-indigo-50/50 dark:bg-indigo-900/10 p-12 flex flex-col items-center justify-center gap-4">
                       <div className="h-10 w-10 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin" />
                       <div className="text-center">
                           <p className="font-medium text-indigo-900 dark:text-indigo-200">Evaluating your answers with AI...</p>
                           <p className="text-sm text-indigo-600/70 dark:text-indigo-400/70 mt-1">This may take a few seconds</p>
                       </div>
                    </div>
                )}
                
                {evaluationData && !isEvaluating && (
                    <>
                        {/* SECTION 1 - Summary Bar */}
                        <div className="flex flex-wrap gap-3 pb-2">
                            <div className={`px-4 py-2 rounded-xl text-sm font-bold border ${evaluationData.avg_score >= 7 ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-800/50' : evaluationData.avg_score >= 4 ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-800/50' : 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800/50'}`}>
                                Avg: {evaluationData.avg_score.toFixed(1)}/10
                            </div>
                            <div className="px-4 py-2 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-800/50 text-sm font-semibold">
                                Strong: {evaluationData.strong_count}
                            </div>
                            <div className="px-4 py-2 rounded-xl bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-800/50 text-sm font-semibold">
                                Adequate: {evaluationData.adequate_count}
                            </div>
                            <div className="px-4 py-2 rounded-xl bg-red-50 text-red-700 border border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800/50 text-sm font-semibold">
                                Weak: {evaluationData.weak_count}
                            </div>
                            <div className="px-4 py-2 rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-200 dark:bg-indigo-900/20 dark:text-indigo-400 dark:border-indigo-800/50 text-sm font-bold">
                                Overall: {evaluationData.overall_verdict}
                            </div>
                        </div>

                        {/* SECTION 2 - Weak Skills */}
                        {evaluationData.weak_skills && evaluationData.weak_skills.length > 0 && (
                            <div className="rounded-xl border border-red-200 dark:border-red-800/40 bg-red-50/60 dark:bg-red-900/10 p-4">
                                <p className="text-xs font-semibold text-red-700 dark:text-red-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                                    <AlertCircle className="h-3.5 w-3.5" /> Areas Needing Improvement
                                </p>
                                <div className="flex flex-wrap gap-2">
                                    {evaluationData.weak_skills.map((skill, i) => (
                                        <span
                                            key={i}
                                            className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 border border-red-200 dark:border-red-700/50"
                                        >
                                            {skill}
                                        </span>
                                    ))}
                                </div>
                                <p className="text-xs text-red-600/70 dark:text-red-400/70 mt-3">
                                    These topics were identified from your lowest-scored answers. Focus your study on these areas.
                                </p>
                            </div>
                        )}
                        {/* SECTION 2 - Question Cards */}
                        <div className="space-y-4">
                            {evaluationData.questions.map((q, i) => (
                                <QuestionCard key={q.question_id || i} q={q} i={i} />
                            ))}
                        </div>
                    </>
                )}

                {/* Show basic question cards if not evaluated yet */}
                {!evaluationData && !isEvaluating && (
                    <div className="space-y-4">
                        {session.questions.map((q, i) => (
                            <QuestionCard key={q.id || i} q={q} i={i} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// WEB SOCKET INTERVIEW ROOM
// ---------------------------------------------------------------------------
interface WebSocketInterviewRoomProps {
    sessionId: string;
    onCompleted: () => void;
}

function WebSocketInterviewRoom({ sessionId, onCompleted, onGoToLobby }: WebSocketInterviewRoomProps & { onGoToLobby?: () => void }) {
    const {
        socket,
        connected,
        connState,
        retryAttempt,
        elapsedMs,
        wsError,
        retryNow,
        markIntentionalClose,
        sendAnswer,
        questions,
        currentIndex,
        setCurrentIndex,
        secondsLeft,
        setSecondsLeft,
        isEvaluating,
        setIsEvaluating,
        evalResult,
        setEvalResult,
        error,
        currentStreamedText,
    } = useWebSocketInterview(sessionId, onCompleted);

    const activeQuestion = questions[currentIndex];
    const total = questions.length;

    // Local typed answer state
    const [typedAnswer, setTypedAnswer] = useState("");
    const [assistantMode, setAssistantMode] = useState(true);

    // Speech & TTS
    const { supported, listening, interimText, finalText, startListening, stopListening, clearFinal } = useVoice();
    const { speak, cancel } = useTTS();
    
    // Typewriter
    const { displayed, done } = useTypewriter(activeQuestion?.question ?? '', 20);

    // Speak active question
    const spokenIndexRef = useRef<number>(-1);
    useEffect(() => {
        cancel();
        spokenIndexRef.current = -1;
        setSecondsLeft(QUESTION_TIME_SEC);
        setEvalResult(null);
        setIsEvaluating(false);
        setTypedAnswer("");
    }, [currentIndex, cancel, setSecondsLeft, setEvalResult, setIsEvaluating]);

    const handleSkip = () => {
        stopListening();
        clearFinal();
        setTypedAnswer("");
        if (currentIndex >= total - 1) {
            onCompleted();
        } else {
            setCurrentIndex(i => i + 1);
        }
    };

    const handleSubmit = () => {
        if (!activeQuestion) return;
        stopListening();

        // Cancel any stale stuck-eval poll and set tracking refs via sendAnswer
        sendAnswer(
            activeQuestion.question_id || activeQuestion.id,
            typedAnswer.trim()
        );

        clearFinal();
    };

    // Timer
    useEffect(() => {
        if (secondsLeft <= 0) {
            handleSkip();
            return;
        }
        if (isEvaluating) return;
        const timer = setTimeout(() => setSecondsLeft(s => s - 1), 1000);
        return () => clearTimeout(timer);
    }, [secondsLeft, isEvaluating, setSecondsLeft]);

    // Auto-trigger microphone after TTS completes
    useEffect(() => {
        if (done && activeQuestion?.question && spokenIndexRef.current !== currentIndex) {
            spokenIndexRef.current = currentIndex;
            speak(activeQuestion.question, () => {
                if (assistantMode) {
                    console.log("TTS finished. Auto starting microphone...");
                    startListening();
                }
            });
        }
    }, [done, activeQuestion?.question, currentIndex, speak, assistantMode, startListening]);

    // Sync speech transcription to local typed answer buffer
    useEffect(() => {
        if (finalText) {
            setTypedAnswer(finalText);
        }
    }, [finalText]);

    // Auto-submit silence detection
    useEffect(() => {
        if (!assistantMode || !listening || !typedAnswer.trim()) return;

        const silenceTimeout = setTimeout(() => {
            console.log("Auto-submitting due to speech pause...");
            handleSubmit();
        }, 2200); // 2.2 seconds of silence

        return () => clearTimeout(silenceTimeout);
    }, [typedAnswer, listening, assistantMode]);

    if (error) {
        return (
            <div className="min-h-[50vh] flex flex-col items-center justify-center gap-4 text-center">
                <AlertCircle className="h-12 w-12 text-red-500 animate-bounce" />
                <h3 className="text-lg font-bold text-gray-900 dark:text-zinc-100">Interview Setup Error</h3>
                <p className="text-sm text-gray-500 dark:text-zinc-400 max-w-md">{error}</p>
                <button
                    onClick={() => window.location.reload()}
                    className="mt-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-semibold text-xs shadow-md transition-colors"
                >
                    Retry Connection
                </button>
            </div>
        );
    }

    return (
        <div className="min-h-[70vh] flex flex-col">
            {/* Connection state banner — shown for all non-connected, non-closed states */}
            <WsConnectionBanner
                connState={connState}
                retryAttempt={retryAttempt}
                elapsedMs={elapsedMs}
                wsError={wsError}
                retryNow={retryNow}
                onGoToLobby={onGoToLobby}
            />

            {/* Reconnect success toast */}
            <ReconnectToast connState={connState} />

            {/* If not yet connected / loading questions — show stream log while banner is visible */}
            {(!connected || questions.length === 0) && (
                <div className="flex flex-col items-center justify-center min-h-[50vh] gap-6 w-full max-w-3xl mx-auto px-4">
                    {currentStreamedText ? (
                        <div className="w-full rounded-2xl border border-gray-200 dark:border-zinc-700 bg-zinc-950 p-6 shadow-xl font-mono text-[10px] sm:text-xs text-emerald-400 overflow-y-auto max-h-[300px] whitespace-pre-wrap leading-relaxed animate-fade-in text-left">
                            <div className="flex items-center justify-between border-b border-zinc-800 pb-2 mb-3">
                                <span className="text-zinc-500 select-none">STREAM_LOG // QUESTION_GENERATION</span>
                                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                            </div>
                            {currentStreamedText}
                            <span className="inline-block w-1.5 h-4 bg-emerald-400 ml-1 live-caret align-middle" />
                        </div>
                    ) : connState === 'connected' ? (
                        <p className="text-xs text-gray-400 italic">Waiting for stream chunks to arrive...</p>
                    ) : null}
                </div>
            )}

            {/* Interview UI — only shown when connected + questions loaded */}
            {connected && questions.length > 0 && (
            <>
            {/* Top bar */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3 animate-slide-in">
                    <span className="text-xs font-bold text-indigo-500 uppercase tracking-widest flex items-center gap-1.5">
                        <span className="h-2.5 w-2.5 rounded-full bg-red-500 inline-block animate-pulse shrink-0" />
                        Live WebSocket Screen
                    </span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${DIFFICULTY_COLOR[activeQuestion.difficulty] ?? 'text-gray-600 dark:text-zinc-400'} bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700`}>
                        {activeQuestion.difficulty}
                    </span>
                    <span className="text-[10px] text-gray-500 dark:text-zinc-400 bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider">
                        {activeQuestion.topic}
                    </span>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={() => {
                            setAssistantMode(prev => {
                                const newVal = !prev;
                                if (!newVal) {
                                    stopListening();
                                }
                                return newVal;
                            });
                        }}
                        className={`text-xs flex items-center gap-1.5 px-3 py-1 rounded-full font-bold border transition ${
                            assistantMode
                                ? 'bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 shadow-[0_0_8px_rgba(16,185,129,0.15)]'
                                : 'bg-gray-100 dark:bg-zinc-800 text-gray-500 dark:text-zinc-400 border-gray-200 dark:border-zinc-700'
                        }`}
                        title="Toggle hands-free conversational loop (Google Assistant style)"
                    >
                        <span>🤖 Assistant Mode</span>
                        <span className={`h-1.5 w-1.5 rounded-full ${assistantMode ? 'bg-emerald-500 animate-pulse' : 'bg-gray-400'} inline-block`} />
                    </button>
                    <span className="text-sm font-semibold text-gray-700 dark:text-zinc-300 bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 px-3 py-1 rounded-full">
                        Q {currentIndex + 1} / {total}
                    </span>
                </div>
            </div>

            {/* Progress bar */}
            <div className="h-1.5 rounded-full bg-gray-100 dark:bg-zinc-800 mb-8 overflow-hidden">
                <div
                    className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-blue-500 transition-all duration-500"
                    style={{ width: `${((currentIndex) / total) * 100}%` }}
                />
            </div>

            {/* Main card */}
            <div className="flex-1 flex flex-col items-center justify-center gap-8">
                {/* Question */}
                <div className="w-full max-w-3xl rounded-2xl border border-gray-200 dark:border-zinc-700 bg-white/60 dark:bg-zinc-900/60 p-8 shadow-sm">
                    <div className="flex items-start gap-4">
                        <div className="flex-shrink-0 h-9 w-9 rounded-full bg-indigo-50 dark:bg-indigo-950 border border-indigo-200 dark:border-indigo-800 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-sm font-bold">
                            {currentIndex + 1}
                        </div>
                        <div className="flex-1">
                            {currentStreamedText ? (
                                <div className="w-full rounded-xl border border-gray-200 dark:border-zinc-700 bg-zinc-950 p-5 shadow-lg font-mono text-[10px] sm:text-xs text-emerald-400 overflow-y-auto max-h-[250px] whitespace-pre-wrap leading-relaxed animate-fade-in text-left">
                                    <div className="flex items-center justify-between border-b border-zinc-800 pb-2 mb-3 select-none">
                                        <span className="text-zinc-500 font-bold uppercase tracking-wider">🤖 AI Interviewer // Drafting Follow-up Question</span>
                                        <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
                                    </div>
                                    {currentStreamedText}
                                    <span className="inline-block w-1.5 h-4 bg-emerald-400 ml-1 live-caret align-middle" />
                                </div>
                            ) : (
                                <>
                                    {renderQuestionText(displayed, done)}
                                    {done && (
                                        <button
                                            type="button"
                                            onClick={() => speak(activeQuestion.question)}
                                            title="Replay question"
                                            className="mt-3 flex items-center gap-1.5 text-xs text-gray-500 dark:text-zinc-500 hover:text-indigo-400 transition"
                                        >
                                            <Volume2 className="h-3.5 w-3.5" /> Replay question
                                        </button>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                </div>

                {/* Score panel if evaluated */}
                <AnimatePresence>
                    {evalResult && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className={`w-full max-w-2xl p-4 rounded-xl border flex items-center gap-4 bg-white/80 dark:bg-zinc-900/80 shadow-md ${
                                Number(evalResult.technical_score ?? evalResult.ai_score) >= 7 ? 'border-emerald-500/30' : 'border-amber-500/30'
                            }`}
                        >
                            <div className={`h-10 w-10 shrink-0 rounded-full border-2 flex items-center justify-center font-bold text-sm ${
                                Number(evalResult.technical_score ?? evalResult.ai_score) >= 7 ? 'border-emerald-500 text-emerald-500' : 'border-amber-500 text-amber-500'
                            }`}>
                                {evalResult.technical_score ?? evalResult.ai_score}
                            </div>
                            <div className="flex-1">
                                <div className="flex items-center gap-2">
                                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                                        evalResult.verdict === 'Strong' || evalResult.ai_verdict === 'Strong' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400' : 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400'
                                    }`}>
                                        {evalResult.verdict ?? evalResult.ai_verdict ?? 'Adequate'}
                                    </span>
                                    <span className="text-[10px] text-gray-400 dark:text-zinc-500">Live calibration complete</span>
                                </div>
                                <p className="text-xs text-gray-600 dark:text-zinc-300 mt-1 italic">"{evalResult.feedback || evalResult.ai_feedback || 'Well analyzed answer.'}"</p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Timer + Mic */}
                <div className="flex flex-col items-center gap-6">
                    <TimerRing seconds={secondsLeft} total={QUESTION_TIME_SEC} />

                    <MicButton
                        listening={listening}
                        onStart={startListening}
                        onStop={stopListening}
                        supported={supported}
                    />

                    {/* Live caption & Text input panel */}
                    <div className="w-full max-w-2xl rounded-xl border border-gray-200 dark:border-zinc-700 bg-white/50 dark:bg-zinc-900/50 p-4 shadow-inner flex flex-col gap-2 relative">
                        <textarea
                            value={typedAnswer}
                            onChange={(e) => setTypedAnswer(e.target.value)}
                            placeholder={listening ? (interimText || 'Listening... speak your answer') : 'Press Speak or type your answer here...'}
                            disabled={isEvaluating}
                            className="w-full min-h-[5rem] bg-transparent border-none outline-none resize-none text-sm text-gray-800 dark:text-zinc-200 placeholder-indigo-400/70 dark:placeholder-indigo-400/50"
                        />
                        {listening && (
                            <span className="absolute bottom-3 right-4 inline-flex items-center gap-1.5 text-[10px] text-red-500 font-bold uppercase tracking-wider animate-pulse">
                                <span className="h-2 w-2 rounded-full bg-red-500" /> Live Voice Stream
                            </span>
                        )}
                    </div>

                    {/* Action row */}
                    <div className="flex items-center gap-4">
                        <button
                          type="button"
                          onClick={handleSkip}
                          disabled={isEvaluating || currentStreamedText.length > 0}
                          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-gray-500 dark:text-zinc-400 hover:text-gray-700 dark:hover:text-zinc-200 hover:bg-gray-100 dark:hover:bg-zinc-800 text-sm font-medium transition disabled:opacity-30 disabled:hover:bg-transparent"
                        >
                            <SkipForward className="h-4 w-4" /> Skip
                        </button>

                        <button
                          type="button"
                          disabled={!typedAnswer.trim() || isEvaluating || currentStreamedText.length > 0}
                          onClick={handleSubmit}
                          className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition disabled:opacity-40 shadow-lg shadow-indigo-100 dark:shadow-indigo-950/30"
                        >
                            {isEvaluating ? (
                                <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing...</>
                            ) : (
                                <><CheckCircle2 className="h-4 w-4" /> Lock In Answer</>
                            )}
                        </button>

                        {(typedAnswer || finalText) && !isEvaluating && (
                            <button
                                type="button"
                                onClick={() => { clearFinal(); setTypedAnswer(""); if (listening) stopListening(); }}
                                className="p-2 rounded-xl text-gray-500 dark:text-zinc-500 hover:text-red-400 hover:bg-gray-100 dark:hover:bg-zinc-800 transition"
                                title="Clear recording"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        )}
                    </div>
                </div>
            </div>
            </>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
const InterviewPrep: React.FC = () => {
    const qc = useQueryClient();
    const [phase, setPhase] = useState<Phase>('lobby');
    const [jdText, setJdText] = useState('');

    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [currentIndex, setCurrentIndex] = useState(0);
    // Track local answers for results view (in case session query is stale)
    const [localAnswers, setLocalAnswers] = useState<Record<string, string>>({});
    // Evaluation state
    const [evaluationData, setEvaluationData] = useState<EvaluationResult | null>(null);
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const urlSessionId = params.get('session_id');
        const isWs = params.get('websocket') === 'true';
        if (urlSessionId) {
            setActiveSessionId(urlSessionId);
            if (isWs) {
                setPhase('interview');
            } else {
                setPhase('results');
            }
        }
    }, [qc]);

    // Session list
    const { data: sessionsData, isLoading: sessionsLoading } = useQuery({
        queryKey: ['interview-sessions'],
        queryFn: listSessions,
    });

    // Active session
    const { data: activeSession, isLoading: sessionLoading } = useQuery({
        queryKey: ['interview-session', activeSessionId],
        queryFn: () => getSession(activeSessionId!),
        enabled: !!activeSessionId,
    });

    // Merge local answers into session for results view
    const mergedSession = useMemo(() => {
        if (!activeSession) return null;
        return {
            ...activeSession,
            questions: activeSession.questions.map(q => ({
                ...q,
                user_answer: localAnswers[q.id] ?? q.user_answer,
            })),
        };
    }, [activeSession, localAnswers]);

    // Auto-detect existing evaluation
    useEffect(() => {
        if (mergedSession && phase === 'results') {
            const alreadyEvaluated = mergedSession.questions.some(q => q.ai_score !== null && q.ai_score !== undefined);
            if (alreadyEvaluated && !evaluationData) {
                setEvaluationData(formatExistingEvaluation(mergedSession));
            }
        }
    }, [mergedSession, phase, evaluationData]);

    // Create session mutation — JD-based: pass jd_text
    const createMutation = useMutation({
        mutationFn: () => {
            return createSession(jdText);
        },
        onSuccess: (session) => {
            setActiveSessionId(session.id);
            setCurrentIndex(0);
            setLocalAnswers({});
            setEvaluationData(null);
            setPhase('interview');
            qc.invalidateQueries({ queryKey: ['interview-sessions'] });
        },
    });

    // Create topic practice session mutation
    const createTopicMutation = useMutation({
        mutationFn: (skillId: string) => {
            return createPracticeTopicSession(skillId);
        },
        onSuccess: (session) => {
            setActiveSessionId(session.id);
            setCurrentIndex(0);
            setLocalAnswers({});
            setEvaluationData(null);
            setPhase('interview');
            qc.invalidateQueries({ queryKey: ['interview-sessions'] });
        },
    });

    const { data: topicsData = [], isLoading: topicsLoading } = useQuery<TaxonomySearchResponse[]>({
        queryKey: ['practice-topics'],
        queryFn: getPracticeTopics,
    });

    // Create project practice session mutation
    const createProjectMutation = useMutation({
        mutationFn: (projectId: string) => {
            return createProjectSession(projectId);
        },
        onSuccess: (session) => {
            setActiveSessionId(session.id);
            setCurrentIndex(0);
            setLocalAnswers({});
            setEvaluationData(null);
            setPhase('interview');
            qc.invalidateQueries({ queryKey: ['interview-sessions'] });
        },
    });

    const { data: projectsData = [], isLoading: projectsLoading } = useQuery<StudentProject[]>({
        queryKey: ['student-projects'],
        queryFn: getStudentProjects,
    });

    // Delete session mutation
    const [deletingId, setDeletingId] = useState<string | null>(null);
    const deleteMutation = useMutation({
        mutationFn: (id: string) => deleteSession(id),
        onMutate: (id) => setDeletingId(id),
        onSuccess: (_data, id) => {
            qc.invalidateQueries({ queryKey: ['interview-sessions'] });
            // If we just deleted the active session, reset
            if (activeSessionId === id) {
                setActiveSessionId(null);
                setPhase('lobby');
            }
        },
        onSettled: () => setDeletingId(null),
    });

    // Evaluate session mutation
    const evaluateMutation = useMutation({
        mutationFn: () => evaluateSession(activeSessionId!),
        onSuccess: (data) => {
            setEvaluationData(data);
            qc.invalidateQueries({ queryKey: ['interview-session', activeSessionId] });
            qc.invalidateQueries({ queryKey: ['interview-sessions'] });
        },
    });

    const handleAnswered = (qId: string, answer: string, completed: boolean) => {
        // Persist locally so results view is accurate even before refetch
        setLocalAnswers(prev => ({ ...prev, [qId]: answer }));
        qc.invalidateQueries({ queryKey: ['interview-session', activeSessionId] });

        const total = activeSession?.questions.length ?? 0;
        if (completed || currentIndex >= total - 1) {
            // Small delay so user sees the submit success
            setTimeout(() => {
                setPhase('results');
                evaluateMutation.mutate();
            }, 600);
        } else {
            setCurrentIndex(i => i + 1);
        }
    };

    const handleSkip = useCallback(() => {
        const total = activeSession?.questions.length ?? 0;
        if (currentIndex >= total - 1) {
            setPhase('results');
            evaluateMutation.mutate();
        } else {
            setCurrentIndex(i => i + 1);
        }
    }, [activeSession, currentIndex, evaluateMutation]);

    const handleSelectSession = (id: string) => {
        setActiveSessionId(id);
        setCurrentIndex(0);
        setLocalAnswers({});
        setEvaluationData(null);
        setPhase('results');
    };

    const handleNewInterview = () => {
        setActiveSessionId(null);
        setCurrentIndex(0);
        setLocalAnswers({});
        setEvaluationData(null);
        setPhase('lobby');
    };

    return (
        <PageTransition className="w-full text-gray-900 dark:text-zinc-100">
            <div className="max-w-6xl mx-auto px-4 py-8">
                {phase === 'lobby' && (
                    <Lobby
                        jdText={jdText}
                        onJdChange={setJdText}
                        onStart={() => createMutation.mutate()}
                        isStarting={createMutation.isPending || createTopicMutation.isPending || createProjectMutation.isPending}
                        startError={createMutation.isError || createTopicMutation.isError || createProjectMutation.isError}
                        sessions={sessionsData?.sessions ?? []}
                        sessionsLoading={sessionsLoading}
                        onSelectSession={handleSelectSession}
                        onDelete={(id) => deleteMutation.mutate(id)}
                        deletingId={deletingId}
                        activeSessionId={activeSessionId}
                        topics={topicsData}
                        topicsLoading={topicsLoading}
                        onStartTopic={(skillId) => createTopicMutation.mutate(skillId)}
                        projects={projectsData}
                        projectsLoading={projectsLoading}
                        onStartProject={(projectId) => createProjectMutation.mutate(projectId)}
                    />
                )}

                {phase === 'interview' && (
                    <WebSocketInterviewRoom
                        sessionId={activeSessionId!}
                        onCompleted={() => {
                            setPhase('results');
                            qc.invalidateQueries({ queryKey: ['interview-session', activeSessionId] });
                        }}
                        onGoToLobby={() => {
                            setActiveSessionId(null);
                            setPhase('lobby');
                        }}
                    />
                )}

                {phase === 'results' && mergedSession && (
                    <ResultsScreen
                        session={mergedSession}
                        evaluationData={evaluationData}
                        onNewInterview={handleNewInterview}
                        onEvaluate={() => evaluateMutation.mutate()}
                        isEvaluating={evaluateMutation.isPending}
                        evaluateError={evaluateMutation.isError}
                    />
                )}
            </div>
        </PageTransition>
    );
};

export default InterviewPrep;
