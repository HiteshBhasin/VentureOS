import { Agent } from '@/types/agent';

interface UseAgentsReturn {
  agents: Agent[];
  loading: boolean;
  error: string | null;
}

export function useAgents(): UseAgentsReturn;
