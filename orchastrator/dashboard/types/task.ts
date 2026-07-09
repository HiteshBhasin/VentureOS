export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  progress: number;        // 0-100
  tags: string[];
  agent_id: string | null;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  result?: { project_path?: string | null; report?: string; [key: string]: unknown } | null;
  error?: string | null;
}

export interface ActiveGoal {
  id: string;
  title: string;
  status: 'executing' | 'paused' | 'completed' | 'failed';
  completion: number;      // 0-100
  elapsed_seconds: number;
  pid: number;
  memory_used_gb: number;
  memory_total_gb: number;
}

export interface SystemStatus {
  active_agents: number;
  tokens_per_sec: number;
  cost_estimate: number;
  memory_used_gb: number;
  memory_total_gb: number;
  uptime_seconds: number;
  latency_ms: number;
}

export interface StreamLog {
  time: string;
  message: string;
}

export interface CreateTaskRequest {
  title: string;
  description: string;
  agent_id?: string;
  priority: Task['priority'];
}

