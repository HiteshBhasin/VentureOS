import { ReactNode } from 'react';
import { Agent } from '@/types/agent';

interface DashboardContextType {
  agents: Agent[];
  selectedAgent: Agent | null;
  setSelectedAgent: (agent: Agent | null) => void;
}

export const DashboardContext: React.Context<DashboardContextType | undefined>;

interface DashboardProviderProps {
  children: ReactNode;
}

export function DashboardProvider({ children }: DashboardProviderProps): JSX.Element;
