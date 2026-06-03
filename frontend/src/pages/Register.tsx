import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api/client';
import {
  User, Briefcase, CheckCircle,
  ChevronRight, ChevronLeft, AlertCircle, Loader2, Plus, X
} from 'lucide-react';

const DEPARTMENTS = ["CSE", "ECE", "AIML", "MECH", "AI&ML"];
const DOMAINS = ["Software", "Hardware", "UI/UX", "AI/ML", "Data", "Embedded systems", "Mechanical", "Manufacturing", "Automotive"];
const TARGET_ROLES = [
  "Software Engineer", "Data Scientist", "Data Engineer",
  "Frontend Developer", "Backend Developer", "Full Stack Developer",
  "DevOps Engineer", "Cybersecurity Analyst", "Embedded Systems Engineer",
  "Hardware/VLSI Design Engineer", "Machine Learning Engineer",
  "Mechanical Design Engineer", "Manufacturing Engineer", "Automotive Engineer",
  "HVAC Engineer", "Robotics/Mechatronics Engineer"
];

export default function Register() {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  // Standard form inputs (Step 1)
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    department: '',
    batchYear: new Date().getFullYear(),
  });

  // Preference logic (Step 2)
  const [preferences, setPreferences] = useState({
    targetRoles: [] as string[],
    preferredDomains: [] as string[],
    timelineMonths: 6,
    openToRemote: true,
    experienceLevel: "fresher"
  });

  const togglePrefArray = (key: 'targetRoles' | 'preferredDomains', value: string) => {
    setPreferences(prev => {
      const arr = prev[key];
      if (arr.includes(value)) {
        return { ...prev, [key]: arr.filter(x => x !== value) };
      } else {
        return { ...prev, [key]: [...arr, value] };
      }
    });
  };

  const validateStep = () => {
    setError('');
    if (step === 1) {
      if (!formData.fullName || !formData.email || !formData.password || !formData.department) {
        setError('Please fill in all required fields.');
        return false;
      }
      if (formData.password.length < 8) {
        setError('Password must be at least 8 characters long.');
        return false;
      }
      return true;
    }
    if (step === 2) {
      if (preferences.targetRoles.length === 0) {
        setError('Select at least one target role.');
        return false;
      }
      return true;
    }
    return true;
  };

  const nextStep = () => {
    if (validateStep()) setStep(s => Math.min(s + 1, 3));
  };
  const prevStep = () => setStep(s => Math.max(s - 1, 1));

  const submitRegistration = async () => {
    setLoading(true);
    setError('');

    try {
      const payload = {
        full_name: formData.fullName,
        email: formData.email,
        password: formData.password,
        department: formData.department,
        batch_year: formData.batchYear,
        current_semester: 1, // Defaulting as backend requires it, but UI ignores it
      };

      const res = await api.post('/auth/register', payload);

      // Auto-login
      if (res.data.student_id || res.data.id) {
        // use student_id or email for login
        const loginId = res.data.student_id || res.data.email;
        await login(loginId, formData.password);
        
        // POST Preferences (will use token from login)
        try {
          await api.post('/preferences', {
             target_roles: preferences.targetRoles,
             preferred_domains: preferences.preferredDomains,
             open_to_remote: preferences.openToRemote,
             career_transition: false,
             transition_from: null,
             transition_to: null,
             timeline_months: preferences.timelineMonths,
             experience_level: preferences.experienceLevel
          });
        } catch (prefErr) {
          console.warn("Failed to save initial preferences:", prefErr);
        }

        navigate('/');
      }

    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // --------------------------------------------------------------------------
  // UI rendering per step
  // --------------------------------------------------------------------------

  const renderStep1 = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Full Name</label>
        <input type="text" className="w-full p-2.5 rounded-xl text-sm transition-all" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-primary)', color: 'var(--text-primary)', outline: 'none' }} value={formData.fullName} onChange={e => setFormData({...formData, fullName: e.target.value})} placeholder="Jane Doe" />
      </div>
      <div>
        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Email Address</label>
        <input type="email" className="w-full p-2.5 rounded-xl text-sm transition-all" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-primary)', color: 'var(--text-primary)', outline: 'none' }} value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} placeholder="jane@example.com" />
      </div>
      <div className="flex gap-4">
        <div className="w-1/2">
          <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Department</label>
          <select className="w-full p-2.5 rounded-xl text-sm transition-all" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-primary)', color: 'var(--text-primary)', outline: 'none' }} value={formData.department} onChange={e => setFormData({...formData, department: e.target.value})}>
            <option value="" style={{ background: '#151e2d' }}>Select Dept</option>
            {DEPARTMENTS.map(d => <option key={d} value={d} style={{ background: '#151e2d' }}>{d}</option>)}
          </select>
        </div>
        <div className="w-1/2">
          <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Batch Year</label>
          <input type="number" className="w-full p-2.5 rounded-xl text-sm" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-primary)', color: 'var(--text-primary)', outline: 'none' }} value={formData.batchYear} onChange={e => setFormData({...formData, batchYear: parseInt(e.target.value)})} />
        </div>
      </div>
      <div>
        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Password</label>
        <input type="password" className="w-full p-2.5 rounded-xl text-sm" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-primary)', color: 'var(--text-primary)', outline: 'none' }} value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} placeholder="Minimum 8 characters with numbers" />
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>Experience Level</h3>
        <div className="flex gap-3">
          {["Fresher", "Intern", "Junior"].map(level => {
            const val = level.toLowerCase();
            const isSelected = preferences.experienceLevel === val;
            return (
              <button
                key={level}
                onClick={() => setPreferences({ ...preferences, experienceLevel: val })}
                className="flex-1 py-2 rounded-xl text-sm font-semibold transition-all"
                style={{ 
                  background: isSelected ? 'rgba(129,140,248,0.12)' : 'rgba(255,255,255,0.03)',
                  border: isSelected ? '1px solid #818cf8' : '1px solid var(--border-primary)',
                  color: isSelected ? '#818cf8' : 'var(--text-secondary)'
                }}
              >
                {level}
              </button>
            )
          })}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>Target Roles</h3>
        <div className="flex flex-wrap gap-2">
          {TARGET_ROLES.map(role => {
            const isSelected = preferences.targetRoles.includes(role);
            return (
              <button
                key={role}
                onClick={() => togglePrefArray('targetRoles', role)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all"
                style={{
                  background: isSelected ? 'rgba(129,140,248,0.12)' : 'rgba(255,255,255,0.03)',
                  color: isSelected ? '#818cf8' : 'var(--text-secondary)',
                  border: isSelected ? '1px solid #818cf8' : '1px solid var(--border-primary)'
                }}
              >
                {isSelected ? <CheckCircle className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" style={{ color: 'var(--text-tertiary)' }} />}
                {role}
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>Preferred Domains</h3>
        <div className="flex flex-wrap gap-2">
          {DOMAINS.map(domain => {
            const isSelected = preferences.preferredDomains.includes(domain);
            return (
              <button
                key={domain}
                onClick={() => togglePrefArray('preferredDomains', domain)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all"
                style={{
                  background: isSelected ? 'rgba(139,92,246,0.12)' : 'rgba(255,255,255,0.03)',
                  color: isSelected ? '#a78bfa' : 'var(--text-secondary)',
                  border: isSelected ? '1px solid #8b5cf6' : '1px solid var(--border-primary)'
                }}
              >
                {isSelected ? <CheckCircle className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" style={{ color: 'var(--text-tertiary)' }} />}
                {domain}
              </button>
            );
          })}
        </div>
      </div>

      <div className="rounded-xl p-4 flex gap-3" style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)', color: '#a5b4fc' }}>
        <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <p className="text-sm">
          Your career intent drives the AI analysis. The system will match your verified GitHub projects and live interview performance directly against these targets.
        </p>
      </div>
    </div>
  );

  const renderStep3 = () => {
    return (
      <div className="space-y-6">
        <div className="rounded-xl p-5" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-primary)' }}>
          <h3 className="font-semibold pb-2 mb-3 text-sm" style={{ color: 'var(--text-primary)', borderBottom: '1px solid var(--border-primary)' }}>Your Identity</h3>
          <div className="grid grid-cols-2 gap-3 text-sm mb-4">
            <div><span style={{ color: 'var(--text-tertiary)' }}>Name:</span> <span className="font-medium ml-1" style={{ color: 'var(--text-primary)' }}>{formData.fullName}</span></div>
            <div><span style={{ color: 'var(--text-tertiary)' }}>Email:</span> <span className="font-medium ml-1" style={{ color: 'var(--text-primary)' }}>{formData.email}</span></div>
            <div><span style={{ color: 'var(--text-tertiary)' }}>Department:</span> <span className="font-medium ml-1" style={{ color: 'var(--text-primary)' }}>{formData.department} ({formData.batchYear})</span></div>
            <div><span style={{ color: 'var(--text-tertiary)' }}>Experience:</span> <span className="font-medium ml-1 capitalize" style={{ color: 'var(--text-primary)' }}>{preferences.experienceLevel}</span></div>
          </div>

          <h3 className="font-semibold pb-2 mb-3 text-sm pt-3" style={{ color: 'var(--text-primary)', borderBottom: '1px solid var(--border-primary)', borderTop: '1px solid var(--border-primary)', paddingTop: '0.75rem' }}>Career Targets</h3>
          <div className="flex flex-wrap gap-2 mb-4">
            {preferences.targetRoles.map(r => (
              <span key={r} className="text-xs font-semibold px-2.5 py-1 rounded-full" style={{ background: 'rgba(129,140,248,0.12)', color: '#818cf8', border: '1px solid rgba(129,140,248,0.22)' }}>{r}</span>
            ))}
          </div>

          <h3 className="font-semibold pb-2 mb-3 text-sm" style={{ color: 'var(--text-primary)', borderBottom: '1px solid var(--border-primary)' }}>Domains</h3>
          <div className="flex flex-wrap gap-2">
            {preferences.preferredDomains.map(r => (
              <span key={r} className="text-xs font-semibold px-2.5 py-1 rounded-full" style={{ background: 'rgba(139,92,246,0.12)', color: '#a78bfa', border: '1px solid rgba(139,92,246,0.22)' }}>{r}</span>
            ))}
          </div>
        </div>

        <div className="rounded-xl p-4 flex gap-3 mt-4" style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)' }}>
          <AlertCircle className="w-5 h-5 flex-shrink-0" style={{ color: '#818cf8' }} />
          <p className="text-sm" style={{ color: '#a5b4fc' }}>
            Clicking "Launch My Career Profile" will create your account. After launching, upload your resume and connect your GitHub to begin AI skill calibration.
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen py-10 px-4 sm:px-6 flex items-center justify-center" style={{ background: 'var(--bg-page)', position: 'relative', overflow: 'hidden' }}>
      {/* Background glow blobs */}
      <div style={{ position: 'absolute', top: '-10%', left: '-10%', width: '500px', height: '500px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(99,102,241,0.06) 0%, transparent 70%)', pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', bottom: '-10%', right: '-10%', width: '400px', height: '400px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(139,92,246,0.05) 0%, transparent 70%)', pointerEvents: 'none' }} />

      <div className="max-w-3xl w-full animate-fade-in">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4" style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', boxShadow: '0 0 32px rgba(99,102,241,0.4)' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          </div>
          <p className="section-label mb-1">Career Intelligence Portal</p>
          <h1 className="text-3xl font-black tracking-tight mb-2" style={{ color: 'var(--text-primary)' }}>
            Create Your Career Profile
          </h1>
          <p style={{ color: 'var(--text-tertiary)', fontSize: '0.9375rem' }}>Your AI-powered career engine starts here.</p>
        </div>

        <div className="rounded-2xl overflow-hidden flex flex-col sm:flex-row" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-primary)', boxShadow: '0 24px 48px rgba(0,0,0,0.4)', minHeight: '520px' }}>
          {/* Progress Sidebar */}
          <div className="w-full sm:w-60 p-6 flex-shrink-0" style={{ background: 'var(--bg-sidebar)', borderRight: '1px solid var(--border-primary)' }}>
            <p className="section-label mb-5">Setup Progress</p>
            <nav aria-label="Progress">
              <ol role="list" className="space-y-5">
                {[
                  { id: 1, name: 'Your Identity', icon: User },
                  { id: 2, name: 'Career Intent', icon: Briefcase },
                  { id: 3, name: 'Review & Launch', icon: CheckCircle },
                ].map((s) => (
                  <li key={s.id}>
                    <div className="flex items-center">
                      <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 transition-all ${
                        step === s.id ? 'border-[#818cf8] text-[#818cf8]' :
                        step > s.id ? 'border-[#6366f1] text-white' :
                        'border-[rgba(255,255,255,0.1)] text-[var(--text-tertiary)]'
                      }`} style={step > s.id ? { background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' } : step === s.id ? { background: 'rgba(129,140,248,0.1)' } : { background: 'rgba(255,255,255,0.03)' }}>
                        <s.icon className="w-4 h-4" />
                      </div>
                      <span className={`ml-3 text-sm font-medium transition-colors ${
                        step === s.id ? 'text-[#818cf8]' :
                        step > s.id ? 'text-[var(--text-primary)]' :
                        'text-[var(--text-tertiary)]'
                      }`}>{s.name}</span>
                    </div>
                  </li>
                ))}
              </ol>
            </nav>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 flex flex-col p-7" style={{ background: 'var(--bg-surface)' }}>
            <AnimatePresence mode="wait">
              <motion.div
                key={step}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
                className="flex-1"
              >
                {error && (
                  <div className="mb-5 px-4 py-3 rounded-xl flex items-center gap-2 text-sm" style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#f87171' }}>
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                )}
                
                {step === 1 && renderStep1()}
                {step === 2 && renderStep2()}
                {step === 3 && renderStep3()}
              </motion.div>
            </AnimatePresence>

            {/* Navigation Footer */}
            <div className="mt-8 pt-5 flex items-center justify-between" style={{ borderTop: '1px solid var(--border-primary)' }}>
              {step > 1 ? (
                <button
                  type="button"
                  onClick={prevStep}
                  disabled={loading}
                  className="flex items-center text-sm font-semibold px-4 py-2 rounded-xl transition-all"
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-primary)', color: 'var(--text-secondary)' }}
                >
                  <ChevronLeft className="w-4 h-4 mr-1" /> Back
                </button>
              ) : (
                <div />
              )}

              {step < 3 ? (
                <button
                  type="button"
                  onClick={nextStep}
                  className="flex items-center text-sm font-bold text-white px-6 py-2.5 rounded-xl transition-all"
                  style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', boxShadow: '0 4px 14px rgba(99,102,241,0.35)' }}
                >
                  Next <ChevronRight className="w-4 h-4 ml-1" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={submitRegistration}
                  disabled={loading}
                  className="flex items-center text-sm font-bold text-white px-6 py-2.5 rounded-xl transition-all disabled:opacity-60"
                  style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', boxShadow: '0 4px 14px rgba(99,102,241,0.3)' }}
                >
                  {loading ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Launching...</>
                  ) : 'Launch My Career Profile'}
                </button>
              )}
            </div>
          </div>
        </div>
        
        {/* Helper Link */}
        <div className="mt-5 text-center">
          <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
            Already have an account?{' '}
            <button onClick={() => navigate('/login')} className="font-semibold transition-colors" style={{ color: 'var(--brand-primary)' }}>
              Sign in instead
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
