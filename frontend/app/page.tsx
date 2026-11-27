"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth, Show, RedirectToSignIn } from "@clerk/nextjs";
import { CheckCircle2, Clock, Circle, Trophy, ArrowRight, Sparkles } from "lucide-react";
import { StudentCatalogSummary } from "@/types/problem";

interface ProblemRow {
  id: string;
  title: string;
  slug: string;
  difficulty: "Easy" | "Medium" | "Hard";
  category: string;
  acceptance: string;
}

const FALLBACK_PROBLEMS: ProblemRow[] = [
  {
    id: "9ab21dc3-87d5-4961-8fdc-158c3dfd2260",
    title: "Two Sum",
    slug: "two-sum",
    difficulty: "Easy",
    category: "Hash Table / Array",
    acceptance: "49.2%",
  },
  {
    id: "8c12a860-2641-4770-b196-419b45e9944a",
    title: "Valid Parentheses",
    slug: "valid-parentheses",
    difficulty: "Easy",
    category: "Stack / String",
    acceptance: "40.8%",
  },
  {
    id: "3df20336-3914-411a-ab93-4a180fec7aa4",
    title: "Reverse Linked List",
    slug: "reverse-linked-list",
    difficulty: "Easy",
    category: "Pointers / Linked List",
    acceptance: "74.1%",
  },
];

