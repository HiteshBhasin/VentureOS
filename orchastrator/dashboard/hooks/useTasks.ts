import { Task } from '@/types/task';

interface UseTasksReturn {
  tasks: Task[];
  loading: boolean;
  error: string | null;
}

export function useTasks(agentId?: string): UseTasksReturn;
