'use client';

import { createContext, useContext, useState, ReactNode } from 'react';
import { Agent } from '@/types/agent';
import { useAgents } from '@/hooks/useAgents';

interface DashboardContextType {
  agents: Agent[];
  selectedAgent: Agent | null;
  setSelectedAgent: (agent: Agent | null) => void;
}

export const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

interface DashboardProviderProps {
  children: ReactNode;
}

export function DashboardProvider({ children }: DashboardProviderProps): React.JSX.Element {
  const { agents } = useAgents();
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  return (
    <DashboardContext.Provider value={{ agents, selectedAgent, setSelectedAgent }}>
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard(): DashboardContextType {
  const ctx = useContext(DashboardContext);
  if (!ctx) throw new Error('useDashboard must be used within DashboardProvider');
  return ctx;
}
