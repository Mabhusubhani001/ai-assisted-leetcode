import type { Metadata } from "next";
import { ClerkProvider, SignInButton, SignUpButton, SignedIn, SignedOut, UserButton } from "@clerk/nextjs";
import Link from "next/link";
import { Code2, Sparkles, Terminal } from "lucide-react";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI-Assisted DSA Assessment Platform",
  description: "Master Data Structures & Algorithms through guided AI mentoring and strict complexity guardrails.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en" className="dark">
        <body className="bg-zinc-950 text-zinc-100 min-h-screen flex flex-col font-sans antialiased">
          {/* Universal Header */}
          <header className="border-b border-zinc-800 bg-zinc-900/80 backdrop-blur sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
              <Link href="/" className="flex items-center gap-2 font-bold tracking-tight text-white hover:opacity-90">
                <div className="bg-emerald-500/10 border border-emerald-500/30 p-1.5 rounded-lg text-emerald-400">
                  <Code2 className="w-5 h-5" />
                </div>
                <span>DSA Coach <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">AI</span></span>
              </Link>

              <div className="flex items-center gap-4 text-sm">
                <Link href="/" className="text-zinc-400 hover:text-zinc-100 transition-colors">
                  Problem Catalog
                </Link>

                <SignedOut>
                  <SignInButton mode="modal">
                    <button className="px-3 py-1.5 text-xs font-medium text-zinc-300 hover:text-white transition-colors">
                      Sign In
                    </button>
                  </SignInButton>
                  <SignUpButton mode="modal">
                    <button className="px-3 py-1.5 text-xs font-semibold bg-emerald-500 text-zinc-950 hover:bg-emerald-400 rounded-md transition-colors shadow-sm">
                      Get Started
                    </button>
                  </SignUpButton>
                </SignedOut>

                <SignedIn>
                  <UserButton
                    appearance={{
                      elements: {
                        avatarBox: "w-8 h-8 rounded-full border border-zinc-700",
                      },
                    }}
                  />
                </SignedIn>
              </div>
            </div>
          </header>

          {/* Main Content Area */}
          <main className="flex-1 flex flex-col">
            {children}
          </main>
        </body>
      </html>
    </ClerkProvider>
  );
}
