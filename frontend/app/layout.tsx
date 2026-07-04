import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dividend Bot B3",
  description: "Scanner fundamentalista da B3",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-br">
      <body className="bg-zinc-950 text-zinc-100 antialiased">{children}</body>
    </html>
  );
}
