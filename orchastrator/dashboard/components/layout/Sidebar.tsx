'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const links = [
  { name: 'Home', href: '/' },
  { name: 'Task', href: '/task' },
  { name: 'Agents', href: '/agents' }, 
  { name: 'Memory', href: '/memory' },
  { name: 'Logs', href: '/logs' },
  {name: 'Analytics', href: '/analytics'},
  { name: 'Settings', href: '/settings' },
];  

export function Sidebar(): JSX.Element {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-gray-800 text-white h-screen">
      <nav className="flex flex-col space-y-2 p-4">
        {links.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`rounded-md px-3 py-2 text-sm font-medium ${
              pathname === item.href
                ? "bg-zinc-100 text-zinc-900"
                : "text-zinc-600 hover:bg-zinc-50"
            }`}
          >
            {item.name}
          </Link>
        ))}
      </nav>
    </aside>
  )
}
