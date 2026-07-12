import React, { useState } from 'react';
import {
  Upload, FileText, CheckCircle2, ChevronRight,
  Plus, X, Loader2, Sparkles, AlertCircle, ArrowRight
} from 'lucide-react';
import api from '../../api/client';
import { parseResumePdf } from '../../api/interview';
import { PreferencesService, RoadmapService } from '../../services/api';
import { useQuery } from '@tanstack/react-query';
import { SkillsService } from '../../services/api';

interface OnboardingWizardProps {
  preferences: any;
  onComplete: () => void;
}

const STEPS = [
  { id: 'resume', title: 'Resume Scan' },
  { id: 'github', title: 'Verify Projects' },
  { id: 'gaps', title: 'Gap Preview' },
  { id: 'roadmap', title: 'Get Roadmap' }
];

export default function OnboardingWizard({ preferences, onComplete }: OnboardingWizardProps) {
  const [activeStep, setActiveStep] = useState(
    preferences?.onboarding_step === 'resume_uploaded' ? 1 :
    preferences?.onboarding_step === 'github_added' ? 2 :
    preferences?.onboarding_step === 'gap_analysis_shown' ? 3 :
    preferences?.onboarding_step === 'roadmap_generated' ? 3 : 0
  );

  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState('');
  const [error, setError] = useState('');
  
  // Resume upload state
  const [file, setFile] = useState<File | null>(null);

  // GitHub repos state
  const [repos, setRepos] = useState<string[]>(['', '', '']);

  // Fetch gaps for the primary target role
  const primaryRole = preferences?.target_roles?.[0] || 'Software Engineer';
  const { data: careerData, refetch: refetchCareer } = useQuery({
    queryKey: ['career-recommendations'],
    queryFn: SkillsService.getCareerRecommendations,
    enabled: activeStep >= 2
  });

  const activeGap = careerData?.tiers?.excellent?.find((g: any) => g.job_role === primaryRole) ||
                    careerData?.tiers?.good?.find((g: any) => g.job_role === primaryRole) ||
                    careerData?.tiers?.potential?.find((g: any) => g.job_role === primaryRole) ||
                    careerData?.tiers?.low?.find((g: any) => g.job_role === primaryRole);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleUploadResume = async () => {
    if (!file) {
      setError('Please select a PDF resume file.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      setStatusText('Parsing PDF resume...');
      const parseRes = await parseResumePdf(file);
      
      setStatusText('Gemini extracting technical skill tags...');
      await api.post('/skills/extract-resume-skills', {
        resume_text: parseRes.text
      });

      setStatusText('Saving updates...');
      const updatedPrefs = { ...preferences, onboarding_step: 'resume_uploaded' };
      delete updatedPrefs.id;
      delete updatedPrefs.user_id;
      delete updatedPrefs.created_at;
      delete updatedPrefs.updated_at;
      await PreferencesService.updatePreferences(updatedPrefs);

      setStatusText('');
      setLoading(false);
      setActiveStep(1);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to parse resume.');
      setLoading(false);
    }
  };

  const handleGitHubSubmit = async (isSkip = false) => {
    setLoading(true);
    setError('');
    try {
      if (!isSkip) {
        setStatusText('Queuing repository complexity analysis...');
        const validRepos = repos.filter(url => url.trim().toLowerCase().includes('github.com'));
        for (const repoUrl of validRepos) {
          await api.post('/skills/project/verify', { repo_url: repoUrl.trim() });
        }
      }

      setStatusText('Updating progress...');
      const updatedPrefs = { ...preferences, onboarding_step: 'github_added' };
      delete updatedPrefs.id;
      delete updatedPrefs.user_id;
      delete updatedPrefs.created_at;
      delete updatedPrefs.updated_at;
      await PreferencesService.updatePreferences(updatedPrefs);

      // Force career recommend refetch
      await refetchCareer();
      setStatusText('');
      setLoading(false);
      setActiveStep(2);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit repos.');
      setLoading(false);
    }
  };

  const handleShowGapAnalysis = async () => {
    setLoading(true);
    setError('');
    try {
      const updatedPrefs = { ...preferences, onboarding_step: 'gap_analysis_shown' };
      delete updatedPrefs.id;
      delete updatedPrefs.user_id;
      delete updatedPrefs.created_at;
      delete updatedPrefs.updated_at;
      await PreferencesService.updatePreferences(updatedPrefs);
      
      setLoading(false);
      setActiveStep(3);
    } catch (err: any) {
      setError(err.message || 'Failed to advance step.');
      setLoading(false);
    }
  };

  const handleGenerateRoadmap = async () => {
    setLoading(true);
    setError('');
    try {
      setStatusText('Generating personalized roadmap and practice tasks...');
      await RoadmapService.generateRoadmap(primaryRole);

      setStatusText('Finalizing onboarding setup...');
      const updatedPrefs = { ...preferences, onboarding_step: 'complete' };
      delete updatedPrefs.id;
      delete updatedPrefs.user_id;
      delete updatedPrefs.created_at;
      delete updatedPrefs.updated_at;
      await PreferencesService.updatePreferences(updatedPrefs);

      setStatusText('');
      setLoading(false);
      onComplete();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to generate roadmap.');
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="w-full max-w-2xl overflow-hidden glassmorphism border border-slate-800 rounded-3xl shadow-2xl animate-fade-in-up">
        
        {/* Header */}
        <div className="p-6 border-b border-slate-800/80 flex items-center justify-between">
          <div>
            <span className="text-xs font-black tracking-widest text-indigo-400 uppercase font-sans">Onboarding Assistant</span>
            <h2 className="text-xl font-black text-slate-100 mt-1 font-sans">Configure Your Career Roadmap</h2>
          </div>
          <Sparkles className="h-5 w-5 text-indigo-400 animate-pulse" />
        </div>

        {/* Progress Bar */}
        <div className="px-6 py-4 bg-slate-900/40 border-b border-slate-800/40 flex justify-between items-center text-xs font-sans">
          {STEPS.map((s, idx) => {
            const isCompleted = activeStep > idx;
            const isActive = activeStep === idx;
            return (
              <div key={s.id} className="flex items-center gap-1.5">
                <div
                  className={`h-5 w-5 rounded-full flex items-center justify-center font-bold transition-all ${
                    isCompleted ? 'bg-indigo-500 text-slate-950' :
                    isActive ? 'bg-slate-200 text-slate-950 ring-4 ring-indigo-500/20' :
                    'bg-slate-800 text-slate-400'
                  }`}
                >
                  {isCompleted ? '✓' : idx + 1}
                </div>
                <span className={`font-semibold ${isActive ? 'text-slate-200' : 'text-slate-400'}`}>{s.title}</span>
                {idx < STEPS.length - 1 && <ChevronRight className="h-3 w-3 text-slate-600" />}
              </div>
            );
          })}
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 font-sans">
          {error && (
            <div className="p-4 rounded-xl flex gap-3 text-sm bg-red-500/10 border border-red-500/20 text-red-400">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center space-y-4">
              <Loader2 className="h-10 w-10 text-indigo-400 animate-spin" />
              <p className="text-sm font-semibold text-slate-300">{statusText}</p>
            </div>
          ) : (
            <>
              {activeStep === 0 && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <h3 className="text-lg font-bold text-slate-100">Step 1: Upload Your Resume</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">
                      Upload your resume in PDF format. SATA automatically scans the text using Gemini to build your initial technical skills profile based on your target career role (<span className="text-indigo-400 font-bold">{primaryRole}</span>).
                    </p>
                  </div>

                  <div className="border-2 border-dashed border-slate-800 rounded-2xl p-8 flex flex-col items-center justify-center gap-3 transition-colors hover:border-slate-700 bg-slate-900/20">
                    <Upload className="h-10 w-10 text-slate-500" />
                    <div className="text-center">
                      <p className="text-sm font-bold text-slate-300">
                        {file ? file.name : 'Select your PDF resume'}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">PDF file formats supported up to 10MB</p>
                    </div>
                    <label className="px-4 py-2 bg-slate-800 text-slate-200 text-xs font-bold rounded-xl cursor-pointer hover:bg-slate-700 transition-all">
                      Choose File
                      <input type="file" accept="application/pdf" className="hidden" onChange={handleFileChange} />
                    </label>
                  </div>

                  <button
                    onClick={handleUploadResume}
                    disabled={!file}
                    className="w-full py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-slate-950 font-black rounded-xl text-sm transition-all hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
                  >
                    Analyze Resume <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              )}

              {activeStep === 1 && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <h3 className="text-lg font-bold text-slate-100">Step 2: Add GitHub Repositories (Optional)</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">
                      SATA verifies your real project experience. Provide up to 3 public GitHub repositories so we can scan commits, README depth, and config files to boost your project scores.
                    </p>
                  </div>

                  <div className="space-y-3">
                    {repos.map((url, idx) => (
                      <div key={idx}>
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Repo URL #{idx + 1}</label>
                        <input
                          type="text"
                          placeholder="e.g. https://github.com/username/project"
                          className="w-full px-3 py-2.5 bg-slate-900/60 border border-slate-800 rounded-xl text-sm text-slate-200 outline-none focus:border-indigo-500/50 transition-all"
                          value={url}
                          onChange={e => {
                            const newRepos = [...repos];
                            newRepos[idx] = e.target.value;
                            setRepos(newRepos);
                          }}
                        />
                      </div>
                    ))}
                  </div>

                  <div className="flex gap-3 pt-2">
                    <button
                      onClick={() => handleGitHubSubmit(true)}
                      className="flex-1 py-3 bg-slate-900 text-slate-300 font-bold border border-slate-800 rounded-xl text-sm hover:bg-slate-800 transition-all"
                    >
                      Skip this step
                    </button>
                    <button
                      onClick={() => handleGitHubSubmit(false)}
                      disabled={!repos.some(url => url.trim().toLowerCase().includes('github.com'))}
                      className="flex-1 py-3 bg-indigo-500 text-slate-950 font-black rounded-xl text-sm hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      Verify Repositories
                    </button>
                  </div>
                </div>
              )}

              {activeStep === 2 && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <h3 className="text-lg font-bold text-slate-100">Step 3: Preview Alignment Gaps</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">
                      SATA has completed matching your resume and project signals against the requirements for <span className="text-indigo-400 font-bold">{primaryRole}</span>.
                    </p>
                  </div>

                  {activeGap ? (
                    <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
                      <div className="flex justify-between items-center pb-3 border-b border-slate-800/60">
                        <div>
                          <p className="text-xs font-bold text-slate-400">Target Role</p>
                          <p className="text-base font-black text-slate-200">{primaryRole}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs font-bold text-slate-400">Skill Alignment</p>
                          <p className="text-lg font-black text-indigo-400">{Math.round(activeGap.match_score)}%</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs font-bold text-red-400 mb-1.5">Missing Skills ({activeGap.missing_skills?.length || 0})</p>
                          <div className="flex flex-wrap gap-1">
                            {activeGap.missing_skills?.slice(0, 3).map((s: any, idx: number) => (
                              <span key={idx} className="px-2 py-0.5 rounded bg-red-950/30 border border-red-900/30 text-red-400 text-[10px] font-semibold">{s.skill_name}</span>
                            ))}
                            {activeGap.missing_skills?.length > 3 && <span className="text-[10px] text-slate-500 font-semibold self-center ml-1">+{activeGap.missing_skills.length - 3} more</span>}
                          </div>
                        </div>

                        <div>
                          <p className="text-xs font-bold text-amber-400 mb-1.5">High Potential ({activeGap.high_potential_skills?.length || 0})</p>
                          <div className="flex flex-wrap gap-1">
                            {activeGap.high_potential_skills?.slice(0, 3).map((s: any, idx: number) => (
                              <span key={idx} className="px-2 py-0.5 rounded bg-amber-950/30 border border-amber-900/30 text-amber-400 text-[10px] font-semibold">{s.skill_name}</span>
                            ))}
                            {activeGap.high_potential_skills?.length > 3 && <span className="text-[10px] text-slate-500 font-semibold self-center ml-1">+{activeGap.high_potential_skills.length - 3} more</span>}
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="p-4 text-center rounded-xl bg-slate-900/40 border border-slate-800 text-slate-400 text-sm">
                      Retrieving skill gap alignment details...
                    </div>
                  )}

                  <button
                    onClick={handleShowGapAnalysis}
                    className="w-full py-3 bg-indigo-500 text-slate-950 font-black rounded-xl text-sm hover:opacity-90 transition-all flex items-center justify-center gap-1.5"
                  >
                    Proceed to Roadmap <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              )}

              {activeStep === 3 && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <h3 className="text-lg font-bold text-slate-100">Step 4: Generate Your Learning Roadmap</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">
                      We will structure a personalized, sequential roadmap targeting your skill gaps for <span className="text-indigo-400 font-bold">{primaryRole}</span>. Practice interview task types are fully integrated into each skill stage.
                    </p>
                  </div>

                  <div className="p-5 rounded-2xl bg-indigo-950/10 border border-indigo-900/20 flex gap-4">
                    <div className="h-10 w-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center flex-shrink-0 text-indigo-400">
                      <Sparkles className="w-5 h-5 animate-pulse" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-200">Personalized Practice Screens Included</h4>
                      <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                        Rather than starting with a mandatory full interview screen, practice technical interview tasks are generated directly under each prioritized skill node.
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={handleGenerateRoadmap}
                    className="w-full py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-slate-950 font-black rounded-xl text-sm hover:opacity-90 transition-all"
                  >
                    Generate My Personal Roadmap
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
