import { CreateTaskRequest } from '@/types/task';

interface TaskFormProps {
  onSubmit: (data: CreateTaskRequest) => Promise<void>;
  loading?: boolean;
}

export function TaskForm({ onSubmit, loading }: TaskFormProps): JSX.Element;