export default function HomePage() {
  const [problems, setProblems] = useState<ProblemRow[]>(FALLBACK_PROBLEMS);
  const [summary, setSummary] = useState<StudentCatalogSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { getToken } = useAuth();

  useEffect(() => {
    async function fetchData() {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

      // 1. Fetch dynamic question catalog from database
      try {
        const qRes = await fetch(`${apiUrl}/api/v1/questions`);
        if (qRes.ok) {
          const qData = await qRes.json();
          if (Array.isArray(qData) && qData.length > 0) {
            const mapped: ProblemRow[] = qData.map((q: any) => {
              const diffRaw = (q.difficulty || "Easy").toLowerCase();
              const diff: "Easy" | "Medium" | "Hard" =
                diffRaw === "medium" ? "Medium" : diffRaw === "hard" ? "Hard" : "Easy";

              let category = "Algorithms";
              const slug = q.slug || "";
              if (slug.includes("sum") || slug.includes("array")) category = "Hash Table / Array";
              else if (slug.includes("parenthes") || slug.includes("stack")) category = "Stack / String";
              else if (slug.includes("list") || slug.includes("tree")) category = "Pointers / Linked List";

              return {
                id: q.id,
                title: q.title,
                slug: q.slug,
                difficulty: diff,
                category: q.category || category,
                acceptance: q.acceptance || "50.0%",
              };
            });
            setProblems(mapped);
          }
        }
      } catch (err) {
        console.warn("Could not fetch dynamic question catalog, using fallback:", err);
      }

      // 2. Fetch student submission summary
      try {
        const token = await getToken();
        const headers: Record<string, string> = {};
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
        const res = await fetch(`${apiUrl}/api/v1/submissions/summary`, {
          headers,
        });
        if (res.ok) {
          const data: StudentCatalogSummary = await res.json();
          setSummary(data);
        }
      } catch (err) {
        console.error("Could not fetch student submission summary:", err);
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, [getToken]);

  const totalProblems = problems.length;
  const totalSolved = summary?.total_solved ?? 0;
  const progressPct = totalProblems > 0 ? Math.round((totalSolved / totalProblems) * 100) : 0;

  return (
    <Show when="signed-in" fallback={<RedirectToSignIn />}>
      <div className="max-w-5xl mx-auto px-4 py-10 w-full flex-1 flex flex-col select-text">
      {/* Header Section */}
      <div className="mb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white mb-1.5 text-balance flex items-center gap-2">
            <span>Assessment Problem Catalog</span>
            <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 border border-zinc-700">
              {problems.length} Questions
            </span>
          </h1>
          <p className="text-xs text-zinc-400 max-w-2xl leading-relaxed">
            The code editor remains locked until you explain your algorithmic approach, data structure, and complexity to the AI coach. Each problem includes a strict 2,000-token guardrail and isolated test evaluation.
          </p>
        </div>
      </div>

      {/* Dynamic Student Progress Banner */}
      <div className="border border-zinc-800 rounded-xl p-4 bg-[#161b22]/50 backdrop-blur-sm mb-6 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-3.5 w-full sm:w-auto">
          <div className="w-11 h-11 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">
            {totalSolved > 0 ? (
              <Trophy className="w-5 h-5 text-emerald-400" />
            ) : (
              <Sparkles className="w-5 h-5 text-zinc-400" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-white">Your Assessment Progress</h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                {progressPct}% Solved
              </span>
            </div>
            <p className="text-xs text-zinc-400 mt-0.5">
              <strong className="text-white font-medium">{totalSolved}</strong> of{" "}
              <strong className="text-white font-medium">{totalProblems}</strong> problems solved
              {summary && summary.total_attempted > totalSolved && (
                <span className="text-amber-400/90 ml-1.5 font-medium">
                  • {summary.total_attempted - totalSolved} in progress
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full sm:w-56 shrink-0 flex flex-col gap-1.5">
          <div className="flex justify-between text-[10px] font-mono text-zinc-500">
            <span>Completion</span>
            <span>{totalSolved}/{totalProblems}</span>
          </div>
          <div className="h-2 w-full bg-zinc-800/80 rounded-full overflow-hidden border border-zinc-700/40">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-700 ease-out"
              style={{ width: `${Math.max(4, progressPct)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Clean Problems Directory Table */}
      <div className="border border-zinc-800 rounded-lg overflow-hidden bg-zinc-950 shadow-sm">
        <div className="grid grid-cols-12 px-4 py-2.5 bg-zinc-900/60 border-b border-zinc-800 text-[11px] font-medium text-zinc-400">
          <span className="col-span-1 text-center">Status</span>
          <span className="col-span-6">Title</span>
          <span className="col-span-2">Category</span>
          <span className="col-span-2">Difficulty</span>
          <span className="col-span-1 text-right">Acceptance</span>
        </div>

        <div className="divide-y divide-zinc-800/80 text-xs">
          {problems.map((problem, idx) => {
            const progress = summary?.progress?.[problem.id];
            const isSolved = progress?.status === "SOLVED";
            const isAttempted = progress?.status === "ATTEMPTED";

            return (
              <Link
                key={problem.slug}
                href={`/problems/${problem.slug}`}
                className="grid grid-cols-12 px-4 py-3 items-center hover:bg-zinc-900/60 transition-colors group focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400"
              >
                {/* Status Column with dynamic badges */}
                <div className="col-span-1 flex items-center justify-center">
                  {isSolved ? (
                    <div title="Solved" className="text-emerald-400 animate-fadeIn">
                      <CheckCircle2 className="w-4 h-4 fill-emerald-500/20" />
                    </div>
                  ) : isAttempted ? (
                    <div title={`Attempted (${progress.attempts} tries)`} className="text-amber-400 animate-fadeIn">
                      <Clock className="w-4 h-4" />
                    </div>
                  ) : (
                    <div title="Not started" className="text-zinc-600 group-hover:text-zinc-500 transition-colors">
                      <Circle className="w-3.5 h-3.5 stroke-[1.5]" />
                    </div>
                  )}
                </div>

                {/* Title Column */}
                <div className="col-span-6 font-medium text-zinc-200 group-hover:text-white flex items-center gap-2 min-w-0">
                  <span className="text-zinc-500 font-mono text-[11px] tabular-nums shrink-0">
                    {idx + 1}.
                  </span>
                  <span className="truncate">{problem.title}</span>

                  {/* Status Pills */}
                  {isSolved && (
                    <span className="text-[10px] font-mono font-medium px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
                      Solved
                    </span>
                  )}
                  {isAttempted && (
                    <span className="text-[10px] font-mono font-medium px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0">
                      Attempted ({progress.attempts})
                    </span>
                  )}
                </div>

                {/* Category Column */}
                <div className="col-span-2 text-zinc-400 text-[11px] truncate">
                  {problem.category}
                </div>

                {/* Difficulty Column */}
                <div className="col-span-2">
                  <span className={`inline-block text-[11px] px-2 py-0.5 rounded font-mono font-medium border ${
                    problem.difficulty === "Easy"
                      ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                      : problem.difficulty === "Medium"
                      ? "text-amber-400 bg-amber-500/10 border-amber-500/20"
                      : "text-rose-400 bg-rose-500/10 border-rose-500/20"
                  }`}>
                    {problem.difficulty}
                  </span>
                </div>

                {/* Acceptance Rate */}
                <div className="col-span-1 text-right text-zinc-500 font-mono text-[11px] tabular-nums group-hover:text-zinc-400 flex items-center justify-end gap-1">
                  <span>{problem.acceptance}</span>
                  <ArrowRight className="w-3 h-3 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-zinc-400 hidden sm:inline-block" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  </Show>
  );
}
