import { Header } from "@/components/layout/Header";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-zinc-950">
      <Header />
      <div className="flex-1">{children}</div>
    </div>
  );
}
