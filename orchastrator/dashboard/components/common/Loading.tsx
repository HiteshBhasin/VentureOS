export function Loading(): React.JSX.Element {
  return (
    <div className="flex h-full items-center justify-center gap-2 bg-[#080c18] font-mono">
      <svg className="h-4 w-4 animate-spin text-cyan-400 [animation-duration:1.5s]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
      <span className="text-[11px] tracking-widest text-zinc-600 uppercase">Loading...</span>
    </div>
  );
}
