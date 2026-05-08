import { useState, useRef, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Map, ChevronDown, Zap, BookOpen, Code2, ExternalLink,
  CheckCircle2, SkipForward, Star, AlertTriangle, RefreshCw,
  ArrowRight, Clock, Trophy, Loader2, GripVertical, PlayCircle, Plus, Trash2, X
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import {
  DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors, DragEndEvent, DragOverlay, defaultDropAnimationSideEffects
} from '@dnd-kit/core';
import {
  SortableContext, arrayMove, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { RoadmapService, PreferencesService } from '../services/api';
import { ErrorDisplay } from '../components/common/Loading';
import type { Roadmap, RoadmapDetail, RoadmapTask } from '../types/career';
import { PageTransition } from '../components/layout/PageTransition';

// ─── Constants ────────────────────────────────────────────────────────────────

const PLATFORM_COLORS: Record<string, string> = {
  Coursera: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400',
  LeetCode: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-400',
  Kaggle: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-400',
  Udemy: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-400',
  Educative: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400',
  GitHub: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300',
};

const STATUS_STYLES: Record<string, string> = {
  active: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400',
  completed: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400',
  archived: 'bg-gray-100 text-gray-500 dark:bg-zinc-800 dark:text-zinc-400',
};

const PHASE_CONFIG = [
  { key: 'learn',    label: 'Learn',    icon: BookOpen, color: '#6366f1' },
  { key: 'practice', label: 'Practice', icon: Code2,    color: '#f59e0b' },
  { key: 'apply',   label: 'Apply',    icon: Trophy,   color: '#10b981' },
] as const;

// ─── Helpers ─────────────────────────────────────────────────────────────────

function platformBadge(platform: string | null) {
  if (!platform) return null;
  const cls = PLATFORM_COLORS[platform] ?? 'bg-gray-100 text-gray-600 dark:bg-zinc-800 dark:text-zinc-300';
  return (
    <span className={`px-2 py-0.5 rounded-md text-xs font-semibold ${cls}`}>
      {platform}
    </span>
  );
}

function StarRating({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  const [hovered, setHovered] = useState(0);
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map(n => (
        <button key={n}
          type="button"
          onMouseEnter={() => setHovered(n)}
          onMouseLeave={() => setHovered(0)}
          onClick={() => onChange(n)}
          className="focus:outline-none"
        >
          <Star className={`w-5 h-5 transition-colors ${n <= (hovered || value)
            ? 'fill-amber-400 text-amber-400'
            : 'text-gray-300 dark:text-zinc-600'}`} />
        </button>
      ))}
    </div>
  );
}

// ─── Skeleton ────────────────────────────────────────────────────────────────

function SkeletonRoadmapList() {
  return (
    <div className="space-y-2">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-100 dark:border-zinc-800 p-4 animate-pulse">
          <div className="h-4 w-32 bg-gray-200 dark:bg-zinc-700 rounded mb-2" />
          <div className="h-2 w-full bg-gray-100 dark:bg-zinc-700 rounded-full" />
        </div>
      ))}
    </div>
  );
}

function SkeletonPhaseCol() {
  return (
    <div className="space-y-3">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-100 dark:border-zinc-800 p-4 animate-pulse space-y-2">
          <div className="h-4 w-40 bg-gray-200 dark:bg-zinc-700 rounded" />
          <div className="h-3 w-24 bg-gray-100 dark:bg-zinc-700 rounded" />
          <div className="h-8 w-28 bg-gray-200 dark:bg-zinc-700 rounded-lg" />
        </div>
      ))}
    </div>
  );
}

// ─── Task Card ───────────────────────────────────────────────────────────────

export function SortableTaskCard({ task, onComplete, onStart, onSkip, onDelete, isUpdating }: any) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: task.id, data: { status: task.status } });
  
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  if (isDragging) {
    return (
      <div ref={setNodeRef} style={style} className="h-32 bg-indigo-50 dark:bg-indigo-900/20 border-2 border-dashed border-indigo-200 dark:border-indigo-800 rounded-xl opacity-50" />
    );
  }

  return (
    <div ref={setNodeRef} style={style} {...attributes}>
      <TaskCardContent task={task} onComplete={onComplete} onStart={onStart} onSkip={onSkip} onDelete={onDelete} isUpdating={isUpdating} dragListeners={listeners} />
    </div>
  );
}

