import { CreateAgentRequest } from '@/types/agent';

interface CreateAgentFormProps {
  onSubmit: (data: CreateAgentRequest) => Promise<void>;
  loading?: boolean;
}

export function CreateAgentForm({ onSubmit, loading }: CreateAgentFormProps): JSX.Element;
