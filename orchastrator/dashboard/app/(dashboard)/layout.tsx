import Link from "next/link";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-zinc-100">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/" className="text-lg font-semibold text-zinc-900">
            VentureOS
          </Link>
          <nav className="flex items-center gap-5 text-sm font-medium text-zinc-700">
            <Link href="/">Overview</Link>
            <Link href="/agents">Agents</Link>
            <Link href="/tasks">Tasks</Link>
          </nav>
        </div>
      </header>
      <div className="mx-auto w-full max-w-6xl flex-1">{children}</div>
    </div>
  );
}