export function TaskCardContent({ task, onComplete, onStart, onSkip, onDelete, isUpdating, dragListeners, isOverlay = false }: any) {
  const [showRating, setShowRating] = useState(false);
  const [rating, setRating] = useState(0);

  const isDone = task.status === 'completed';
  const isSkipped = task.status === 'skipped';
  const isCustom = task.task_type === 'custom';

  const handleSubmitComplete = () => {
    onComplete(rating || undefined);
    setShowRating(false);
    setRating(0);
  };

  const priorityLabel = task.phase === 'learn' ? 'High' : task.phase === 'practice' ? 'Medium' : 'Low';
  const priorityColor = task.phase === 'learn' ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-400' :
                        task.phase === 'practice' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400' :
                        'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400';

  return (
    <motion.div
      layout={!isOverlay}
      initial={!isOverlay ? { opacity: 0, scale: 0.97 } : false}
      animate={!isOverlay ? { opacity: 1, scale: 1 } : false}
      transition={{ duration: 0.25 }}
      style={isOverlay ? { cursor: 'grabbing', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)' } : undefined}
      className={`rounded-xl border p-4 transition-colors relative group ${
        isDone
          ? 'bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-100 dark:border-emerald-900/40'
          : isSkipped
          ? 'bg-gray-50 dark:bg-zinc-800/40 border-gray-100 dark:border-zinc-700 opacity-60'
          : 'bg-white dark:bg-zinc-900 border-gray-100 dark:border-zinc-800'
      }`}
    >
      {/* Header and drag handle */}
      <div className="flex items-start gap-2 mb-2">
        <div {...dragListeners} className="mt-0.5 cursor-grab active:cursor-grabbing text-gray-400 dark:text-zinc-500 hover:text-gray-600 dark:hover:text-zinc-300">
          <GripVertical className="w-4 h-4" />
        </div>
        <div className="min-w-0 flex-1">
          <p className={`text-sm font-semibold leading-snug break-words ${
            isSkipped ? 'line-through text-gray-400 dark:text-zinc-500' : 'text-gray-900 dark:text-zinc-100'
          }`}>
            {task.title}
          </p>
        </div>
        {isCustom && onDelete && !isDone && !isSkipped && (
          <button onClick={onDelete} disabled={isUpdating} className="flex-shrink-0 p-1 text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50">
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Badges row */}
      <div className="flex flex-wrap items-center gap-1.5 mb-3 pl-6">
        {platformBadge(task.platform)}
        <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wide ${priorityColor}`}>
          Priority: {priorityLabel}
        </span>
        {task.estimated_hours && (
          <span className="flex items-center gap-0.5 text-xs text-gray-500 dark:text-zinc-400">
            <Clock className="w-3 h-3" />
            {task.estimated_hours}h
          </span>
        )}
        {task.resource_url && (
          <a href={task.resource_url} target="_blank" rel="noreferrer"
            className="flex items-center gap-0.5 text-xs text-indigo-500 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium transition-colors">
            Open <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>

      {/* Completed info */}
      {isDone && (
        <div className="pl-6 flex items-center gap-2 mb-1">
          {task.feedback_score && (
            <div className="flex gap-0.5">
              {[1,2,3,4,5].map(n => (
                <Star key={n} className={`w-3 h-3 ${n <= (task.feedback_score ?? 0)
                  ? 'fill-amber-400 text-amber-400' : 'text-gray-200 dark:text-zinc-700'}`} />
              ))}
            </div>
          )}
          {task.completed_at && (
            <span className="text-xs text-gray-400 dark:text-zinc-500">
              {new Date(task.completed_at).toLocaleDateString()}
            </span>
          )}
        </div>
      )}

      {/* Actions */}
      {!isDone && !isSkipped && (
        <div className="pl-6 pt-1">
          {!showRating ? (
            <div className="flex flex-wrap gap-2">
              {task.status === 'pending' && (
                <button
                  onClick={onStart}
                  disabled={isUpdating}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 dark:bg-indigo-500/10 dark:text-indigo-400 dark:hover:bg-indigo-500/20 transition-colors disabled:opacity-50"
                >
                  {isUpdating ? <Loader2 className="w-3 h-3 animate-spin" /> : <PlayCircle className="w-3 h-3" />}
                  Start
                </button>
              )}
              {task.status === 'in_progress' && (
                <button
                  onClick={() => setShowRating(true)}
                  disabled={isUpdating}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition-colors disabled:opacity-50"
                >
                  <CheckCircle2 className="w-3 h-3" /> Mark Complete
                </button>
              )}
              <button
                onClick={onSkip}
                disabled={isUpdating}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-gray-500 dark:text-zinc-400 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors disabled:opacity-50"
              >
                <SkipForward className="w-3 h-3" /> Skip
              </button>
            </div>
          ) : (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
              className="bg-gray-50 dark:bg-zinc-800/50 rounded-lg p-3 space-y-2 border border-gray-100 dark:border-zinc-800">
              <p className="text-xs font-medium text-gray-600 dark:text-zinc-300">Rate this task details below (optional)</p>
              <StarRating value={rating} onChange={setRating} />
              <div className="flex gap-2">
                <button onClick={handleSubmitComplete}
                  disabled={isUpdating}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition-colors disabled:opacity-50 flex items-center gap-1">
                  {isUpdating && <Loader2 className="w-3 h-3 animate-spin" />}
                  Submit
                </button>
                <button onClick={() => { setShowRating(false); setRating(0); }}
                  className="px-3 py-1.5 rounded-lg text-xs text-gray-500 dark:text-zinc-400 hover:bg-gray-200 dark:hover:bg-zinc-700 transition-colors">
                  Cancel
                </button>
              </div>
            </motion.div>
          )}
        </div>
      )}
    </motion.div>
  );
}

// ─── Kanban Column & Custom Task Form ────────────────────────────────────────

function KanbanColumn({ id, title, tasks, onStart, onComplete, onSkip, onDelete, isUpdating, onAddClick, showAddForm, children }: any) {
  const { setNodeRef } = useSortable({ id, data: { isColumn: true } });

  return (
    <div className="flex flex-col bg-gray-50/50 dark:bg-zinc-800/30 rounded-2xl border border-gray-100 dark:border-zinc-800 p-4 min-h-[500px]">
      <div className="flex items-center justify-between mb-4 px-1">
        <h3 className="text-sm font-bold text-gray-900 dark:text-zinc-100 uppercase tracking-wide flex items-center gap-2">
          {title}
          <span className="flex items-center justify-center bg-white dark:bg-zinc-700 text-gray-600 dark:text-zinc-300 text-xs font-semibold rounded-full w-5 h-5 border border-gray-200 dark:border-zinc-600 shadow-sm">
            {tasks.length}
          </span>
        </h3>
      </div>
      <div ref={setNodeRef} className="flex-1 space-y-3 pb-4">
        <SortableContext items={tasks.map((t: any) => t.id)} strategy={verticalListSortingStrategy}>
          {tasks.map((task: any) => (
            <SortableTaskCard key={task.id} task={task} onStart={() => onStart(task.id)} onComplete={(score: any) => onComplete(task.id, score)} onSkip={() => onSkip(task.id)} onDelete={() => onDelete(task.id)} isUpdating={isUpdating} />
          ))}
        </SortableContext>
        {children}
        
        {!showAddForm && (
          <button onClick={onAddClick} className="w-full flex items-center justify-center gap-1.5 py-3 border-2 border-dashed border-gray-200 dark:border-zinc-700 rounded-xl text-gray-500 dark:text-zinc-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:border-indigo-200 dark:hover:border-indigo-800 hover:bg-indigo-50/50 dark:hover:bg-indigo-900/10 transition-colors text-sm font-semibold">
            <Plus className="w-4 h-4" /> Add Task
          </button>
        )}
      </div>
    </div>
  );
}

function AddCustomTaskForm({ roadmapId, phase, onCancel, onSuccess }: any) {
  const [title, setTitle] = useState('');
  const [platform, setPlatform] = useState('');
  const [hours, setHours] = useState<number>(1);
  const [url, setUrl] = useState('');

  const mutation = useMutation({
    mutationFn: () => RoadmapService.addCustomTask(roadmapId, {
      title, platform: platform || undefined, estimated_hours: hours, resource_url: url || undefined, phase
    }),
    onSuccess: () => {
      onSuccess();
    }
  });

  return (
    <div className="bg-white dark:bg-zinc-900 border-2 border-indigo-100 dark:border-indigo-900/40 rounded-xl p-4 mt-3 space-y-3 shadow-sm">
      <div className="flex items-center justify-between mb-1">
        <h4 className="text-xs font-bold text-gray-900 dark:text-zinc-100 uppercase tracking-wide">Add Custom Task</h4>
        <button onClick={onCancel} className="text-gray-400 hover:text-gray-600 dark:hover:text-zinc-300">
          <X className="w-4 h-4" />
        </button>
      </div>
      <input autoFocus placeholder="Task title..." value={title} onChange={e=>setTitle(e.target.value)} className="w-full text-sm bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-lg px-3 py-2 text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
      <div className="grid grid-cols-2 gap-2">
        <input placeholder="Platform (e.g. YouTube)" value={platform} onChange={e=>setPlatform(e.target.value)} className="w-full text-xs bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-lg px-3 py-2 text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        <input type="number" min={1} placeholder="Hours" value={hours} onChange={e=>setHours(parseInt(e.target.value)||1)} className="w-full text-xs bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-lg px-3 py-2 text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
      </div>
      <input placeholder="Resource URL (optional)" value={url} onChange={e=>setUrl(e.target.value)} className="w-full text-xs bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-lg px-3 py-2 text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
      <div className="pt-1 flex justify-end">
        <button onClick={() => mutation.mutate()} disabled={!title || mutation.isPending} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg disabled:opacity-50 flex items-center gap-1.5 transition-colors">
          {mutation.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />} Add Task
        </button>
      </div>
    </div>
  );
}

// ─── Roadmap Detail View ──────────────────────────────────────────────────────

function RoadmapDetailView({ roadmapId }: { roadmapId: string }) {
  const qc = useQueryClient();
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['roadmap', roadmapId],
    queryFn: () => RoadmapService.getRoadmap(roadmapId),
  });

  const completeMutation = useMutation({
    mutationFn: ({ taskId, score }: { taskId: string; score?: number }) =>
      RoadmapService.completeTask(taskId, score),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['roadmap', roadmapId] }),
  });

  const skipMutation = useMutation({
    mutationFn: (taskId: string) => RoadmapService.skipTask(taskId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['roadmap', roadmapId] }),
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: 'pending'|'in_progress'|'completed' }) => 
      RoadmapService.updateTaskStatus(taskId, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['roadmap', roadmapId] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (taskId: string) => RoadmapService.deleteTask(taskId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['roadmap', roadmapId] }),
  });

  const [activeTab, setActiveTab] = useState<'pending' | 'in_progress' | 'completed'>('pending');
  const [addFormPhase, setAddFormPhase] = useState<'learn'|'practice'|'apply'|null>(null);
  
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const [activeDragTask, setActiveDragTask] = useState<RoadmapTask | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 p-6 animate-pulse">
          <div className="h-6 w-48 bg-gray-200 dark:bg-zinc-700 rounded mb-3" />
          <div className="h-3 w-full bg-gray-100 dark:bg-zinc-700 rounded-full" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <SkeletonPhaseCol /><SkeletonPhaseCol /><SkeletonPhaseCol />
        </div>
      </div>
    );
  }
  if (isError || !data) return <ErrorDisplay message="Failed to load roadmap" onRetry={() => refetch()} />;

  const rm = data as RoadmapDetail;
  const pct = rm.total_tasks > 0 ? Math.round((rm.completed_tasks / rm.total_tasks) * 100) : 0;

  const tasksByStatus = {
    pending: rm.tasks.filter(t => t.phase === 'learn' && t.status !== 'completed'),
    in_progress: rm.tasks.filter(t => (t.phase === 'practice' || t.phase === 'apply') && t.status !== 'completed'),
    completed: rm.tasks.filter(t => t.status === 'completed'),
  };

  const handleDragStart = (event: any) => {
    const { active } = event;
    setActiveDragTask(rm.tasks.find(t => t.id === active.id) || null);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveDragTask(null);
    const { active, over } = event;
    if (!over) return;
    
    const activeTaskId = active.id as string;
    const overId = over.id as string;
    
    let targetStatus: 'pending' | 'in_progress' | 'completed' | null = null;
    
    if (['pending', 'in_progress', 'completed'].includes(overId)) {
      targetStatus = overId as any;
    } else {
      const overTask = rm.tasks.find(t => t.id === overId);
      if (overTask) targetStatus = overTask.status as any;
    }
    
    const activeTask = rm.tasks.find(t => t.id === activeTaskId);
    if (activeTask && targetStatus && activeTask.status !== targetStatus) {
      updateStatusMutation.mutate({ taskId: activeTaskId, status: targetStatus });
    }
  };

  const startTask = (taskId: string) => updateStatusMutation.mutate({ taskId, status: 'in_progress' });
  const completeTaskStatus = (taskId: string, score?: number) => completeMutation.mutate({ taskId, score });
  const skipTaskAction = (taskId: string) => skipMutation.mutate(taskId);
  const deleteTaskAction = (taskId: string) => deleteMutation.mutate(taskId);

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-xl font-bold text-gray-900 dark:text-zinc-100">{rm.job_role}</h2>
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-zinc-800 text-gray-500 dark:text-zinc-400">
                v{rm.version}
              </span>
            </div>
            <p className="text-sm text-gray-500 dark:text-zinc-400">
              {rm.completed_tasks} of {rm.total_tasks} tasks completed — {pct}%
            </p>
          </div>
          {rm.status === 'completed' && (
            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 text-sm font-semibold">
              <Trophy className="w-4 h-4" /> Completed!
            </span>
          )}
        </div>

        <div className="relative h-3 rounded-full bg-gray-100 dark:bg-zinc-800 overflow-hidden">
          <motion.div
            className="h-3 rounded-full bg-gradient-to-r from-indigo-500 to-blue-500"
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' as const }}
          />
        </div>

        {rm.is_transition && (
          <div className="mt-4 flex items-center gap-2 text-sm text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800/40 rounded-xl px-4 py-2.5">
            <ArrowRight className="w-4 h-4 flex-shrink-0" />
            Career Transition Roadmap — tasks are ordered to bridge your current knowledge gap.
          </div>
        )}
      </div>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
        {/* Mobile: Tab switcher */}
        <div className="flex lg:hidden gap-1 bg-gray-100 dark:bg-zinc-800 p-1 rounded-xl">
          {[
            { key: 'pending', label: 'To Learn' },
            { key: 'in_progress', label: 'Practicing' },
            { key: 'completed', label: 'Completed' }
          ].map(({ key, label }) => (
            <button key={key}
              onClick={() => setActiveTab(key as typeof activeTab)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === key
                  ? 'bg-white dark:bg-zinc-900 text-gray-900 dark:text-zinc-100 shadow-sm'
                  : 'text-gray-500 dark:text-zinc-400'
              }`}
            >
              {label} <span className="text-[10px] bg-gray-200 dark:bg-zinc-800 px-1.5 rounded-full">{tasksByStatus[key as keyof typeof tasksByStatus].length}</span>
            </button>
          ))}
        </div>

        {/* Desktop: 3-column grid */}
        <div className="hidden lg:grid grid-cols-3 gap-5">
           <KanbanColumn id="pending" title="To Learn" tasks={tasksByStatus.pending} 
             onStart={startTask} onComplete={completeTaskStatus} onSkip={skipTaskAction} onDelete={deleteTaskAction} 
             isUpdating={updateStatusMutation.isPending || completeMutation.isPending || deleteMutation.isPending} onAddClick={() => setAddFormPhase('learn')} showAddForm={addFormPhase === 'learn'}>
             {addFormPhase === 'learn' && <AddCustomTaskForm roadmapId={roadmapId} phase="learn" onCancel={() => setAddFormPhase(null)} onSuccess={() => setAddFormPhase(null)} />}
           </KanbanColumn>

           <KanbanColumn id="in_progress" title="Practicing" tasks={tasksByStatus.in_progress} 
             onStart={startTask} onComplete={completeTaskStatus} onSkip={skipTaskAction} onDelete={deleteTaskAction} 
             isUpdating={updateStatusMutation.isPending || completeMutation.isPending || deleteMutation.isPending} onAddClick={() => setAddFormPhase('practice')} showAddForm={addFormPhase === 'practice'}>
             {addFormPhase === 'practice' && <AddCustomTaskForm roadmapId={roadmapId} phase="practice" onCancel={() => setAddFormPhase(null)} onSuccess={() => setAddFormPhase(null)} />}
           </KanbanColumn>

           <KanbanColumn id="completed" title="Completed" tasks={tasksByStatus.completed} 
             onStart={startTask} onComplete={completeTaskStatus} onSkip={skipTaskAction} onDelete={deleteTaskAction} 
             isUpdating={updateStatusMutation.isPending || completeMutation.isPending || deleteMutation.isPending} onAddClick={() => setAddFormPhase('apply')} showAddForm={addFormPhase === 'apply'}>
             {addFormPhase === 'apply' && <AddCustomTaskForm roadmapId={roadmapId} phase="apply" onCancel={() => setAddFormPhase(null)} onSuccess={() => setAddFormPhase(null)} />}
           </KanbanColumn>
        </div>

        {/* Mobile: Single active phase */}
        <div className="lg:hidden space-y-3">
          <AnimatePresence mode="wait">
            <motion.div key={activeTab}
              initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }} className="space-y-3">
               <KanbanColumn id={activeTab} title={
                 activeTab === 'pending' ? 'To Learn' : activeTab === 'in_progress' ? 'Practicing' : 'Completed'
               } tasks={tasksByStatus[activeTab]} 
                 onStart={startTask} onComplete={completeTaskStatus} onSkip={skipTaskAction} onDelete={deleteTaskAction} 
                 isUpdating={updateStatusMutation.isPending || completeMutation.isPending || deleteMutation.isPending} 
                 onAddClick={() => setAddFormPhase(activeTab === 'pending' ? 'learn' : activeTab === 'in_progress' ? 'practice' : 'apply')} 
                 showAddForm={addFormPhase !== null}
               >
                 {addFormPhase && <AddCustomTaskForm roadmapId={roadmapId} phase={addFormPhase} onCancel={() => setAddFormPhase(null)} onSuccess={() => setAddFormPhase(null)} />}
               </KanbanColumn>
            </motion.div>
          </AnimatePresence>
        </div>

        <DragOverlay dropAnimation={defaultDropAnimationSideEffects({ styles: { active: { opacity: '0.5' } } }) as any}>
          {activeDragTask ? <TaskCardContent task={activeDragTask} isOverlay={true} /> : null}
        </DragOverlay>
      </DndContext>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const RoadmapPage = () => {
  const qc = useQueryClient();
  const [selectedRoadmapId, setSelectedRoadmapId] = useState<string | null>(null);
  const [selectedRole, setSelectedRole] = useState('');
  const roadmapRef = useRef<HTMLDivElement>(null);

  // Fetch preferences for target_roles dropdown
  const { data: prefs } = useQuery({
    queryKey: ['preferences'],
    queryFn: PreferencesService.getPreferences,
  });

  // Fetch roadmap list
  const { data: roadmaps, isLoading: listLoading } = useQuery({
    queryKey: ['roadmaps'],
    queryFn: RoadmapService.listRoadmaps,
    onSuccess: (data: Roadmap[]) => {
      // Auto-select the first active roadmap
      if (!selectedRoadmapId && data.length > 0) {
        const active = data.find(r => r.status === 'active') ?? data[0];
        setSelectedRoadmapId(active.id);
        setSelectedRole(active.job_role);
      }
    },
  } as any);

  const generateMutation = useMutation({
    mutationFn: (role: string) => RoadmapService.generateRoadmap(role),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['roadmaps'] });
      setSelectedRoadmapId(data.id);
      setTimeout(() => roadmapRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    },
  });

  const deleteRoadmapMutation = useMutation({
    mutationFn: (id: string) => RoadmapService.deleteRoadmap(id),
    onSuccess: (_, deletedId) => {
      qc.invalidateQueries({ queryKey: ['roadmaps'] });
      if (selectedRoadmapId === deletedId) {
        setSelectedRoadmapId(null);
      }
    },
  });

  // Fetch existing gaps to get the full list of roles with computed analysis
  const { data: skillGaps } = useQuery({
    queryKey: ['skill-gaps'],
    queryFn: () => import('../services/api').then(m => m.SkillsService.getSkillGaps()),
  });

  // Build the dropdown list: preference roles first (starred), then all gap-computed roles
  const prefRoles: string[] = prefs?.target_roles ?? [];
  const gapRoles: string[] = (skillGaps ?? []).map((g: any) => g.job_role);
  const allDropdownRoles = [
    ...prefRoles,
    ...gapRoles.filter(r => !prefRoles.includes(r)),
  ];

  const existingForRole = (roadmaps as Roadmap[] | undefined)?.find(
    r => r.job_role === selectedRole && r.status === 'active'
  );

  return (
    <PageTransition className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-zinc-100 flex items-center gap-3">
          <span className="p-2 bg-indigo-100 dark:bg-indigo-900/40 rounded-xl">
            <Map className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
          </span>
          Learning Roadmap
        </h1>
        <p className="text-gray-500 dark:text-zinc-400 mt-1 ml-14">
          AI-generated personalized paths to your career goals
        </p>
      </div>

      {/* Section 1 — Generate Panel */}
      <div className="bg-gradient-to-br from-indigo-50 to-blue-50 dark:from-indigo-950/30 dark:to-blue-950/30 rounded-2xl border border-indigo-100 dark:border-indigo-900/50 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-4 h-4 text-indigo-500" />
          <h2 className="text-sm font-semibold text-indigo-700 dark:text-indigo-400 uppercase tracking-wider">
            Generate Roadmap
          </h2>
        </div>

        <div className="flex flex-wrap gap-3 items-end">
          {/* Role dropdown */}
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray-600 dark:text-zinc-400 mb-1.5">
              Target Role
            </label>
            <div className="relative">
              <select
                value={selectedRole}
                onChange={e => setSelectedRole(e.target.value)}
                className="w-full appearance-none bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 pr-9 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer"
              >
                <option value="">— Select a role —</option>
                {prefRoles.length > 0 && (
                  <optgroup label="⭐ Your Target Roles">
                    {prefRoles.map((r: string) => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </optgroup>
                )}
                {gapRoles.filter(r => !prefRoles.includes(r)).length > 0 && (
                  <optgroup label="All Available Roles">
                    {gapRoles.filter(r => !prefRoles.includes(r)).map((r: string) => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </optgroup>
                )}
              </select>
              <ChevronDown className="w-4 h-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          {/* Warning + Generate button */}
          <div className="space-y-2">
            {existingForRole && (
              <div className="flex items-center gap-1.5 text-xs text-amber-600 dark:text-amber-400">
                <AlertTriangle className="w-3.5 h-3.5" />
                This will archive your current roadmap
              </div>
            )}
            <button
              disabled={!selectedRole || generateMutation.isPending}
              onClick={() => selectedRole && generateMutation.mutate(selectedRole)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {generateMutation.isPending
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating…</>
                : existingForRole
                ? <><RefreshCw className="w-4 h-4" /> Regenerate</>
                : <><Zap className="w-4 h-4" /> Generate Roadmap</>
              }
            </button>
          </div>
        </div>

        {generateMutation.isError && (
          <p className="mt-3 text-sm text-red-600 dark:text-red-400">
            Failed to generate roadmap. Make sure your skill gap analysis has been computed.
          </p>
        )}
      </div>

      {/* Sections 2+3 — Sidebar List + Active Roadmap */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6" ref={roadmapRef}>
        {/* Section 2: Roadmap List */}
        <div className="lg:col-span-1">
          <h2 className="text-xs font-semibold text-gray-500 dark:text-zinc-400 uppercase tracking-wider mb-3">
            Your Roadmaps
          </h2>
          {listLoading ? (
            <SkeletonRoadmapList />
          ) : !roadmaps || (roadmaps as Roadmap[]).length === 0 ? (
            <div className="text-sm text-gray-500 dark:text-zinc-400 text-center py-8">
              No roadmaps yet. Generate one above!
            </div>
          ) : (
            <div className="space-y-2">
              {(roadmaps as Roadmap[]).map(rm => (
                <div key={rm.id} className="relative group">
                  <button
                    onClick={() => setSelectedRoadmapId(rm.id)}
                    className={`w-full text-left rounded-xl border px-4 py-3 transition-all ${
                      selectedRoadmapId === rm.id
                        ? 'bg-indigo-50 dark:bg-indigo-950/30 border-indigo-200 dark:border-indigo-800'
                        : 'bg-white dark:bg-zinc-900 border-gray-100 dark:border-zinc-800 hover:border-indigo-200 dark:hover:border-indigo-800'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-semibold text-gray-900 dark:text-zinc-100 truncate mr-2">
                        {rm.job_role}
                      </span>
                      <span className={`flex-shrink-0 px-1.5 py-0.5 rounded-full text-[10px] font-semibold ${STATUS_STYLES[rm.status] ?? STATUS_STYLES.archived}`}>
                        {rm.status}
                      </span>
                    </div>
                    {/* Mini progress bar */}
                    <div className="h-1.5 rounded-full bg-gray-100 dark:bg-zinc-800 pr-6">
                      <div
                        className="h-1.5 rounded-full bg-indigo-500 transition-all"
                        style={{ width: `${rm.completion_percentage ?? 0}%` }}
                      />
                    </div>
                    <p className="text-[10px] text-gray-400 dark:text-zinc-500 mt-1">
                      {Math.round(rm.completion_percentage ?? 0)}% complete
                    </p>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteRoadmapMutation.mutate(rm.id);
                    }}
                    disabled={deleteRoadmapMutation.isPending && deleteRoadmapMutation.variables === rm.id}
                    className="absolute bottom-3 right-3 p-1.5 bg-red-50 hover:bg-red-100 dark:bg-red-900/20 dark:hover:bg-red-900/40 text-red-600 dark:text-red-400 rounded-lg opacity-0 group-hover:opacity-100 transition-all focus:opacity-100 disabled:opacity-50"
                  >
                    {deleteRoadmapMutation.isPending && deleteRoadmapMutation.variables === rm.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Trash2 className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Section 3+4: Roadmap Detail */}
        <div className="lg:col-span-3">
          {selectedRoadmapId ? (
            <RoadmapDetailView roadmapId={selectedRoadmapId} />
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400 dark:text-zinc-500">
              <Map className="w-12 h-12 mb-3 opacity-30" />
              <p className="text-sm">Select a roadmap or generate a new one</p>
            </div>
          )}
        </div>
      </div>
    </PageTransition>
  );
};

export default RoadmapPage;
