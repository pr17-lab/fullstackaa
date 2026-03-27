import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, TrendingUp, AlertTriangle, ChevronDown, ChevronUp,
  ArrowUpDown, ArrowDownUp, Briefcase, Target, BookOpen, ArrowRight,
  Plus, Search, X, GraduationCap, Check
} from 'lucide-react';
import { SkillsService, JobListingsService } from '../services/api';
import { ErrorDisplay } from '../components/common/Loading';
import type { StudentSkill, SkillGap, TaxonomySearchResponse } from '../types/career';
import { PageTransition } from '../components/layout/PageTransition';
import { useAuth } from '../contexts/AuthContext';

// ─── Animation Variants ────────────────────────────────────────────────────────

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' as const } },
} as const;

// ─── Helpers ───────────────────────────────────────────────────────────────────

function levelColor(level: string) {
  if (level === 'strong') return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400';
  if (level === 'moderate') return 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400';
  return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400';
}

function matchLabelColor(label: string) {
  if (label === 'Excellent') return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400';
  if (label === 'Good') return 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400';
  if (label === 'Potential') return 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400';
  return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400';
}

function progressBarColor(score: number) {
  if (score >= 45) return 'bg-emerald-500';
  if (score >= 25) return 'bg-amber-500';
  return 'bg-red-500';
}

// ─── SVG Circular Progress ────────────────────────────────────────────────────

function CircularProgress({ score, size = 120 }: { score: number; size?: number }) {
  const r = (size - 16) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 60 ? '#10b981' : score >= 35 ? '#3b82f6' : score >= 20 ? '#f59e0b' : '#ef4444';

  return (
    <svg width={size} height={size} className="rotate-[-90deg]">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="currentColor"
        strokeWidth={8} className="text-gray-200 dark:text-zinc-700" />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color}
        strokeWidth={8} strokeDasharray={circ} strokeDashoffset={offset}
        strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1s ease' }} />
    </svg>
  );
}

// ─── Skeleton Components ──────────────────────────────────────────────────────

