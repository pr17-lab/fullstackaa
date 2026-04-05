import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import {
  User, BookOpen, Briefcase, CheckCircle,
  ChevronRight, ChevronLeft, AlertCircle, Loader2, Plus, X
} from 'lucide-react';

const DEPARTMENTS = ["CSE", "ECE", "AIML", "MECH", "AI&ML"];
const DOMAINS = ["Software", "Hardware", "UI/UX", "AI/ML", "Data", "Embedded systems"];
const TARGET_ROLES = [
  "Software Engineer", "Data Scientist", "Data Engineer",
  "Frontend Developer", "Backend Developer", "Full Stack Developer",
  "DevOps Engineer", "Cybersecurity Analyst", "Embedded Systems Engineer",
  "Hardware/VLSI Design Engineer", "Machine Learning Engineer"
];

export default function Register() {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  // Standard form inputs
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    studentId: '',
    password: '',
    department: '',
    batchYear: new Date().getFullYear(),
    currentSemester: 1
  });

  // Academic Records logic
  const [academicRecords, setAcademicRecords] = useState<any[]>([]);
  const [activeSemTab, setActiveSemTab] = useState(1);
  const [fetchingTemplates, setFetchingTemplates] = useState(false);

  // Preference logic
  const [preferences, setPreferences] = useState({
    targetRoles: [] as string[],
    preferredDomains: [] as string[],
    timelineMonths: 6,
    openToRemote: true,
    experienceLevel: "fresher"
  });

  // Handle initialization of academic records when semester/department changes
  useEffect(() => {
    if (step === 2 && formData.department && formData.currentSemester > 0) {
      if (academicRecords.length !== formData.currentSemester) {
        initAcademicRecords();
      }
    }
  }, [step, formData.department, formData.currentSemester]);

  const initAcademicRecords = async () => {
    setFetchingTemplates(true);
    try {
      const records = [];
      for (let s = 1; s <= formData.currentSemester; s++) {
        // Fetch existing subjects for placeholder template
        const { data } = await api.get(`/auth/subject-templates?department=${formData.department}&semester=${s}`);
        
        let subjects = data || [];
        // Map templates to the input shape
        subjects = subjects.map((sub: any) => ({
          subject_name: sub.subject_name,
          subject_code: sub.subject_code,
          credits: sub.credits,
          marks_obtained: '', // Allow empty for 'unpublished'
          total_marks: 100
        }));

        records.push({
          semester: s,
          subjects: subjects
        });
      }
      setAcademicRecords(records);
      setActiveSemTab(1);
    } catch (err) {
      console.error("Template fetch error", err);
    } finally {
      setFetchingTemplates(false);
    }
  };

  const handleSubjectMarkChange = (semIndex: number, subIndex: number, val: string) => {
    const updated = [...academicRecords];
    const parsed = val === '' ? '' : parseInt(val);
    updated[semIndex].subjects[subIndex].marks_obtained = parsed;
    setAcademicRecords(updated);
  };

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
      if (!formData.fullName || !formData.email || !formData.studentId || !formData.password || !formData.department) {
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
      // Validate marks (must be <= 100 if filled)
      for (let r of academicRecords) {
        for (let sub of r.subjects) {
          if (sub.marks_obtained !== '' && (sub.marks_obtained < 0 || sub.marks_obtained > sub.total_marks)) {
            setError(`Invalid marks for ${sub.subject_name}. Must be 0 - ${sub.total_marks}.`);
            return false;
          }
        }
      }
      return true;
    }
    if (step === 3) {
      if (preferences.targetRoles.length === 0) {
        setError('Select at least one target role.');
        return false;
      }
      return true;
    }
    return true;
  };

  const nextStep = () => {
    if (validateStep()) setStep(s => Math.min(s + 1, 4));
  };
  const prevStep = () => setStep(s => Math.max(s - 1, 1));

  const submitRegistration = async () => {
    setLoading(true);
    setError('');

    try {
      // Sanitize academic records
      const sanitizedRecords = academicRecords.map(r => ({
        semester: r.semester,
        subjects: r.subjects.map((sub: any) => ({
          subject_name: sub.subject_name.trim(),
          subject_code: sub.subject_code.trim() || 'NA',
          credits: parseInt(sub.credits) || 3,
          marks_obtained: sub.marks_obtained === '' ? null : parseInt(sub.marks_obtained),
          total_marks: parseInt(sub.total_marks) || 100
        }))
      }));

      const payload = {
        full_name: formData.fullName,
        email: formData.email,
        student_id: formData.studentId,
        password: formData.password,
        department: formData.department,
        batch_year: formData.batchYear,
        current_semester: formData.currentSemester,
        academic_records: sanitizedRecords
      };

      const res = await api.post('/auth/register', payload);

      // Auto-login
      if (res.data.student_id) {
        await login(formData.studentId, formData.password);
        
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
        <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
        <input type="text" className="w-full p-2.5 border rounded-lg" value={formData.fullName} onChange={e => setFormData({...formData, fullName: e.target.value})} placeholder="Jane Doe" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
        <input type="email" className="w-full p-2.5 border rounded-lg" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} placeholder="jane@example.com" />
      </div>
      <div className="flex gap-4">
        <div className="w-1/2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Student ID (Roll No)</label>
          <input type="text" className="w-full p-2.5 border rounded-lg" value={formData.studentId} onChange={e => setFormData({...formData, studentId: e.target.value.toUpperCase()})} placeholder="S123456" />
        </div>
        <div className="w-1/2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
          <select className="w-full p-2.5 border rounded-lg" value={formData.department} onChange={e => setFormData({...formData, department: e.target.value})}>
            <option value="">Select Dept</option>
            {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
      </div>
      <div className="flex gap-4">
        <div className="w-1/2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Batch Year</label>
          <input type="number" className="w-full p-2.5 border rounded-lg" value={formData.batchYear} onChange={e => setFormData({...formData, batchYear: parseInt(e.target.value)})} />
        </div>
        <div className="w-1/2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Current Semester</label>
          <select className="w-full p-2.5 border rounded-lg" value={formData.currentSemester} onChange={e => setFormData({...formData, currentSemester: parseInt(e.target.value)})}>
            {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
          </select>
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
        <input type="password" className="w-full p-2.5 border rounded-lg" value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} placeholder="Minimum 8 characters with numbers" />
      </div>
    </div>
  );

  const renderStep2 = () => {
    if (fetchingTemplates) {
      return (
        <div className="py-12 flex flex-col items-center justify-center text-gray-500">
          <Loader2 className="w-8 h-8 animate-spin mb-4" />
          <p>Generating academic templates...</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        <p className="text-sm text-gray-500">Enter your marks for each semester. Leave blank if results are not yet published.</p>
        
        {/* Semester Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2 border-b">
          {academicRecords.map((r, i) => (
            <button
              key={r.semester}
              onClick={() => setActiveSemTab(i + 1)}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors whitespace-nowrap ${
                activeSemTab === r.semester
                  ? 'bg-indigo-50 text-indigo-700 border-b-2 border-indigo-600'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              Sem {r.semester}
            </button>
          ))}
        </div>

        {/* Subjects list for active tab */}
        <div className="space-y-4">
          {academicRecords[activeSemTab - 1]?.subjects.map((sub: any, idx: number) => (
            <div key={idx} className="flex items-center gap-4 bg-gray-50 p-4 rounded-xl border border-gray-100">
              <div className="flex-1">
                <p className="font-medium text-sm text-gray-900">{sub.subject_name}</p>
                <p className="text-xs text-gray-500">{sub.subject_code} • {sub.credits} Credits</p>
              </div>
              <div className="w-24">
                <label className="text-xs text-gray-500 block mb-1">Marks</label>
                <input 
                  type="number"
                  placeholder="-"
                  className="w-full p-2 border rounded bg-white text-center text-sm"
                  value={sub.marks_obtained}
                  onChange={(e) => handleSubjectMarkChange(activeSemTab - 1, idx, e.target.value)}
                  min="0"
                  max={sub.total_marks}
                />
              </div>
              <div className="w-16">
                <label className="text-xs text-gray-500 block mb-1">Total</label>
                <input 
                  type="number"
                  className="w-full p-2 border rounded bg-gray-100 text-center text-sm text-gray-500"
                  value={sub.total_marks}
                  readOnly
                />
              </div>
            </div>
          ))}
          {academicRecords[activeSemTab - 1]?.subjects.length === 0 && (
            <p className="text-sm text-gray-500 italic py-4">No predefined templates for this semester. In a real app, you would be able to manually add subjects here.</p>
          )}
        </div>
      </div>
    );
  };

  const renderStep3 = () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-sm font-medium text-gray-900 mb-3">Preferred Target Roles</h3>
        <div className="flex flex-wrap gap-2">
          {TARGET_ROLES.map(role => {
            const isSelected = preferences.targetRoles.includes(role);
            return (
              <button
                key={role}
                onClick={() => togglePrefArray('targetRoles', role)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                  isSelected 
                    ? 'bg-indigo-600 text-white shadow-md' 
                    : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
                }`}
              >
                {isSelected ? <CheckCircle className="w-4 h-4" /> : <Plus className="w-4 h-4 text-gray-400" />}
                {role}
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-medium text-gray-900 mb-3">Preferred Domains</h3>
        <div className="flex flex-wrap gap-2">
          {DOMAINS.map(domain => {
            const isSelected = preferences.preferredDomains.includes(domain);
            return (
              <button
                key={domain}
                onClick={() => togglePrefArray('preferredDomains', domain)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                  isSelected 
                    ? 'bg-violet-600 text-white shadow-md' 
                    : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
                }`}
              >
                {isSelected ? <CheckCircle className="w-4 h-4" /> : <Plus className="w-4 h-4 text-gray-400" />}
                {domain}
              </button>
            );
          })}
        </div>
      </div>

      <div className="bg-blue-50/50 p-4 rounded-xl border border-blue-100">
        <p className="text-sm text-blue-800">
          This data will immediately be used to generate your personalized skill gaps and career roadmap after registration.
        </p>
      </div>
    </div>
  );

  const renderStep4 = () => {
    // Calculate simple stats
    const filledSubjects = academicRecords.reduce((acc, r) => acc + r.subjects.filter((s:any) => s.marks_obtained !== '').length, 0);
    const totalSubjects = academicRecords.reduce((acc, r) => acc + r.subjects.length, 0);

    return (
      <div className="space-y-6">
        <div className="bg-gray-50 rounded-xl p-6 border border-gray-100 space-y-4">
          <h3 className="font-semibold text-gray-900 border-b pb-2">Profile Summary</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="text-gray-500">Name:</span> <span className="font-medium text-gray-900">{formData.fullName}</span></div>
            <div><span className="text-gray-500">Email:</span> <span className="font-medium text-gray-900">{formData.email}</span></div>
            <div><span className="text-gray-500">Student ID:</span> <span className="font-medium text-gray-900">{formData.studentId}</span></div>
            <div><span className="text-gray-500">Department:</span> <span className="font-medium text-gray-900">{formData.department} ({formData.batchYear})</span></div>
          </div>
          
          <h3 className="font-semibold text-gray-900 border-b pb-2 pt-4">Academic Import</h3>
          <p className="text-sm text-gray-700">Importing <span className="font-medium">{filledSubjects} / {totalSubjects}</span> subjects with grades across {formData.currentSemester} semesters.</p>

          <h3 className="font-semibold text-gray-900 border-b pb-2 pt-4">Career Targets</h3>
          <div className="flex flex-wrap gap-2">
            {preferences.targetRoles.map(r => (
              <span key={r} className="text-xs font-medium px-2 py-1 bg-indigo-100 text-indigo-700 rounded-md">{r}</span>
            ))}
          </div>
        </div>

        <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4 flex gap-3 text-indigo-800">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm">Clicking "Submit & Compute" will create your SATA portal account and trigger our AI to analyze your academic background against your career targets.</p>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 py-12 px-4 sm:px-6 flex items-center justify-center">
      <div className="max-w-3xl w-full">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            SATA Initial Setup
          </h1>
          <p className="mt-2 text-lg leading-8 text-gray-600">
            Welcome! Let's build your AI career tracking profile.
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl shadow-gray-200/50 overflow-hidden border border-gray-100 flex flex-col sm:flex-row min-h-[500px]">
          {/* Progress Sidebar */}
          <div className="bg-gray-50 w-full sm:w-64 p-6 sm:border-r border-b sm:border-b-0 border-gray-100 flex-shrink-0">
            <nav aria-label="Progress">
              <ol role="list" className="space-y-6">
                {[
                  { id: 1, name: 'Personal Details', icon: User },
                  { id: 2, name: 'Academic Record', icon: BookOpen },
                  { id: 3, name: 'Career Preference', icon: Briefcase },
                  { id: 4, name: 'Review', icon: CheckCircle },
                ].map((s) => (
                  <li key={s.id}>
                    <div className="flex items-center">
                      <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 transition-colors ${
                        step === s.id ? 'border-indigo-600 bg-indigo-50 text-indigo-600' : 
                        step > s.id ? 'border-indigo-600 bg-indigo-600 text-white' : 
                        'border-gray-200 bg-white text-gray-400'
                      }`}>
                        <s.icon className="w-4 h-4" />
                      </div>
                      <span className={`ml-3 text-sm font-medium transition-colors ${
                        step === s.id ? 'text-indigo-600' : 
                        step > s.id ? 'text-gray-900' : 
                        'text-gray-500'
                      }`}>{s.name}</span>
                    </div>
                  </li>
                ))}
              </ol>
            </nav>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 flex flex-col p-8 bg-white relative">
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
                  <div className="mb-6 bg-red-50 text-red-600 px-4 py-3 rounded-lg flex items-center gap-2 text-sm border border-red-100">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                )}
                
                {step === 1 && renderStep1()}
                {step === 2 && renderStep2()}
                {step === 3 && renderStep3()}
                {step === 4 && renderStep4()}
              </motion.div>
            </AnimatePresence>

            {/* Navigation Footer */}
            <div className="mt-8 pt-6 border-t border-gray-100 flex items-center justify-between">
              {step > 1 ? (
                <button
                  type="button"
                  onClick={prevStep}
                  disabled={loading}
                  className="flex items-center text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors bg-white px-4 py-2 rounded-lg border hover:bg-gray-50"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" /> Back
                </button>
              ) : (
                <div /> // Placeholder
              )}

              {step < 4 ? (
                <button
                  type="button"
                  onClick={nextStep}
                  className="flex items-center text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 transition-colors px-6 py-2 rounded-lg shadow-sm"
                >
                  Next <ChevronRight className="w-4 h-4 ml-1" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={submitRegistration}
                  disabled={loading}
                  className="flex items-center text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 transition-all px-6 py-2 rounded-lg shadow-md disabled:opacity-70"
                >
                  {loading ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Processing...</>
                  ) : 'Submit & Compute Profiles'}
                </button>
              )}
            </div>
          </div>
        </div>
        
        {/* Helper Link */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            Already have an account?{' '}
            <button onClick={() => navigate('/login')} className="font-medium text-indigo-600 hover:text-indigo-500">
              Sign in instead
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
