"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Mic, List, Search, Music } from "lucide-react";
import { clsx } from "clsx";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
}

interface NavSection {
  title?: string;
  items: NavItem[];
}

const NAV: NavSection[] = [
  {
    items: [
      { label: "Fazer Transcrição", href: "/transcricao", icon: Mic },
    ],
  },
  {
    title: "Transcrições",
    items: [
      { label: "Listagem", href: "/listagem", icon: List },
      { label: "Busca Avançada", href: "/busca", icon: Search },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col bg-gradient-sidebar h-screen overflow-y-auto">
      <Brand />
      <nav className="flex-1 px-3 py-2">
        {NAV.map((section, i) => (
          <NavSection key={i} section={section} pathname={pathname} />
        ))}
      </nav>
      <SidebarFooter />
    </aside>
  );
}

function Brand() {
  return (
    <div className="px-5 py-5 border-b border-white/10">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-primary flex items-center justify-center shadow-lg shadow-primary/40">
          <Music size={18} className="text-white" />
        </div>
        <div>
          <p className="text-white font-bold text-base leading-none">Transcriber</p>
          <p className="text-white/40 text-xs mt-0.5">faster-whisper + AI</p>
        </div>
      </div>
    </div>
  );
}

function NavSection({ section, pathname }: { section: NavSection; pathname: string }) {
  return (
    <div className="mt-2">
      {section.title && (
        <p className="px-3 py-2 text-white/35 text-[10px] font-semibold uppercase tracking-widest">
          {section.title}
        </p>
      )}
      <ul className="space-y-0.5">
        {section.items.map((item) => (
          <NavLink key={item.href} item={item} active={pathname === item.href} />
        ))}
      </ul>
    </div>
  );
}

function NavLink({ item, active }: { item: NavItem; active: boolean }) {
  const Icon = item.icon;
  return (
    <li>
      <Link
        href={item.href}
        className={clsx(
          "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150",
          active
            ? "bg-gradient-primary text-white shadow-lg shadow-primary/30"
            : "text-white/60 hover:text-white hover:bg-white/8"
        )}
      >
        <Icon size={16} className={active ? "text-white" : "text-white/50"} />
        {item.label}
      </Link>
    </li>
  );
}

function SidebarFooter() {
  return (
    <div className="px-5 py-4 border-t border-white/10">
      <p className="text-white/25 text-xs">© 2026 Transcriber</p>
    </div>
  );
}
