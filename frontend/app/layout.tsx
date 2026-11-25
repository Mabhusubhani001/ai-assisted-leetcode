import type { Metadata } from "next";
import { ClerkProvider, SignInButton, SignUpButton, Show, UserButton } from "@clerk/nextjs";
import { Suspense } from "react";
import Link from "next/link";
import { Terminal } from "lucide-react";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI-Assisted DSA Assessment Platform",
  description: "A disciplined algorithmic practice environment pairing real-time complexity analysis with sandboxed execution.",
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
                <Show when="signed-out">
                  <SignInButton mode="modal">
                    <button
                      type="button"
                      className="px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white transition-colors focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none rounded"
                    >
                      Sign In
                    </button>
                  </SignInButton>
                  <SignUpButton mode="modal">
                    <button
                      type="button"
                      className="px-3 py-1 text-xs font-medium bg-zinc-100 text-zinc-950 hover:bg-white transition-colors rounded shadow-sm focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none"
                    >
                      Register
                    </button>
                  </SignUpButton>
                </Show>

                <Show when="signed-in">
                  <UserButton
                    appearance={{
                      elements: {
                        avatarBox: "w-7 h-7 rounded-full border border-zinc-800",
                      },
                    }}
                  />
                </Show>
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
