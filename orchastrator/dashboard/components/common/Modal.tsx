interface ModalProps {
  isOpen: boolean;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}

export function Modal({ isOpen, title, onClose, children }: ModalProps): React.JSX.Element | null {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 font-mono">
      <div className="absolute inset-0" onClick={onClose} />
      <div className="relative w-full max-w-md rounded border border-zinc-800 bg-[#0a0e1a] shadow-lg shadow-cyan-900/20">
        <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
          <span className="text-[11px] font-bold tracking-widest text-zinc-200 uppercase">{title}</span>
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            className="text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}
