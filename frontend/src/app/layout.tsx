import type { Metadata } from "next";
import { Nav } from "@/components/Nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Graph-Driven Exam Gen",
  description: "Plataforma GraphRAG para geracao de itens com ancoragem na Matriz de Referencia do ENEM",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <Nav />
        <main>{children}</main>
      </body>
    </html>
  );
}
