import { useQuery } from '@tanstack/react-query';
import { Link, useLocation } from 'react-router-dom';
import {
    Award, Target, Briefcase, ChevronRight, Map,
    Cpu, CheckSquare, Zap, AlertCircle, TrendingUp,
    Bell, Plus, Info, Star
} from 'lucide-react';
import { SkillsService, RoadmapService, JobListingsService } from '../services/api';
import { listSessions } from '../api/interview';
import { ErrorDisplay } from '../components/common/Loading';
import { SkeletonStatCard } from '../components/common/SkeletonStatCard';
import { useAuth } from '../contexts/AuthContext';
import { PageTransition } from '../components/layout/PageTransition';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function CircularProgress({ value, size = 56, stroke = 4, color = '#818cf8' }: {
    value: number; size?: number; stroke?: number; color?: string;
}) {
    const r = (size - stroke * 2) / 2;
    const circ = 2 * Math.PI * r;
    const dash = (value / 100) * circ;
    return (
        <svg width={size} height={size} className="-rotate-90">
            <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={stroke} />
            <circle
                cx={size / 2} cy={size / 2} r={r} fill="none"
                stroke={color} strokeWidth={stroke}
                strokeDasharray={`${dash} ${circ}`}
                strokeLinecap="round"
                style={{ transition: 'stroke-dasharray 1s cubic-bezier(0.4,0,0.2,1)' }}
            />
        </svg>
    );
}

function StatCard({ title, value, subtitle, icon: Icon, accentColor = '#818cf8', badge, progress }: {
    title: string;
    value: string | number;
    subtitle?: string;
    icon: any;
    accentColor?: string;
    badge?: string;
    progress?: number;
}) {
    return (
        <div className="stat-card animate-fade-in-up">
            {/* Icon row */}
            <div className="flex items-start justify-between mb-3">
                <div
                    className="h-9 w-9 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{ background: `${accentColor}18`, border: `1px solid ${accentColor}25` }}
                >
                    <Icon className="h-4 w-4" style={{ color: accentColor }} />
                </div>
                {badge && (
                    <span
                        className="px-2 py-0.5 rounded-full text-xs font-bold"
                        style={{ background: `${accentColor}18`, color: accentColor, border: `1px solid ${accentColor}25` }}
                    >
                        {badge}
                    </span>
                )}
            </div>

            {/* Value */}
            <p
                className="text-2xl font-black tracking-tight mb-0.5 animate-number"
                style={{ color: accentColor, lineHeight: 1.1 }}
            >
                {value}
            </p>
            <p className="text-xs font-semibold mb-1" style={{ color: 'var(--text-primary)', opacity: 0.9 }}>
                {title}
            </p>
            {subtitle && (
                <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                    {subtitle}
                </p>
            )}

            {/* Optional progress bar */}
            {progress !== undefined && (
                <div className="mt-2.5 progress-track">
                    <div
                        className="progress-fill"
                        style={{ width: `${progress}%`, background: `linear-gradient(90deg, ${accentColor}, ${accentColor}cc)` }}
                    />
                </div>
            )}
        </div>
    );
}

function SkillBar({ label, value, color = '#818cf8' }: { label: string; value: number; color?: string }) {
    return (
        <div className="space-y-1.5">
            <div className="flex justify-between items-center">
                <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>
                    {label}
                </span>
                <span className="text-xs font-bold" style={{ color }}>
                    {value}%
                </span>
            </div>
            <div className="progress-track">
                <div
                    className="progress-fill"
                    style={{ width: `${value}%`, background: `linear-gradient(90deg, ${color}, ${color}cc)` }}
                />
            </div>
        </div>
    );
}

// ─── Dashboard Component ───────────────────────────────────────────────────────

