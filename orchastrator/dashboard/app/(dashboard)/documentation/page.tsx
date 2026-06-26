const SECTIONS = [
  {
    title: 'Getting Started',
    body: 'Enter an objective on the Dashboard and press Execute. The Meta-Agent decomposes your goal into a task graph, spawns specialist agents, and runs them through the agent engine.',
  },
  {
    title: 'Tasks',
    body: 'Track decomposition progress on the Tasks page. Each task moves through pending -> running -> completed (or failed) as the background worker claims and executes it.',
  },
  {
    title: 'Agents',
    body: 'View active agents on the Agents page. Click an agent card to see its current activity, model, and cost estimate. Use "+ New Agent" to manually spawn a specialist.',
  },
  {
    title: 'Memory',
    body: 'The Memory page lists everything the system has persisted across runs — short-term, long-term, episodic, semantic, and working memory entries.',
  },
  {
    title: 'Logs',
    body: 'The Logs page streams real-time system events over Server-Sent Events as agents are spawned, execute tasks, and report results.',
  },
];

export default function DocumentationPage() {
  return (
    <div className="flex flex-col h-full bg-[#080c18] text-zinc-300 font-mono p-5 gap-5 max-w-2xl overflow-y-auto">
      <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-400 uppercase">Documentation</span>
      {SECTIONS.map((section) => (
        <div key={section.title} className="rounded border border-zinc-800 bg-zinc-900/50 p-4">
          <h2 className="text-[11px] font-bold tracking-widest text-cyan-400 uppercase mb-1.5">{section.title}</h2>
          <p className="text-[11px] text-zinc-500 leading-relaxed">{section.body}</p>
        </div>
      ))}
    </div>
  );
}
