import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "KapexAI Scenario Workbench",
  description: "Interactive financial scenario analysis",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
