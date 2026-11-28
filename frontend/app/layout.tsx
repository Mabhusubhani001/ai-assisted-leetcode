import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { Suspense } from "react";
import Link from "next/link";
import { Terminal } from "lucide-react";
import { HeaderAuth } from "@/components/HeaderAuth";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "AI-Assisted DSA Assessment Platform",
    template: "%s | AI DSA Platform",
  },
  description:
    "A disciplined algorithmic practice environment pairing real-time complexity analysis with sandboxed execution.",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_APP_URL ||
      "http://production-dsa-alb-209746966.ap-southeast-2.elb.amazonaws.com"
  ),
  openGraph: {
    title: "AI-Assisted DSA Assessment Platform",
    description:
      "Master algorithms with real-time AI coaching, token guardrails, and multi-language evaluation.",
    siteName: "AI DSA Platform",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "AI-Assisted DSA Assessment Platform",
    description: "Master algorithms with real-time AI coaching.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en" className="dark" style={{ colorScheme: "dark" }}>
        <body className="bg-black text-zinc-100 min-h-screen flex flex-col font-sans antialiased selection:bg-zinc-800 selection:text-white">
          {/* Minimal Global Header */}
        <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 h-12 flex items-center justify-between text-xs">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="flex items-center gap-2 font-semibold tracking-tight text-white hover:text-zinc-200 transition-colors focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none rounded px-1 py-0.5"
              >
                <div className="w-5 h-5 rounded bg-zinc-900 border border-zinc-700 flex items-center justify-center text-zinc-300">
                  <Terminal className="w-3.5 h-3.5" aria-hidden="true" />
                </div>
                <span>Algorithmic Assessment</span>
              </Link>
              <span className="text-zinc-700" aria-hidden="true">/</span>
              <Link
                href="/"
                className="text-zinc-400 hover:text-zinc-200 transition-colors focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none rounded px-1 py-0.5"
              >
                Catalog
              </Link>
            </div>

            <div className="flex items-center gap-3">
              <Suspense fallback={<div className="w-16 h-6 animate-pulse bg-zinc-900 rounded" />}>
                <HeaderAuth />
              </Suspense>
            </div>
          </div>
        </header>

          {/* Workspace Canvas */}
          <main className="flex-1 flex flex-col min-h-0">
            {children}
          </main>
        </body>
      </html>
    </ClerkProvider>
  );
}
