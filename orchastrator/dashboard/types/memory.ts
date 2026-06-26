export interface MemoryEntry {
  id: string;
  user_id: string;
  agent_id: string | null;
  key: string;
  value: unknown;
  memory_type: 'short_term' | 'long_term' | 'episodic' | 'semantic' | 'working';
  created_at: string;
  updated_at: string;
}
