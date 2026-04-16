import { Task } from '@/types/task';

interface TaskListProps {
  tasks: Task[];
  loading?: boolean;
}

export function TaskList({ tasks, loading }: TaskListProps): JSX.Element;
