export default function SupportPage() {
  return (
    <div className="flex flex-col h-full bg-[#080c18] text-zinc-300 font-mono p-5 gap-5 max-w-lg">
      <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-400 uppercase">Support</span>

      <div className="rounded border border-zinc-800 bg-zinc-900/50 p-4 flex flex-col gap-3">
        <p className="text-[11px] text-zinc-500 leading-relaxed">
          Having trouble with VentureOS? Reach out and we&apos;ll help you get unblocked.
        </p>
        <div className="flex flex-col gap-1.5">
          <span className="text-[9px] tracking-widest text-zinc-600 uppercase">Email</span>
          <span className="text-[11px] text-cyan-400">support@ventureos.ai</span>
        </div>
        <div className="flex flex-col gap-1.5">
          <span className="text-[9px] tracking-widest text-zinc-600 uppercase">Docs</span>
          <span className="text-[11px] text-zinc-300">See the Documentation page in the sidebar for setup and usage guides.</span>
        </div>
      </div>
    </div>
  );
}
