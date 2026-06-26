interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

const VARIANT_CLASSES: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary: 'border-cyan-500/40 bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20 hover:border-cyan-400',
  secondary: 'border-zinc-700 bg-zinc-900/50 text-zinc-300 hover:bg-zinc-800',
  danger: 'border-red-700/50 bg-red-900/20 text-red-400 hover:bg-red-900/40',
};

const SIZE_CLASSES: Record<NonNullable<ButtonProps['size']>, string> = {
  sm: 'px-2.5 py-1 text-[9px]',
  md: 'px-4 py-2 text-[10px]',
  lg: 'px-5 py-2.5 text-[11px]',
};

export function Button({ variant = 'primary', size = 'md', children, className = '', ...props }: ButtonProps): React.JSX.Element {
  return (
    <button
      {...props}
      className={`rounded border font-bold tracking-widest uppercase transition-colors disabled:opacity-30 disabled:cursor-not-allowed font-mono ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`}
    >
      {children}
    </button>
  );
}