function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 p-5 animate-pulse ${className}`}>
      <div className="h-4 w-24 bg-gray-200 dark:bg-zinc-700 rounded mb-3" />
      <div className="h-8 w-16 bg-gray-200 dark:bg-zinc-700 rounded mb-2" />
      <div className="h-3 w-32 bg-gray-200 dark:bg-zinc-700 rounded" />
    </div>
  );
}

function SkeletonGapCard() {
  return (
    <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 p-5 animate-pulse">
      <div className="flex justify-between mb-3">
        <div className="h-5 w-36 bg-gray-200 dark:bg-zinc-700 rounded" />
        <div className="h-5 w-16 bg-gray-200 dark:bg-zinc-700 rounded" />
      </div>
      <div className="h-2 w-full bg-gray-200 dark:bg-zinc-700 rounded-full" />
    </div>
  );
}

// ─── Section 1: Summary Bar ────────────────────────────────────────────────────

function SkillsSummarySection() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['skills-summary'],
    queryFn: SkillsService.getSkillsSummary,
    enabled: isAuthenticated && !authLoading,
    retry: 1,
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <SkeletonCard /><SkeletonCard /><SkeletonCard />
        </div>
      </div>
    );
  }
  if (isError || !data) {
    return <ErrorDisplay message="Failed to load skills summary" onRetry={() => refetch()} />;
  }

  const topStrong = data.top_skills.filter(s => s.level === 'strong').slice(0, 3);

  const statCards = [
    { label: 'Strong Skills', count: data.strong_count, icon: Zap, color: 'emerald' },
    { label: 'Moderate Skills', count: data.moderate_count, icon: TrendingUp, color: 'amber' },
    { label: 'Weak Skills', count: data.weak_count, icon: AlertTriangle, color: 'red' },
  ];

  const colorMap: Record<string, string> = {
    emerald: 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-100 dark:border-emerald-800/50 text-emerald-700 dark:text-emerald-400',
    amber: 'bg-amber-50 dark:bg-amber-900/20 border-amber-100 dark:border-amber-800/50 text-amber-700 dark:text-amber-400',
    red: 'bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-800/50 text-red-700 dark:text-red-400',
  };
  const iconBgMap: Record<string, string> = {
    emerald: 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400',
    amber: 'bg-amber-100 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400',
    red: 'bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400',
  };

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {statCards.map(({ label, count, icon: Icon, color }) => (
          <motion.div key={label} variants={cardVariants}
            className={`rounded-2xl border p-5 flex items-center gap-4 ${colorMap[color]}`}>
            <div className={`p-3 rounded-xl ${iconBgMap[color]}`}>
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <p className="text-2xl font-bold">{count}</p>
              <p className="text-sm font-medium opacity-80">{label}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {topStrong.length > 0 && (
        <motion.div variants={cardVariants} className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-gray-500 dark:text-zinc-400 mr-1">Top skills:</span>
          {topStrong.map(s => (
            <span key={s.skill_name}
              className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400">
              ⚡ {s.skill_name}
            </span>
          ))}
        </motion.div>
      )}
    </motion.div>
  );
}

// ─── Section 2: Career Recommendation Banner ──────────────────────────────────

function CareerRecommendationSection() {
  // Derive recommendation from gaps data — use top gap as primary
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { data: gaps, isLoading, isError } = useQuery({
    queryKey: ['skill-gaps'],
    queryFn: SkillsService.getSkillGaps,
    enabled: isAuthenticated && !authLoading,
    retry: 1,
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 p-6 animate-pulse">
        <div className="flex gap-6 items-center">
          <div className="w-28 h-28 rounded-full bg-gray-200 dark:bg-zinc-700" />
          <div className="flex-1 space-y-3">
            <div className="h-6 w-48 bg-gray-200 dark:bg-zinc-700 rounded" />
            <div className="h-4 w-32 bg-gray-200 dark:bg-zinc-700 rounded" />
            <div className="flex gap-2">
              <div className="h-6 w-24 bg-gray-200 dark:bg-zinc-700 rounded-full" />
              <div className="h-6 w-24 bg-gray-200 dark:bg-zinc-700 rounded-full" />
            </div>
          </div>
        </div>
      </div>
    );
  }
  if (isError || !gaps || gaps.length === 0) {
    return (
      <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 p-6 text-center text-gray-500 dark:text-zinc-400">
        No career gap data available yet.
      </div>
    );
  }

  const primary = gaps[0];
  const alternatives = gaps.slice(1, 3);

  return (
    <motion.div variants={cardVariants} initial="hidden" animate="visible">
      <div className="bg-gradient-to-br from-indigo-50 to-blue-50 dark:from-indigo-950/40 dark:to-blue-950/40 rounded-2xl border border-indigo-100 dark:border-indigo-900/50 p-6">
        <div className="flex flex-col sm:flex-row items-center gap-6">
          {/* Circular Progress */}
          <div className="relative flex-shrink-0">
            <CircularProgress score={primary.match_score} size={120} />
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-gray-900 dark:text-zinc-100">
                {Math.round(primary.match_score)}%
              </span>
              <span className="text-xs text-gray-500 dark:text-zinc-400">match</span>
            </div>
          </div>

          {/* Details */}
          <div className="flex-1 text-center sm:text-left">
            <p className="text-xs font-semibold text-indigo-500 dark:text-indigo-400 uppercase tracking-wider mb-1">
              Best Career Match
            </p>
            <h2 className="text-xl font-bold text-gray-900 dark:text-zinc-100 mb-2">
              {primary.job_role}
            </h2>
            <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold mb-3 ${matchLabelColor(primary.match_label)}`}>
              {primary.match_label}
            </span>

            {alternatives.length > 0 && (
              <div className="flex flex-wrap gap-2 justify-center sm:justify-start">
                <span className="text-xs text-gray-500 dark:text-zinc-400 self-center">Also consider:</span>
                {alternatives.map(alt => (
                  <span key={alt.job_role}
                    className="px-3 py-1 rounded-full text-xs font-medium bg-white/70 dark:bg-zinc-800/70 text-gray-700 dark:text-zinc-300 border border-gray-200 dark:border-zinc-700">
                    {alt.job_role} · {Math.round(alt.match_score)}%
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Right stat */}
          <div className="hidden lg:flex flex-col items-center gap-1 text-center">
            <Briefcase className="w-6 h-6 text-indigo-400" />
            <span className="text-xs text-gray-500 dark:text-zinc-400">
              {gaps.length} roles analysed
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// ─── Section 3: Skill Gaps Grid ───────────────────────────────────────────────

function formatRelativeTime(dateString: string) {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 3600 * 24));
  if (diffInDays === 0) return 'Today';
  if (diffInDays === 1) return 'Yesterday';
  if (diffInDays < 30) return `${diffInDays} days ago`;
  const diffInMonths = Math.floor(diffInDays / 30);
  return `${diffInMonths} month${diffInMonths > 1 ? 's' : ''} ago`;
}

function GapCard({ gap }: { gap: SkillGap }) {
  const [open, setOpen] = useState(false);

  const { data: jobsResponse, isLoading: jobsLoading, isError: jobsError } = useQuery({
    queryKey: ['job-listings', gap.job_role],
    queryFn: () => JobListingsService.getJobListings(gap.job_role),
    enabled: open,
    staleTime: 0,        // always fetch fresh when card opens
    gcTime: 1000 * 60 * 30, // keep in garbage-collection cache for 30 min
  });

  return (
    <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full p-5 flex items-center justify-between text-left hover:bg-gray-50 dark:hover:bg-zinc-800/60 transition-colors"
      >
        <div className="flex-1 min-w-0 mr-3">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-semibold text-gray-900 dark:text-zinc-100 text-sm truncate">
              {gap.job_role}
            </span>
            <span className={`flex-shrink-0 px-2 py-0.5 rounded-full text-xs font-semibold ${matchLabelColor(gap.match_label)}`}>
              {gap.match_label}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex-1 h-2 rounded-full bg-gray-100 dark:bg-zinc-700">
              <div
                className={`h-2 rounded-full transition-all duration-700 ${progressBarColor(gap.match_score)}`}
                style={{ width: `${Math.min(gap.match_score, 100)}%` }}
              />
            </div>
            <span className="text-xs font-semibold text-gray-600 dark:text-zinc-400 flex-shrink-0">
              {Math.round(gap.match_score)}%
            </span>
          </div>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-gray-400 flex-shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' as const }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 border-t border-gray-100 dark:border-zinc-800 pt-4 space-y-3">
              {gap.missing_skills.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-red-500 dark:text-red-400 uppercase tracking-wider mb-2">
                    Missing Skills ({gap.missing_skills.length})
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {gap.missing_skills.slice(0, 8).map((m, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-md text-xs bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 border border-red-100 dark:border-red-800/50">
                        {m.importance === 'must_have' ? '🔴' : m.importance === 'preferred' ? '🟡' : '⚪'} {m.skill_name ?? m.skill_id ?? `Skill ${i + 1}`}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {gap.weak_skills.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-amber-500 dark:text-amber-400 uppercase tracking-wider mb-2">
                    Skills to Improve ({gap.weak_skills.length})
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {gap.weak_skills.slice(0, 6).map((w, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-md text-xs bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border border-amber-100 dark:border-amber-800/50">
                        {Math.round(w.score)}% / {w.required}% required
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {gap.strong_skills.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-emerald-500 dark:text-emerald-400 uppercase tracking-wider mb-2">
                    Already Strong ({gap.strong_skills.length})
                  </p>
                  <span className="text-xs text-gray-500 dark:text-zinc-400">
                    {gap.strong_skills.length} skill{gap.strong_skills.length !== 1 ? 's' : ''} meet the role requirements ✓
                  </span>
                </div>
              )}

              {/* Live Job Listings Section */}
              <div className="pt-4 mt-2 border-t border-gray-100 dark:border-zinc-800">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-semibold text-indigo-500 dark:text-indigo-400 uppercase tracking-wider">
                    Available Jobs
                  </p>
                  {jobsResponse && jobsResponse.source === 'jsearch' && (
                    <span className="text-[10px] text-gray-400 dark:text-zinc-500 uppercase font-medium tracking-wide">
                      Powered by JSearch
                    </span>
                  )}
                  {jobsResponse && jobsResponse.source === 'fallback' && (
                    <span className="text-[10px] text-gray-400 dark:text-zinc-500 uppercase font-medium tracking-wide">
                      Search manually
                    </span>
                  )}
                </div>

                {jobsLoading ? (
                  <div className="flex items-center justify-center gap-2 p-4 text-xs text-indigo-500">
                    <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                    Fetching live jobs...
                  </div>
                ) : jobsError ? (
                  <div className="text-xs text-red-500 dark:text-red-400 text-center py-3">
                    Failed to load live jobs. Try collapsing and expanding the card again.
                  </div>
                ) : jobsResponse?.source === 'fallback' ? (
                  <div className="space-y-3">
                    <p className="text-xs text-gray-500 dark:text-zinc-400">
                      Live listings unavailable — search on these platforms:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {jobsResponse.jobs.map(job => (
                        <a
                          key={job.job_id}
                          href={job.job_apply_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-4 py-2 rounded-lg text-xs font-semibold bg-gray-50 dark:bg-zinc-800 text-gray-700 dark:text-zinc-300 hover:bg-gray-100 dark:hover:bg-zinc-700 border border-gray-200 dark:border-zinc-700 transition"
                        >
                          🔗 {job.employer_name}
                        </a>
                      ))}
                    </div>
                  </div>
                ) : (jobsResponse?.jobs?.length ?? 0) > 0 ? (
                  <div className="space-y-3">
                    {jobsResponse!.jobs.slice(0, 5).map(job => (
                      <div key={job.job_id} className="p-3.5 bg-gray-50 dark:bg-zinc-800/50 rounded-xl border border-gray-100 dark:border-zinc-800 flex items-start justify-between gap-4">
                        <div className="min-w-0">
                          <h4 className="text-sm font-semibold text-gray-900 dark:text-zinc-100 truncate">
                            {job.job_title}
                          </h4>
                          <div className="flex flex-wrap items-center gap-2 mt-1.5 text-xs text-gray-500 dark:text-zinc-400">
                            <span className="font-medium text-gray-700 dark:text-zinc-300">
                              {job.employer_name}
                            </span>
                            {(job.job_city || job.job_country) && (
                              <>
                                <span>·</span>
                                <span>{[job.job_city, job.job_country].filter(Boolean).join(', ')}</span>
                              </>
                            )}
                            {job.job_posted_at_datetime_utc && (
                              <>
                                <span>·</span>
                                <span>{formatRelativeTime(job.job_posted_at_datetime_utc)}</span>
                              </>
                            )}
                          </div>
                        </div>
                        <a
                          href={job.job_apply_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-500/20 transition-colors whitespace-nowrap"
                        >
                          Apply →
                        </a>
                      </div>
                    ))}
                  </div>
                ) : jobsResponse ? (
                  <div className="text-xs text-gray-500 dark:text-zinc-400 text-center py-4">
                    No matching jobs found right now.
                  </div>
                ) : null}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function SkillGapsSection() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { data: gaps, isLoading, isError, refetch } = useQuery({
    queryKey: ['skill-gaps'],
    queryFn: SkillsService.getSkillGaps,
    enabled: isAuthenticated && !authLoading,
    retry: 1,
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[...Array(4)].map((_, i) => <SkeletonGapCard key={i} />)}
      </div>
    );
  }
  if (isError) return <ErrorDisplay message="Failed to load skill gaps" onRetry={() => refetch()} />;
  if (!gaps || gaps.length === 0) {
    return (
      <div className="text-center py-10 text-gray-500 dark:text-zinc-400 text-sm">
        No skill gap data available yet.
      </div>
    );
  }

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible"
      className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {gaps.map(gap => (
        <motion.div key={gap.job_role} variants={cardVariants}>
          <GapCard gap={gap} />
        </motion.div>
      ))}
    </motion.div>
  );
}

// ─── Section 4: Full Skills List ──────────────────────────────────────────────

function SkillsListSection() {
  const qc = useQueryClient();
  const [sortAlpha, setSortAlpha] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSkill, setSelectedSkill] = useState<TaxonomySearchResponse | null>(null);
  const [confidence, setConfidence] = useState(50);
  const [showDropdown, setShowDropdown] = useState(false);

  // Debounced search for taxonomy
  const [debouncedQuery, setDebouncedQuery] = useState('');
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(searchQuery), 300);
    return () => clearTimeout(t);
  }, [searchQuery]);

  const { data: searchResults, isFetching: isSearching } = useQuery({
    queryKey: ['taxonomy-search', debouncedQuery],
    queryFn: () => SkillsService.searchTaxonomy(debouncedQuery),
    enabled: debouncedQuery.length > 0,
  });

  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { data: skills, isLoading, isError, refetch } = useQuery({
    queryKey: ['my-skills'],
    queryFn: SkillsService.getMySkills,
    enabled: isAuthenticated && !authLoading,
    retry: 1,
    staleTime: 5 * 60 * 1000,
  });

  const addMutation = useMutation({
    mutationFn: () => SkillsService.addManualSkill(selectedSkill?.skill_name || searchQuery, confidence),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-skills'] });
      qc.invalidateQueries({ queryKey: ['skills-summary'] });
      qc.invalidateQueries({ queryKey: ['skill-gaps'] });
      setIsAdding(false);
      setSearchQuery('');
      setSelectedSkill(null);
      setConfidence(50);
    }
  });

  const removeMutation = useMutation({
    mutationFn: (id: string) => SkillsService.removeManualSkill(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-skills'] });
      qc.invalidateQueries({ queryKey: ['skills-summary'] });
      qc.invalidateQueries({ queryKey: ['skill-gaps'] });
    }
  });

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 overflow-hidden animate-pulse">
        <div className="p-5 border-b border-gray-100 dark:border-zinc-800">
          <div className="h-5 w-32 bg-gray-200 dark:bg-zinc-700 rounded" />
        </div>
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center gap-4 px-5 py-4 border-b border-gray-100 dark:border-zinc-800 last:border-0">
            <div className="h-4 w-32 bg-gray-200 dark:bg-zinc-700 rounded" />
            <div className="h-4 w-20 bg-gray-200 dark:bg-zinc-700 rounded" />
            <div className="flex-1 h-2 bg-gray-200 dark:bg-zinc-700 rounded-full" />
            <div className="h-5 w-16 bg-gray-200 dark:bg-zinc-700 rounded-full" />
          </div>
        ))}
      </div>
    );
  }
  if (isError) return <ErrorDisplay message="Failed to load your skills" onRetry={() => refetch()} />;
  if (!skills || skills.length === 0) {
    return (
      <div className="text-center py-10 text-gray-500 dark:text-zinc-400 text-sm">
        No skill data found. Skills are computed from your academic records.
      </div>
    );
  }

  const sorted = [...skills].sort((a, b) =>
    sortAlpha
      ? a.skill_name.localeCompare(b.skill_name)
      : b.confidence_score - a.confidence_score
  );

  return (
    <motion.div variants={cardVariants} initial="hidden" animate="visible"
      className="bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-zinc-800">
        <p className="font-semibold text-gray-900 dark:text-zinc-100 text-sm">
          All Skills <span className="text-gray-400 dark:text-zinc-500 font-normal">({skills.length})</span>
        </p>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSortAlpha(a => !a)}
            className="flex items-center gap-1.5 text-xs font-medium text-gray-500 dark:text-zinc-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
          >
            {sortAlpha ? <ArrowUpDown className="w-3.5 h-3.5" /> : <ArrowDownUp className="w-3.5 h-3.5" />}
            {sortAlpha ? 'Sort by Score' : 'Sort A–Z'}
          </button>
          {!isAdding && (
            <button
              onClick={() => setIsAdding(true)}
              className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-500/20 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" /> Add a Skill
            </button>
          )}
        </div>
      </div>

      {/* Add Skill Inline Form */}
      <AnimatePresence>
        {isAdding && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-b border-gray-100 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20"
          >
            <div className="p-5 flex flex-col md:flex-row gap-6">
              <div className="flex-1 relative">
                <label className="block text-xs font-semibold text-gray-700 dark:text-zinc-300 mb-1.5">Search Skill</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="e.g. React, Python, Data Analysis..."
                    className="w-full pl-9 pr-4 py-2 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl text-sm outline-none focus:ring-2 focus:ring-indigo-500/50"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setSelectedSkill(null);
                      setShowDropdown(true);
                    }}
                    onFocus={() => setShowDropdown(true)}
                  />
                  {addMutation.isError && (
                     <p className="mt-1 text-xs text-red-500 flex items-center gap-1"><AlertTriangle className="w-3 h-3"/> Skill not found or custom entry failed.</p>
                  )}
                </div>
                {showDropdown && searchResults && searchResults.length > 0 && searchQuery.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl shadow-lg max-h-48 overflow-y-auto">
                    {searchResults.map(res => (
                      <button
                        key={res.id}
                        className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-zinc-800 flex items-center justify-between transition-colors"
                        onClick={() => {
                          setSelectedSkill(res);
                          setSearchQuery(res.skill_name);
                          setShowDropdown(false);
                        }}
                      >
                        <span className="font-medium text-gray-900 dark:text-zinc-100">{res.skill_name}</span>
                        <span className="text-[10px] text-gray-500 uppercase tracking-wider">{res.category}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex-1">
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-gray-700 dark:text-zinc-300">Confidence Score</label>
                  <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400">
                    {confidence} – {confidence < 45 ? 'Learning' : confidence < 70 ? 'Familiar' : 'Proficient'}
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={confidence}
                  onChange={(e) => setConfidence(Number(e.target.value))}
                  className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gray-200 dark:bg-zinc-700 outline-none"
                  style={{ accentColor: '#4f46e5' }}
                />
                <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                  <span>0</span>
                  <span>50</span>
                  <span>100</span>
                </div>
              </div>

              <div className="flex items-end gap-2 pb-5 md:pb-0" style={{ paddingBottom: '0.6rem' }}>
                <button
                  type="button"
                  onClick={() => setIsAdding(false)}
                  className="px-4 py-2.5 rounded-xl text-gray-500 dark:text-zinc-400 hover:bg-gray-100 dark:hover:bg-zinc-800 text-sm font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={!searchQuery.trim() || addMutation.isPending}
                  onClick={() => addMutation.mutate()}
                  className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition disabled:opacity-50 flex items-center gap-2"
                >
                  {addMutation.isPending ? 'Adding...' : 'Add Skill'}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 dark:bg-zinc-800/50 text-xs text-gray-500 dark:text-zinc-400 uppercase tracking-wider">
              <th className="text-left px-5 py-3 font-medium">Skill</th>
              <th className="text-left px-4 py-3 font-medium hidden sm:table-cell">Category</th>
              <th className="text-left px-4 py-3 font-medium">Score</th>
              <th className="text-left px-4 py-3 font-medium">Level</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((skill: StudentSkill, i) => (
              <motion.tr key={skill.skill_name}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.03 }}
                className="border-t border-gray-50 dark:border-zinc-800 hover:bg-gray-50/50 dark:hover:bg-zinc-800/30 transition-colors"
              >
                <td className="px-5 py-3.5 font-medium text-gray-900 dark:text-zinc-100">
                  <div className="flex flex-col gap-1 items-start">
                    <div className="flex items-center gap-2">
                      {skill.skill_name}
                        <GraduationCap className="w-3.5 h-3.5 text-emerald-500" />
                    </div>
                    {skill.source.includes('self_reported') && (
                      <div className="flex items-center gap-1">
                        <span className="text-[10px] italic text-gray-400 dark:text-zinc-500 bg-gray-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded flex items-center gap-1">
                          Self-reported
                          <button
                            onClick={() => removeMutation.mutate(skill.skill_id)}
                            className="hover:text-red-500 transition-colors"
                            title="Remove manual entry"
                            disabled={removeMutation.isPending}
                          >
                            <X className="w-2.5 h-2.5" />
                          </button>
                        </span>
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3.5 text-gray-500 dark:text-zinc-400 hidden sm:table-cell">
                  {skill.category}
                </td>
                <td className="px-4 py-3.5">
                  <div className="flex items-center gap-2 min-w-[80px]">
                    <div className="flex-1 h-1.5 rounded-full bg-gray-100 dark:bg-zinc-700">
                      <div
                        className={`h-1.5 rounded-full ${skill.level === 'strong' ? 'bg-emerald-500' : skill.level === 'moderate' ? 'bg-amber-500' : 'bg-red-500'}`}
                        style={{ width: `${Math.min(skill.confidence_score, 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-600 dark:text-zinc-300 w-7 text-right">
                      {Math.round(skill.confidence_score)}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3.5">
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${levelColor(skill.level)}`}>
                    {skill.level}
                  </span>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const SkillsPage = () => {
  return (
    <PageTransition className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-zinc-100 flex items-center gap-3">
          <span className="p-2 bg-indigo-100 dark:bg-indigo-900/40 rounded-xl">
            <Target className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
          </span>
          Career Skills
        </h1>
        <p className="text-gray-500 dark:text-zinc-400 mt-1 ml-14">
          Your computed skill profile and career match analysis
        </p>
      </div>

      {/* Section 1 — Summary Stat Cards */}
      <section>
        <SkillsSummarySection />
      </section>

      {/* Section 2 — Career Recommendation */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Briefcase className="w-4 h-4 text-indigo-500" />
          <h2 className="text-sm font-semibold text-gray-700 dark:text-zinc-300 uppercase tracking-wider">
            Best Career Match
          </h2>
        </div>
        <CareerRecommendationSection />
      </section>

      {/* Section 3 — Skill Gaps */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-4 h-4 text-indigo-500" />
          <h2 className="text-sm font-semibold text-gray-700 dark:text-zinc-300 uppercase tracking-wider">
            Career Gap Analysis
          </h2>
          <span className="ml-auto flex items-center gap-1 text-xs text-indigo-500 dark:text-indigo-400 font-medium">
            Click a card to expand <ArrowRight className="w-3 h-3" />
          </span>
        </div>
        <SkillGapsSection />
      </section>

      {/* Section 4 — Skills Table */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <BookOpen className="w-4 h-4 text-indigo-500" />
          <h2 className="text-sm font-semibold text-gray-700 dark:text-zinc-300 uppercase tracking-wider">
            Full Skill Profile
          </h2>
        </div>
        <SkillsListSection />
      </section>
    </PageTransition>
  );
};

export default SkillsPage;
