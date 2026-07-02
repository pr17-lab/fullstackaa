// ─── V2 Career Intelligence Types ─────────────────────────────────────────────

export interface StudentSkill {
  skill_id: string;
  skill_name: string;
  category: string;
  confidence_score: number;
  /** 'strong' | 'moderate' | 'weak' */
  level: string;
  source: string[];
  last_computed_at: string | null;
}

export interface SkillGap {
  job_role: string;
  match_score: number;
  /** 'Excellent' | 'Good' | 'Potential' */
  match_label: string;
  missing_skills: Array<{ skill_id: string; skill_name?: string; importance: string; gap: boolean }>;
  weak_skills: Array<{ skill_id: string; skill_name?: string; score: number; required: number }>;
  strong_skills: Array<{ skill_id: string; skill_name?: string; score: number }>;
  high_potential_skills: Array<{ skill_id: string; skill_name?: string; parent_id?: string; parent_name?: string }>;
  computed_at: string | null;
}

export interface SkillsSummary {
  total_skills: number;
  strong_count: number;
  moderate_count: number;
  weak_count: number;
  top_skills: StudentSkill[];
  skill_gaps: SkillGap[];
}

export interface CareerRecommendation {
  primary: {
    job_role: string;
    match_score: number;
    match_label: string;
  };
  alternatives: Array<{
    job_role: string;
    match_score: number;
    match_label: string;
  }>;
  is_transition: boolean;
  transition_target: string | null;
}

export interface RoadmapTask {
  id: string;
  roadmap_id: string;
  phase: string;           // 'learn' | 'practice' | 'apply'
  task_type: string;       // 'course' | 'exercise' | 'project'
  title: string;
  description: string | null;
  resource_url: string | null;
  platform: string | null;
  estimated_hours: number;
  order_index: number;
  status: string;          // 'pending' | 'completed' | 'skipped'
  completed_at: string | null;
  feedback_score: number | null;
  skill_name: string | null;
  /** Backend validation fields for project tasks */
  validation_status?: string | null;   // 'pending' | 'verified' | 'failed'
  submission_link?: string | null;
  associated_skill_id?: string | null;
  skill_id?: string | null;
}

export interface Roadmap {
  id: string;
  job_role: string;
  version: number;
  status: string;           // 'active' | 'completed' | 'archived'
  completion_percentage: number;
  total_tasks: number;
  completed_tasks: number;
  is_transition: boolean;
  generated_by: string;
  created_at: string;
  updated_at: string;
}

export type RoadmapDetail = Roadmap & {
  user_id: string;
  tasks: RoadmapTask[];
};

export interface StudentPreferences {
  id?: string;
  user_id?: string;
  target_roles: string[];
  preferred_domains: string[];
  open_to_remote: boolean;
  career_transition: boolean;
  transition_from: string | null;
  transition_to: string | null;
  timeline_months: number;
  experience_level: string;
  created_at?: string;
  updated_at?: string;
}

export interface JobListing {
  job_id: string;
  job_title: string;
  employer_name: string;
  job_city: string;
  job_country: string;
  job_apply_link: string;
  job_description: string;
  job_posted_at_datetime_utc: string;
}

export interface JobListingsResponse {
  job_role: string;
  source: string;
  jobs: JobListing[];
  cached: boolean;
  fetched_at: string;
}

export interface TaxonomySearchResponse {
  id: string;
  skill_name: string;
  category: string;
}
