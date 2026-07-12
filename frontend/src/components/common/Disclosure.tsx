import React, { useState } from 'react';
import { HelpCircle, AlertTriangle, Info } from 'lucide-react';

interface DisclosureProps {
  topic: 'github_verification' | 'career_match' | 'limitations';
  className?: string;
}

export const Disclosure: React.FC<DisclosureProps> = ({ topic, className = '' }) => {
  const [expanded, setExpanded] = useState(false);

  if (topic === 'github_verification') {
    return (
      <div className={`relative inline-block group ${className}`}>
        <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400 cursor-help">
          ✓ Verified (Heuristic Pre-Filter)
        </span>
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-56 hidden group-hover:block z-30 bg-zinc-950 text-[10px] text-zinc-300 p-2.5 rounded-lg border border-zinc-800 shadow-xl pointer-events-none font-normal leading-normal">
          <strong>GitHub Heuristic Pre-Filter:</strong> Checks structural signals (tests, CI config, README depth, and commit history). This is a heuristic check and does not verify logical code correctness.
        </div>
      </div>
    );
  }

  if (topic === 'career_match') {
    return (
      <div className={className}>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-[10px] font-semibold text-indigo-500 hover:text-indigo-600 dark:text-indigo-400/80 dark:hover:text-indigo-300 transition-colors underline focus:outline-none flex items-center gap-1"
        >
          <HelpCircle className="w-3.5 h-3.5" />
          {expanded ? 'Hide calculation details' : 'How is this calculated?'}
        </button>
        {expanded && (
          <div className="mt-2 text-[11px] leading-relaxed text-gray-600 dark:text-zinc-400 bg-white/50 dark:bg-zinc-900/40 p-3 rounded-xl border border-gray-100 dark:border-zinc-800">
            <p className="font-semibold mb-1">Career Match Score Logic:</p>
            <ul className="list-disc pl-4 space-y-1">
              <li><strong>Weighted Importance:</strong> Must-Have (3), Preferred (2), Nice-to-Have (1).</li>
              <li><strong>Contribution Credit:</strong> Strong verified baseline (100%), High Potential concept (40%), Weak/Missing (0%).</li>
              <li><strong>Match Tier Thresholds:</strong> Excellent (≥60%), Good (≥35%), Potential (≥20%), Low (&lt;20%).</li>
            </ul>
          </div>
        )}
      </div>
    );
  }

  if (topic === 'limitations') {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex gap-3 items-start p-3 bg-amber-500/10 text-amber-500 rounded-xl border border-amber-500/20 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold mb-1 text-amber-700 dark:text-amber-400">GitHub Heuristic Scoring</p>
            <p className="opacity-90 leading-relaxed text-amber-600 dark:text-amber-300">
              Scoring is based on structural indicators (presence of test suites, CI configurations, README depth, commit patterns) and does not guarantee code correctness or design quality.
            </p>
          </div>
        </div>
        <div className="flex gap-3 items-start p-3 bg-indigo-500/10 text-indigo-500 rounded-xl border border-indigo-500/20 text-xs">
          <Info className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold mb-1 text-indigo-700 dark:text-indigo-400">AI Interview Calibration</p>
            <p className="opacity-90 leading-relaxed text-indigo-600 dark:text-indigo-300">
              Interview performance metrics represent evaluation of the specific transcript and questions in that session. Results depend on response framing and do not form a generalized competence metric.
            </p>
          </div>
        </div>
        <div className="flex gap-3 items-start p-3 bg-zinc-500/10 text-zinc-500 rounded-xl border border-zinc-500/20 text-xs">
          <Info className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold mb-1 text-gray-700 dark:text-zinc-300">Job Requirements & Market Data</p>
            <p className="opacity-90 leading-relaxed text-gray-600 dark:text-zinc-400">
              Industry requirements are reviewed periodically by faculty and experts. They reflect general expectations and are not real-time feeds from external job boards.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return null;
};
