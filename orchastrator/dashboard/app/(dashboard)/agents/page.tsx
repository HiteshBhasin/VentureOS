'use client';

import { useState } from 'react';
import { DashboardProvider, useDashboard } from '@/contexts/DashboardContext';
import { AgentCard } from '@/components/dashboard/AgentCard';
import { StatusWidget } from '@/components/dashboard/StatusWidget';
import { Modal } from '@/components/common/Modal';
import { CreateAgentForm } from '@/components/forms/CreateAgentForm';
import { Loading } from '@/components/common/Loading';
import { Error as ErrorView } from '@/components/common/Error';
import { useAgents } from '@/hooks/useAgents';
import { createAgent } from '@/lib/api';
import { CreateAgentRequest } from '@/types/agent';

function AgentsGrid() {
  const { agents, selectedAgent, setSelectedAgent } = useDashboard();
  const { loading, error, refetch } = useAgents();
  const [showCreate, setShowCreate] = useState(false);

  const handleCreate = async (data: CreateAgentRequest) => {
    await createAgent(data);
    setShowCreate(false);
    refetch();
  };

  if (loading && agents.length === 0) return <Loading />;
  if (error) return <ErrorView message={error} onRetry={refetch} />;

  return (
    <div className="flex flex-col h-full bg-[#080c18] text-zinc-300 font-mono p-5 gap-5">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-400 uppercase">Active_Agents</span>
        <button
          type="button"
          onClick={() => setShowCreate(true)}
          className="rounded border border-violet-500/40 bg-violet-500/10 text-violet-400 text-[10px] font-bold tracking-widest px-3 py-1.5 uppercase hover:bg-violet-500/20 hover:border-violet-400 transition-colors"
        >
          + New Agent
        </button>
      </div>

      {agents.length === 0 ? (
        <div className="flex flex-1 items-center justify-center">
          <span className="text-[11px] tracking-widest text-zinc-600 uppercase">No agents yet</span>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-3">
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} onClick={setSelectedAgent} />
          ))}
        </div>
      )}

      <Modal isOpen={selectedAgent !== null} title={selectedAgent?.name ?? ''} onClose={() => setSelectedAgent(null)}>
        {selectedAgent && (
          <div className="flex flex-col gap-3">
            <StatusWidget agent={selectedAgent} />
            <div className="text-[10px] text-zinc-500 leading-relaxed">{selectedAgent.description}</div>
            <div className="grid grid-cols-2 gap-2 text-[10px] text-zinc-500">
              <span>Model: <span className="text-zinc-300">{selectedAgent.model}</span></span>
              <span>Type: <span className="text-zinc-300">{selectedAgent.type}</span></span>
              <span>Tokens/sec: <span className="text-zinc-300">{selectedAgent.tokens_per_sec}</span></span>
              <span>Cost (est): <span className="text-zinc-300">${selectedAgent.cost_estimate.toFixed(2)}</span></span>
            </div>
          </div>
        )}
      </Modal>

      <Modal isOpen={showCreate} title="New Agent" onClose={() => setShowCreate(false)}>
        <CreateAgentForm onSubmit={handleCreate} />
      </Modal>
    </div>
  );
}

export default function AgentsPage() {
  return (
    <DashboardProvider>
      <AgentsGrid />
    </DashboardProvider>
  );
}
