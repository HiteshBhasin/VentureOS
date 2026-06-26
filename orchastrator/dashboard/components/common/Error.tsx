interface ErrorProps {
  message: string;
  onRetry?: () => void;
}

export function Error({ message, onRetry }: ErrorProps): React.JSX.Element {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 bg-[#080c18] font-mono">
      <span className="text-[11px] tracking-widest text-red-400 uppercase">Error: {message}</span>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="rounded border border-zinc-700 bg-zinc-900/50 px-4 py-2 text-[10px] font-bold tracking-widest text-zinc-300 uppercase hover:bg-zinc-800 transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  );
}
