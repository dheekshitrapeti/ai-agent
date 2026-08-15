import Link from "next/link";
import { Activity, Home, Link2, Sparkles } from "lucide-react";

const links = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/integrations", label: "Integrations", icon: Link2 },
  { href: "/activity", label: "Activity", icon: Activity },
];

export function Sidebar() {
  return (
    <aside className="w-full border-b border-slate-200 bg-white md:min-h-screen md:w-64 md:border-b-0 md:border-r">
      <div className="flex h-full flex-col">
        <div className="flex items-center gap-3 border-b border-slate-100 px-5 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-white">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <p className="font-semibold">AI Workspace</p>
            <p className="text-xs text-slate-500">Assistant</p>
          </div>
        </div>
        <nav className="flex gap-1 overflow-x-auto p-3 md:block">
          {links.map(({ href, label, icon: Icon }) => (
            <Link key={href} href={href} className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-600 hover:bg-slate-100">
              <Icon className="h-4 w-4" />{label}
            </Link>
          ))}
        </nav>
      </div>
    </aside>
  );
}
