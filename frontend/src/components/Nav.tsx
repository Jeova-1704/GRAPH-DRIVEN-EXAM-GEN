"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/geracao", label: "Geracao" },
  { href: "/avaliacao", label: "Avaliacao" },
  { href: "/grafo", label: "Grafo" },
  { href: "/obsidian", label: "Export Obsidian" },
  { href: "/configuracao", label: "Configuracao" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <nav
      style={{
        display: "flex",
        gap: 4,
        padding: "12px 24px",
        background: "#1a1a1a",
        flexWrap: "wrap",
      }}
    >
      <strong style={{ color: "#fff", marginRight: 24 }}>Graph-Driven Exam Gen</strong>
      {LINKS.map((link) => {
        const active = pathname === link.href;
        return (
          <Link
            key={link.href}
            href={link.href}
            style={{
              color: active ? "#fff" : "#aaa",
              textDecoration: "none",
              padding: "4px 10px",
              borderRadius: 6,
              background: active ? "#333" : "transparent",
              fontSize: 14,
            }}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