const Dashboard = () => {
    const { user } = useAuth();

    const {
        data: careerData,
        isLoading: careerLoading,
        error: careerError,
        refetch: refetchCareer
    } = useQuery({
        queryKey: ['career-recommendations'],
        queryFn: SkillsService.getCareerRecommendations,
        staleTime: 5 * 60 * 1000,
    });

    const {
        data: skills,
        isLoading: skillsLoading,
    } = useQuery({
        queryKey: ['my-skills'],
        queryFn: SkillsService.getMySkills,
        staleTime: 5 * 60 * 1000,
    });

    const {
        data: roadmaps,
        isLoading: roadmapsLoading,
    } = useQuery({
        queryKey: ['roadmaps'],
        queryFn: RoadmapService.listRoadmaps,
        staleTime: 5 * 60 * 1000,
    });

    const {
        data: sessionsData,
        isLoading: sessionsLoading,
        error: sessionsError
    } = useQuery({
        queryKey: ['interview-sessions'],
        queryFn: listSessions,
        staleTime: 5 * 60 * 1000,
    });

    const primaryRec = careerData?.recommendations?.primary;
    const activeRole = primaryRec?.job_role || 'Developer';

    const {
        data: jobListings,
        isLoading: jobsLoading
    } = useQuery({
        queryKey: ['job-listings', activeRole],
        queryFn: () => JobListingsService.getJobListings(activeRole),
        enabled: !!activeRole && !careerLoading,
        staleTime: 5 * 60 * 1000,
    });

    const loading = careerLoading || skillsLoading || roadmapsLoading || sessionsLoading;
    const error = careerError || sessionsError;

    if (loading) {
        return (
            <div className="space-y-5 animate-fade-in">
                {/* Header skeleton */}
                <div>
                    <div className="h-4 w-32 skeleton mb-1.5" />
                    <div className="h-7 w-52 skeleton mb-1" />
                    <div className="h-3 w-36 skeleton" />
                </div>
                {/* Stat cards skeleton */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    {[...Array(4)].map((_, i) => (
                        <div key={i} className="stat-card space-y-2">
                            <div className="h-9 w-9 skeleton rounded-xl" />
                            <div className="h-6 w-16 skeleton" />
                            <div className="h-3 w-24 skeleton" />
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <ErrorDisplay
                message={(error as Error).message || 'Failed to fetch career intelligence data'}
                onRetry={() => refetchCareer()}
            />
        );
    }

    // --- Compute metrics ---
    const primaryMatchScore = primaryRec?.match_score ? Math.round(primaryRec.match_score) : 0;
    const verifiedSkillsCount = skills ? skills.filter((s: any) => Number(s.confidence_score) >= 70).length : 0;
    const completedInterviews = sessionsData?.sessions
        ? sessionsData.sessions.filter((s: any) => s.status === 'completed').length
        : 0;
    const activeRoadmap = roadmaps ? roadmaps.find((r: any) => r.status === 'active') : null;
    const roadmapProgressPct = activeRoadmap && activeRoadmap.total_tasks > 0
        ? Math.round((activeRoadmap.completed_tasks / activeRoadmap.total_tasks) * 100)
        : 0;

    // --- Skill proficiency bars ---
    let avgTechnical = 65;
    let avgProject = 70;
    let avgCommunication = 60;
    let avgInterview = 75;

    if (skills && skills.length > 0) {
        const total = skills.length;
        const strong = skills.filter((s: any) => s.level === 'strong');
        const moderate = skills.filter((s: any) => s.level === 'moderate');
        avgTechnical = Math.round((strong.length / total) * 100);
        avgProject = Math.round(skills.reduce((sum: number, s: any) => sum + s.confidence_score, 0) / total);
        avgInterview = strong.length > 0
            ? Math.round(strong.reduce((sum: number, s: any) => sum + s.confidence_score, 0) / strong.length)
            : 0;
        avgCommunication = moderate.length > 0
            ? Math.round(moderate.reduce((sum: number, s: any) => sum + s.confidence_score, 0) / moderate.length)
            : 0;
    }

    // --- Skill gaps ---
    const allGaps = [
        ...(careerData?.tiers?.excellent || []),
        ...(careerData?.tiers?.good || []),
        ...(careerData?.tiers?.potential || []),
        ...(careerData?.tiers?.low || []),
    ];
    const activeGap = allGaps.find((g: any) => g.job_role === activeRole);
    const missingSkills = activeGap?.missing_skills || [];
    const highPotentialSkills = activeGap?.high_potential_skills || [];
    const weakSkills = activeGap?.weak_skills || [];

    return (
        <PageTransition className="space-y-5">

            {/* ── HEADER ────────────────────────────────────────────────── */}
            <div className="flex items-start justify-between animate-fade-in-up">
                <div>
                    <p className="section-label mb-1">Active Intelligence</p>
                    <h1 className="text-2xl font-black tracking-tight" style={{ color: 'var(--text-primary)' }}>
                        Welcome back, {user?.name?.split(' ')[0] || 'Alex'}
                    </h1>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
                        {user?.branch || 'B.Tech'} · Career Tracker Active
                    </p>
                </div>
                <button
                    className="p-2 rounded-xl transition-colors"
                    style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-primary)', color: 'var(--text-secondary)' }}
                >
                    <Bell className="h-5 w-5" />
                </button>
            </div>

            {/* ── STAT CARDS ────────────────────────────────────────────── */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 stagger">
                <StatCard
                    title="Match Score"
                    value={`${primaryMatchScore}%`}
                    icon={Award}
                    accentColor="#818cf8"
                    badge="+2%"
                    progress={primaryMatchScore}
                />
                <StatCard
                    title="Verified Skills"
                    value={verifiedSkillsCount}
                    icon={Target}
                    accentColor="#3b82f6"
                    subtitle={`${skills?.length || 0} total`}
                />
                <StatCard
                    title="Screenings"
                    value={String(completedInterviews).padStart(2, '0')}
                    icon={Cpu}
                    accentColor="#8b5cf6"
                    subtitle="AI screens done"
                />
                <StatCard
                    title="Roadmap"
                    value={`${roadmapProgressPct}%`}
                    icon={Map}
                    accentColor="#f59e0b"
                    progress={roadmapProgressPct}
                    subtitle={activeRoadmap ? `${activeRoadmap.completed_tasks}/${activeRoadmap.total_tasks} tasks` : 'No active roadmap'}
                />
            </div>

            {/* ── MAIN GRID ─────────────────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

                {/* LEFT COLUMN (2/3) */}
                <div className="lg:col-span-2 space-y-4">

                    {/* SKILL PROFICIENCY CARD */}
                    <div
                        className="rounded-2xl p-5 animate-fade-in-up"
                        style={{
                            background: 'var(--bg-surface)',
                            border: '1px solid var(--border-primary)',
                        }}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <p className="section-label">Skill Proficiency</p>
                            <button style={{ color: 'var(--text-tertiary)' }}>
                                <Info className="h-4 w-4" />
                            </button>
                        </div>
                        <div className="space-y-4">
                            <SkillBar label="Technical"     value={avgTechnical}     color="#818cf8" />
                            <SkillBar label="Project"       value={avgProject}       color="#3b82f6" />
                            <SkillBar label="Communication" value={avgCommunication} color="#8b5cf6" />
                            <SkillBar label="Interview"     value={avgInterview}     color="#f59e0b" />
                        </div>
                    </div>

                    {/* TARGET INTELLIGENCE CARD */}
                    <div className="target-card animate-fade-in-up">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="section-label mb-1">Target Intelligence</p>
                                <p className="text-xl font-black tracking-tight" style={{ color: 'var(--text-primary)' }}>
                                    {activeRole}
                                </p>
                                <div className="flex items-center gap-2 mt-2">
                                    <span className="tag tag-indigo">
                                        <TrendingUp className="h-3 w-3 mr-1" />
                                        High Market Demand
                                    </span>
                                    {primaryMatchScore >= 70 && (
                                        <span className="tag tag-blue">
                                            <Star className="h-3 w-3 mr-1" />
                                            Strong Fit
                                        </span>
                                    )}
                                </div>
                            </div>
                            <Link
                                to="/roadmap"
                                className="h-10 w-10 rounded-full flex items-center justify-center flex-shrink-0 transition-all hover:scale-110"
                                style={{
                                    background: 'linear-gradient(135deg, #818cf8, #6366f1)',
                                    boxShadow: '0 0 16px rgba(99,102,241,0.4)',
                                    color: '#0a0e1a',
                                }}
                            >
                                <Plus className="h-5 w-5" />
                            </Link>
                        </div>

                        {/* Match score bar */}
                        <div className="mt-4">
                            <div className="flex justify-between text-xs mb-1.5" style={{ color: 'var(--text-tertiary)' }}>
                                <span>Role Match</span>
                                <span style={{ color: 'var(--brand-primary)' }}>{primaryMatchScore}%</span>
                            </div>
                            <div className="progress-track" style={{ height: '6px' }}>
                                <div
                                    className="progress-fill"
                                    style={{ width: `${primaryMatchScore}%` }}
                                />
                            </div>
                        </div>
                    </div>

                    {/* SKILL GAPS CARD */}
                    <div
                        className="rounded-2xl p-5 animate-fade-in-up"
                        style={{
                            background: 'var(--bg-surface)',
                            border: '1px solid var(--border-primary)',
                        }}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <p className="section-label">Skill Gaps · {activeRole}</p>
                            <Link
                                to="/skills"
                                className="text-xs font-semibold flex items-center gap-0.5 transition-colors"
                                style={{ color: 'var(--brand-primary)' }}
                            >
                                View all <ChevronRight className="h-3.5 w-3.5" />
                            </Link>
                        </div>

                        {missingSkills.length === 0 && highPotentialSkills.length === 0 && weakSkills.length === 0 ? (
                            <div
                                className="rounded-xl p-4 text-sm"
                                style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.15)', color: 'var(--brand-primary)' }}
                            >
                                ✓ No major skill gaps identified — you're job-ready for this role!
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {highPotentialSkills.length > 0 && (
                                    <div
                                        className="rounded-xl p-3 space-y-2"
                                        style={{ background: 'rgba(99,102,241,0.07)', border: '1px solid rgba(99,102,241,0.15)' }}
                                    >
                                        <p className="text-xs font-bold flex items-center gap-1.5" style={{ color: '#a78bfa' }}>
                                            <Zap className="h-3.5 w-3.5" /> High Potential ({highPotentialSkills.length})
                                        </p>
                                        <div className="flex flex-wrap gap-1.5">
                                            {highPotentialSkills.slice(0, 5).map((s: any, idx: number) => (
                                                <span key={idx} className="tag tag-purple text-xs">
                                                    {s.skill_name}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {missingSkills.length > 0 && (
                                        <div className="space-y-2">
                                            <p className="text-xs font-bold" style={{ color: '#f87171' }}>
                                                Missing ({missingSkills.length})
                                            </p>
                                            <div className="flex flex-wrap gap-1.5">
                                                {missingSkills.slice(0, 6).map((s: any, idx: number) => (
                                                    <span key={idx} className="tag tag-red text-xs">{s.skill_name}</span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    {weakSkills.length > 0 && (
                                        <div className="space-y-2">
                                            <p className="text-xs font-bold" style={{ color: '#fbbf24' }}>
                                                To Improve ({weakSkills.length})
                                            </p>
                                            <div className="flex flex-wrap gap-1.5">
                                                {weakSkills.slice(0, 6).map((s: any, idx: number) => (
                                                    <span key={idx} className="tag tag-amber text-xs">
                                                        {s.skill_name}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* RIGHT COLUMN (1/3) */}
                <div className="space-y-4">

                    {/* CAREER RECOMMENDATION */}
                    <div
                        className="rounded-2xl p-5 animate-fade-in-up relative overflow-hidden"
                        style={{
                            background: 'linear-gradient(145deg, #0f0f1e 0%, #0b0d1a 100%)',
                            border: '1px solid rgba(99,102,241,0.2)',
                        }}
                    >
                        {/* Glow orb */}
                        <div
                            className="absolute -top-8 -right-8 w-24 h-24 rounded-full pointer-events-none"
                            style={{ background: 'radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)' }}
                        />
                        <div className="flex items-center gap-2 mb-3">
                            <Briefcase className="h-4 w-4" style={{ color: 'var(--brand-primary)' }} />
                            <p className="section-label">Career Rec.</p>
                        </div>

                        {primaryRec ? (
                            <div>
                                <p className="text-xl font-black tracking-tight mb-1" style={{ color: 'var(--text-primary)' }}>
                                    {primaryRec.job_role}
                                </p>
                                <div className="flex items-center gap-2 mb-4">
                                    <CircularProgress value={primaryMatchScore} size={44} stroke={4} color="#818cf8" />
                                    <div>
                                        <p className="text-lg font-black" style={{ color: '#818cf8' }}>{primaryMatchScore}%</p>
                                        <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Fit Score</p>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Link
                                        to="/skills"
                                        className="flex items-center justify-center gap-1.5 w-full py-2.5 rounded-xl text-xs font-bold transition-all hover:opacity-90"
                                        style={{
                                            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                                            color: '#ffffff',
                                            boxShadow: '0 4px 14px rgba(99,102,241,0.35)',
                                        }}
                                    >
                                        Skill Bridge <ChevronRight className="h-3.5 w-3.5" />
                                    </Link>
                                    <Link
                                        to="/roadmap"
                                        className="flex items-center justify-center gap-1.5 w-full py-2.5 rounded-xl text-xs font-bold transition-all"
                                        style={{
                                            background: 'rgba(255,255,255,0.05)',
                                            color: 'var(--text-secondary)',
                                            border: '1px solid var(--border-primary)',
                                        }}
                                    >
                                        <Map className="h-3.5 w-3.5" /> View Roadmap
                                    </Link>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                                    Configure career targets to calculate your personalized match score.
                                </p>
                                <Link
                                    to="/settings"
                                    className="flex items-center justify-center w-full py-2.5 rounded-xl text-xs font-bold"
                                    style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: '#ffffff' }}
                                >
                                    Set Preferences
                                </Link>
                            </div>
                        )}
                    </div>

                    {/* LIVE JOB LISTINGS */}
                    <div
                        className="rounded-2xl p-5 animate-fade-in-up"
                        style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-primary)' }}
                    >
                        <div className="flex items-center justify-between mb-3">
                            <p className="section-label">Live Opportunities</p>
                            {jobListings?.source && (
                                <span className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--text-tertiary)' }}>
                                    {jobListings.source}
                                </span>
                            )}
                        </div>

                        {jobsLoading ? (
                            <div className="flex flex-col items-center justify-center py-6 gap-2">
                                <div
                                    className="w-5 h-5 border-2 border-t-transparent rounded-full animate-spin"
                                    style={{ borderColor: 'var(--brand-primary)', borderTopColor: 'transparent' }}
                                />
                                <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Scanning listings...</p>
                            </div>
                        ) : jobListings?.jobs && jobListings.jobs.length > 0 ? (
                            <div className="space-y-2.5 max-h-[280px] overflow-y-auto pr-1">
                                {jobListings.jobs.slice(0, 4).map((job: any) => (
                                    <div
                                        key={job.job_id}
                                        className="p-3 rounded-xl transition-all"
                                        style={{
                                            background: 'rgba(255,255,255,0.03)',
                                            border: '1px solid var(--border-primary)',
                                        }}
                                    >
                                        <h4 className="text-xs font-bold truncate mb-0.5" style={{ color: 'var(--text-primary)' }}>
                                            {job.job_title}
                                        </h4>
                                        <p className="text-xs truncate mb-2" style={{ color: 'var(--text-tertiary)' }}>
                                            {job.employer_name} · {job.job_city || job.job_country || 'Remote'}
                                        </p>
                                        <div className="flex items-center justify-between">
                                            <span className="tag tag-indigo" style={{ fontSize: '0.625rem' }}>Active</span>
                                            <a
                                                href={job.job_apply_link}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-xs font-bold flex items-center gap-0.5 transition-colors"
                                                style={{ color: 'var(--brand-primary)' }}
                                            >
                                                Apply <ChevronRight className="h-3 w-3" />
                                            </a>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="flex flex-col items-center py-6 gap-2">
                                <AlertCircle className="h-6 w-6" style={{ color: 'var(--text-muted)' }} />
                                <p className="text-xs text-center" style={{ color: 'var(--text-tertiary)' }}>
                                    No active job matches found right now.
                                </p>
                            </div>
                        )}
                    </div>

                    {/* QUICK ACTIONS */}
                    <div
                        className="rounded-2xl p-4 animate-fade-in-up"
                        style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-primary)' }}
                    >
                        <p className="section-label mb-3">Quick Actions</p>
                        <div className="grid grid-cols-2 gap-2">
                            {[
                                { label: 'Interview Prep', href: '/interview', icon: Cpu, color: '#8b5cf6' },
                                { label: 'Skill Audit',    href: '/skills',    icon: Target, color: '#3b82f6' },
                                { label: 'Roadmap',        href: '/roadmap',   icon: Map,    color: '#818cf8' },
                                { label: 'Settings',       href: '/settings',  icon: CheckSquare, color: '#f59e0b' },
                            ].map((action) => (
                                <Link
                                    key={action.href}
                                    to={action.href}
                                    className="flex flex-col items-center gap-1.5 p-3 rounded-xl transition-all hover:scale-105"
                                    style={{
                                        background: `${action.color}10`,
                                        border: `1px solid ${action.color}20`,
                                        textDecoration: 'none',
                                    }}
                                >
                                    <action.icon className="h-5 w-5" style={{ color: action.color }} />
                                    <span className="text-xs font-semibold text-center leading-tight" style={{ color: 'var(--text-secondary)' }}>
                                        {action.label}
                                    </span>
                                </Link>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </PageTransition>
    );
};

export default Dashboard;
