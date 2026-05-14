import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import DashboardPage from "./(dashboard)/page";

export default function Home() {
  return (
    <div className="flex h-screen bg-[#080c18] overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto">
          <DashboardPage />
        </main>
      </div>
    </div>
  );
}

