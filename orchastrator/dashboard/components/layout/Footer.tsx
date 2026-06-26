export function Footer(): React.JSX.Element {
  return (
    <footer className="flex items-center justify-between border-t border-zinc-800/60 bg-[#0a0e1a] px-4 py-2 font-mono">
      <span className="text-[9px] tracking-widest text-zinc-600 uppercase">VentureOS &copy; {new Date().getFullYear()}</span>
      <span className="text-[9px] tracking-widest text-zinc-600 uppercase">V2.0.4-STABLE</span>
    </footer>
  );
}
