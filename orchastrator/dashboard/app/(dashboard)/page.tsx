import Link from "next/link";

const quickLinks = [
  {
    title: "Agents",
    description: "Manage and monitor all active agents.",
    href: "/agents",
  },
  {
    title: "Tasks",
    description: "Review queued, running, and completed tasks.",
    href: "/tasks",
  },
  {
    title: "Sample Detail",
    description: "Open a dynamic route powered by [id].",
    href: "/demo-id",
  },
];

export default function DashboardPage() {
  return (
    <main className="flex-1 bg-zinc-50 p-6 md:p-10">
      <section className="mx-auto max-w-5xl space-y-8">
        <header className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-zinc-900">Dashboard</h1>
          <p className="text-zinc-600">
            Welcome to VentureOS. Choose a section to continue.
          </p>
        </header>

        <div className="grid gap-4 md:grid-cols-3">
          {quickLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm transition hover:border-zinc-300 hover:shadow"
            >
              <h2 className="text-lg font-semibold text-zinc-900">{link.title}</h2>
              <p className="mt-2 text-sm text-zinc-600">{link.description}</p>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
