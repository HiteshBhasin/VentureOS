export interface Agent {
  id: string;
  name: string;
  type: 'coding' | 'research' | 'review' | 'runtime';
  status: 'active' | 'idle' | 'error' | 'stopped';
  activity: string;        // e.g. "THINKING", "SCRAPING", "IDLE"
  progress: number;        // 0-100
  description: string;     // current activity description / thought
  tokens_per_sec: number;
  cost_estimate: number;
  model: string;
  created_at?: string;
  updated_at?: string;
}

export interface CreateAgentRequest {
  name: string;
  type: Agent['type'];
  description: string;
}

