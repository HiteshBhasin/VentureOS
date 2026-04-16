export interface Agent {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'error';
  type: 'coding' | 'research' | 'review' | 'runtime';
  description: string;
  createdAt: string;
  updatedAt: string;
  lastRun?: string;
}

export interface CreateAgentRequest {
  name: string;
  type: Agent['type'];
  description: string;
}
