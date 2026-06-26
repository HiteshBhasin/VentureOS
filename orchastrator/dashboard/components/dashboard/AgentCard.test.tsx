import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AgentCard } from './AgentCard';
import { Agent } from '@/types/agent';

const agent: Agent = {
  id: 'agent-12345678',
  name: 'STRATEGY_LEAD',
  type: 'research',
  status: 'active',
  activity: 'THINKING',
  progress: 42,
  description: 'Doing strategy things',
  tokens_per_sec: 100,
  cost_estimate: 0.5,
  model: 'gpt-4o',
};

describe('AgentCard', () => {
  it('renders agent name, status, and progress', () => {
    render(<AgentCard agent={agent} />);
    expect(screen.getByText('STRATEGY_LEAD')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
    expect(screen.getByText('42%')).toBeInTheDocument();
  });

  it('calls onClick with the agent when clicked', () => {
    const onClick = vi.fn();
    render(<AgentCard agent={agent} onClick={onClick} />);
    screen.getByText('STRATEGY_LEAD').click();
    expect(onClick).toHaveBeenCalledWith(agent);
  });
});
